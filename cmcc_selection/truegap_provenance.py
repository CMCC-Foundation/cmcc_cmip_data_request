#!/usr/bin/env python
"""
Trace the TRUE-GAP variables back to their origin: which High/Medium CMCC
opportunity requested them, through which variable group, and which Division
owns that opportunity.

Joins:
  * out/cmcc_variables_mapped.csv  (map_category, groups, opportunities per var)
  * CMCC_CMIP7-DR-opportunities-Final_DR-Selection.csv  (Division per opportunity)

Group names are reconciled with the same cleaning + ALIASES used by
build_cmcc_cmip7_table.py, so the two sides line up (e.g. omip_geometry_physics
-> omip_scalars_high_priority). No DR API needed - runs in any env.

Usage:
    python truegap_provenance.py \
        --mapped out/cmcc_variables_mapped.csv \
        --csv "../CMCC_CMIP7-DR-opportunities-Final_DR-Selection.csv"
"""
import argparse
import csv
import os
from collections import defaultdict

import build_cmcc_cmip7_table as build   # reuse ALIASES, clean_group_token, _norm

_norm = build._norm
ALIASES_NORM = {_norm(k): v for k, v in build.ALIASES.items()}


def parse_cmcc(path):
    """opportunity -> {division, priority, groups_norm:set, norm2name:dict}."""
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
        groups_norm, norm2name = set(), {}
        for tok in vg.replace("\n", ",").split(","):
            gid, _ = build.clean_group_token(tok)
            if not gid:
                continue
            # resolve CMCC shorthand to the actual DR group name(s)
            dr_names = ALIASES_NORM.get(_norm(gid), [gid])
            for dn in dr_names:
                groups_norm.add(_norm(dn))
                norm2name[_norm(dn)] = dn
        opps[opp] = {"division": division or "(unspecified)", "priority": prio,
                     "groups_norm": groups_norm, "norm2name": norm2name}
    return opps


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--mapped", default=os.path.join(here, "out", "cmcc_variables_mapped.csv"))
    ap.add_argument("--csv", default=os.path.join(here, "..",
                    "CMCC_CMIP7-DR-opportunities-Final_DR-Selection.csv"))
    ap.add_argument("--outdir", default=os.path.join(here, "out"))
    args = ap.parse_args()

    cmcc = parse_cmcc(args.csv)

    with open(args.mapped, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("map_category") == "true_gap"]
    print(f"[in] {len(rows)} true_gap variables; {len(cmcc)} High/Medium opportunities")

    # (division, opportunity, priority, group) -> {varname: {long_name, realm, freqs}}
    rec = defaultdict(dict)
    unattributed = []
    for r in rows:
        var = r.get("cmip6_name") or r.get("out_name", "")
        ln, realm, freq = r.get("long_name", ""), r.get("realm", ""), r.get("frequency", "")
        v_opps = [o for o in r.get("opportunities", "").split(";") if o]
        v_groups = {_norm(g) for g in r.get("groups", "").split(";") if g}
        placed = False
        for opp in v_opps:
            info = cmcc.get(opp)
            if not info:
                continue
            for gn in (v_groups & info["groups_norm"]):
                d = rec[(info["division"], opp, info["priority"], info["norm2name"][gn])]
                e = d.setdefault(var, {"long_name": ln, "realm": realm, "freqs": set()})
                e["freqs"].add(freq)
                placed = True
        if not placed:
            unattributed.append(var)

    # detail CSV: one row per (division, opportunity, group), with the var names
    out = os.path.join(args.outdir, "truegap_provenance.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["division", "opportunity", "cmcc_priority", "group",
                    "n_true_gap", "true_gap_variables"])
        for (div, opp, prio, grp), d in sorted(rec.items()):
            w.writerow([div, opp, prio, grp, len(d), ", ".join(sorted(d))])

    # opportunity-level rollup CSV: one row per (division, opportunity)
    out_opp = os.path.join(args.outdir, "truegap_by_opportunity.csv")
    by_opp = defaultdict(lambda: {"groups": set(), "vars": set()})
    for (div, opp, prio, grp), d in rec.items():
        b = by_opp[(div, opp, prio)]
        b["groups"].add(grp)
        b["vars"].update(d)
    with open(out_opp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["division", "opportunity", "cmcc_priority", "n_true_gap",
                    "groups_with_true_gap", "true_gap_variables"])
        for (div, opp, prio), b in sorted(by_opp.items()):
            w.writerow([div, opp, prio, len(b["vars"]),
                        ", ".join(sorted(b["groups"])), ", ".join(sorted(b["vars"]))])

    # priority-split, nicely formatted files (one HIGH, one MEDIUM), txt + csv
    written = []
    for prio in ("high", "medium"):
        written += write_priority(prio, rec, args.outdir)

    # short console summary
    by_div = defaultdict(set)
    for (div, opp, prio, grp), d in rec.items():
        by_div[div].update(d)
    print()
    for div in sorted(by_div):
        print(f"  {div:16s} {len(by_div[div]):4d} distinct true_gap variables")
    if unattributed:
        print(f"\n[warn] {len(unattributed)} true_gap vars not attributed "
              f"(e.g. {', '.join(sorted(set(unattributed))[:5])})")
    for p in [out, out_opp] + written:
        print(f"[write] {p}")


def write_priority(prio, rec, outdir):
    """Write truegap_<prio>.txt (formatted, Division-separated) and .csv."""
    sub = {k: v for k, v in rec.items() if k[2] == prio}
    if not sub:
        return []
    # division -> opportunity -> list of (group, {var:info})
    by_div = defaultdict(lambda: defaultdict(list))
    for (div, opp, _p, grp), d in sub.items():
        by_div[div][opp].append((grp, d))

    n_vars = len({v for _k, d in sub.items() for v in d})
    n_opps = len({(k[0], k[1]) for k in sub})
    label = prio.upper()

    txt = os.path.join(outdir, f"truegap_{prio}.txt")
    W = 78
    with open(txt, "w") as f:
        f.write("=" * W + "\n")
        f.write(f" CMIP7 output — variables with NO corresponding model field (TRUE GAP)\n")
        f.write(f" Priority: {label}\n")
        f.write(f" {n_vars} distinct variables, {n_opps} opportunities, {len(by_div)} divisions\n")
        f.write("=" * W + "\n\n")
        for div in sorted(by_div):
            f.write("\n" + "#" * W + "\n")
            f.write(f"#  DIVISION: {div}\n")
            f.write("#" * W + "\n")
            for opp in sorted(by_div[div]):
                f.write(f"\n  Opportunity: {opp}\n")
                f.write("  " + "-" * (W - 4) + "\n")
                for grp, d in sorted(by_div[div][opp]):
                    f.write(f"\n    group: {grp}\n")
                    for var in sorted(d):
                        ln = d[var]["long_name"]
                        f.write(f"        {var:20s} {ln}\n")
            f.write("\n")

    out_csv = os.path.join(outdir, f"truegap_{prio}.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["division", "opportunity", "group", "variable",
                    "long_name", "realm", "frequencies"])
        for (div, opp, _p, grp), d in sorted(sub.items()):
            for var in sorted(d):
                info = d[var]
                w.writerow([div, opp, grp, var, info["long_name"],
                            info["realm"], " ".join(sorted(f for f in info["freqs"] if f))])
    return [txt, out_csv]


if __name__ == "__main__":
    main()
