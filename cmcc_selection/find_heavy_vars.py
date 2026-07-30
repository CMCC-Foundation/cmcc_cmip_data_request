#!/usr/bin/env python
"""
Find the heavy variables (default: 3-hourly OCEAN) and trace each to its
variable group, opportunity, Division, priority, whether it belongs to the
Baseline (IPCC) opportunity, and its GB/year.

3-D vs 2-D is read from the CMIP7 branded/compound name: the vertical token of
the branding label (e.g. ocean.ficeberg.tavg-**ol**-hxy-sea.3hr.glb -> "ol" =
ocean model levels = 3-D; "u"/single-level -> 2-D).

Joins cmcc_variables_mapped.csv with the CMCC opportunities file (Division), the
same way as truegap_provenance.py. No DR API needed.

Usage:
    python find_heavy_vars.py --realm ocean --freq 3hr
"""
import argparse
import csv
import os
from collections import defaultdict

import build_cmcc_cmip7_table as build

_norm = build._norm
ALIASES_NORM = {_norm(k): v for k, v in build.ALIASES.items()}
LEVEL_TOKENS = {"ol", "olevel", "al", "alevel", "sl", "rho"}   # full-depth/level = 3-D
BASELINE_KEY = "baseline climate variables"                    # the IPCC baseline opportunity


def parse_cmcc(path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    hdr = next((i for i, r in enumerate(rows) if any("CMCC priority" in c for c in r)), 1)
    opps = {}
    for r in rows[hdr + 1:]:
        if len(r) < 5:
            continue
        division, opp, prio, vg = r[1].strip(), r[2].strip(), r[3].strip().lower(), r[4]
        if not opp or prio not in build.KEEP_PRIORITIES:
            continue
        gset, n2n = set(), {}
        for tok in vg.replace("\n", ",").split(","):
            gid, _ = build.clean_group_token(tok)
            if not gid:
                continue
            for dn in ALIASES_NORM.get(_norm(gid), [gid]):
                gset.add(_norm(dn))
                n2n[_norm(dn)] = dn
        opps[opp] = {"division": division or "(unspecified)", "priority": prio,
                     "groups_norm": gset, "norm2name": n2n}
    return opps


def vertical_token(compound):
    """Return the branding vertical token (2nd field of the 3rd dotted part)."""
    parts = compound.split(".")
    if len(parts) < 3:
        return ""
    bl = parts[2].split("-")
    return bl[1] if len(bl) > 1 else ""


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--mapped", default=os.path.join(here, "out", "cmcc_variables_mapped.csv"))
    ap.add_argument("--csv", default=os.path.join(here, "..",
                    "CMCC_CMIP7-DR-opportunities-Final - DR-Selection.csv"))
    ap.add_argument("--outdir", default=os.path.join(here, "out"))
    ap.add_argument("--realm", default="ocean", help="realm to filter (default ocean)")
    ap.add_argument("--freq", default="3hr", help="frequency to filter (default 3hr)")
    ap.add_argument("--only-3d", action="store_true", help="keep only 3-D variables")
    args = ap.parse_args()

    cmcc = parse_cmcc(args.csv)
    with open(args.mapped, newline="") as f:
        rows = list(csv.DictReader(f))

    # GB/year: prefer the dedicated volume file (survives map reruns that drop the
    # GB_per_year column from cmcc_variables_mapped.csv)
    vol = {}
    vpath = os.path.join(args.outdir, "volume_by_variable.csv")
    if os.path.exists(vpath):
        with open(vpath, newline="") as f:
            for v in csv.DictReader(f):
                vol[v.get("compound_name", "")] = v.get("GB_per_year", "")

    hits = [r for r in rows
            if r.get("realm") == args.realm and r.get("frequency") == args.freq]

    out_rows = []
    for r in hits:
        is3d = vertical_token(r.get("compound_name", "")) in LEVEL_TOKENS
        if args.only_3d and not is3d:
            continue
        var = r.get("cmip6_name") or r.get("out_name", "")
        gb = r.get("GB_per_year", "") or vol.get(r.get("compound_name", ""), "")
        v_opps = [o for o in r.get("opportunities", "").split(";") if o]
        v_groups = {_norm(g) for g in r.get("groups", "").split(";") if g}
        placed = False
        for opp in v_opps:
            info = cmcc.get(opp)
            if not info:
                continue
            for gn in (v_groups & info["groups_norm"]):
                out_rows.append({
                    "variable": var, "dim": "3D" if is3d else "2D",
                    "cell": r.get("cell", ""), "GB_per_year": gb,
                    "map_category": r.get("map_category", ""),
                    "group": info["norm2name"][gn], "opportunity": opp,
                    "division": info["division"], "cmcc_priority": info["priority"],
                    "in_baseline": "YES" if BASELINE_KEY in opp.lower() else "no",
                    "long_name": r.get("long_name", ""),
                    "compound_name": r.get("compound_name", ""),
                })
                placed = True
        if not placed:
            out_rows.append({"variable": var, "dim": "3D" if is3d else "2D",
                             "cell": r.get("cell", ""), "GB_per_year": gb,
                             "map_category": r.get("map_category", ""),
                             "group": "?", "opportunity": "?", "division": "?",
                             "cmcc_priority": "?", "in_baseline": "?",
                             "long_name": r.get("long_name", ""),
                             "compound_name": r.get("compound_name", "")})

    def gbf(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    out_rows.sort(key=lambda x: -gbf(x["GB_per_year"]))
    fields = ["variable", "dim", "cell", "GB_per_year", "map_category", "in_baseline",
              "group", "opportunity", "division", "cmcc_priority", "long_name",
              "compound_name"]
    out = os.path.join(args.outdir, f"heavy_{args.realm}_{args.freq}.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    # console summary
    n3 = len({r["variable"] for r in out_rows if r["dim"] == "3D"})
    n2 = len({r["variable"] for r in out_rows if r["dim"] == "2D"})
    in_base = sorted({r["variable"] for r in out_rows if r["in_baseline"] == "YES"})
    print(f"{args.freq} {args.realm}: {n3} distinct 3-D and {n2} distinct 2-D variables\n")
    print(f"{'variable':16s} {'dim':3s} {'GB/yr':>7s} {'category':9s} {'baseline':8s} "
          f"{'division':14s} {'group':28s} opportunity")
    seen = set()
    for r in out_rows:
        k = (r["variable"], r["group"], r["opportunity"])
        if k in seen:
            continue
        seen.add(k)
        print(f"{r['variable']:16s} {r['dim']:3s} {gbf(r['GB_per_year']):7.1f} "
              f"{r['map_category']:9s} {r['in_baseline']:8s} {r['division']:14s} "
              f"{r['group']:28s} {r['opportunity']}")
    print(f"\n>>> 3-D {args.freq} {args.realm} variables in the BASELINE (IPCC) opportunity: "
          + (", ".join(in_base) if in_base else "NONE"))
    print(f"[write] {out}")


if __name__ == "__main__":
    main()
