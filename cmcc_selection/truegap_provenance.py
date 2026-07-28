#!/usr/bin/env python
"""
Trace the TRUE-GAP variables back to their origin: which High/Medium CMCC
opportunity requested them, through which variable group, and which Division
owns that opportunity.

Joins:
  * out/cmcc_variables_mapped.csv  (map_category, groups, opportunities per var)
  * CMCC_CMIP7-DR-opportunities-Final - DR-Selection.csv  (Division per opportunity)

Group names are reconciled with the same cleaning + ALIASES used by
build_cmcc_cmip7_table.py, so the two sides line up (e.g. omip_geometry_physics
-> omip_scalars_high_priority). No DR API needed - runs in any env.

Usage:
    python truegap_provenance.py \
        --mapped out/cmcc_variables_mapped.csv \
        --csv "../CMCC_CMIP7-DR-opportunities-Final - DR-Selection.csv"
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
                    "CMCC_CMIP7-DR-opportunities-Final - DR-Selection.csv"))
    ap.add_argument("--outdir", default=os.path.join(here, "out"))
    args = ap.parse_args()

    cmcc = parse_cmcc(args.csv)

    with open(args.mapped, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("map_category") == "true_gap"]
    print(f"[in] {len(rows)} true_gap variables; {len(cmcc)} High/Medium opportunities")

    # (division, opportunity, priority, group) -> list of true_gap var names
    rec = defaultdict(list)
    unattributed = []
    for r in rows:
        var = r.get("cmip6_name") or r.get("out_name", "")
        v_opps = [o for o in r.get("opportunities", "").split(";") if o]
        v_groups = {_norm(g) for g in r.get("groups", "").split(";") if g}
        placed = False
        for opp in v_opps:
            info = cmcc.get(opp)
            if not info:
                continue
            for gn in (v_groups & info["groups_norm"]):
                rec[(info["division"], opp, info["priority"],
                     info["norm2name"][gn])].append(var)
                placed = True
        if not placed:
            unattributed.append(var)

    # detail CSV: one row per (division, opportunity, group)
    out = os.path.join(args.outdir, "truegap_provenance.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["division", "opportunity", "cmcc_priority", "group",
                    "n_true_gap", "true_gap_variables"])
        for (div, opp, prio, grp), vs in sorted(rec.items()):
            uv = sorted(set(vs))
            w.writerow([div, opp, prio, grp, len(uv), ", ".join(uv)])

    # readable summary grouped by Division -> Opportunity -> group
    by_div = defaultdict(lambda: defaultdict(list))
    for (div, opp, prio, grp), vs in rec.items():
        by_div[div][(opp, prio)].append((grp, len(set(vs))))
    print()
    for div in sorted(by_div):
        n = sum(c for opp in by_div[div].values() for _, c in opp)
        print(f"### {div}   ({n} true_gap variable-slots)")
        for (opp, prio) in sorted(by_div[div]):
            grps = sorted(by_div[div][(opp, prio)])
            print(f"  [{prio:6}] {opp}")
            for grp, c in grps:
                print(f"        {grp:52s} {c:3d}")
    if unattributed:
        print(f"\n[warn] {len(unattributed)} true_gap vars not attributed to a "
              f"High/Medium group (e.g. {', '.join(sorted(set(unattributed))[:5])})")
    print(f"\n[write] {out}")


if __name__ == "__main__":
    main()
