#!/usr/bin/env python
"""
Extend the in-repo CMIP7 lookup tables (../cmip7-lookup/<comp>_lookup.csv) so that
they list not only the variables the model already produces but ALSO every
variable of the CMCC request that has NO raw name yet - appended at the end as
rows with an EMPTY `model` column, to be filled in by hand.

The tables keep the ORIGINAL 4-column format of
cmip_reformatter/cmip-tables/cmip6plus/variables/<comp>_lookup.csv:

    variable,reprocess,model,long_name
    ...                                  <- the original block, untouched, in order
    snw,False,,Surface Snow Amount       <- appended: fill `model` (e.g. H2OSNO)

Fill `model` -> the row becomes a normal reformatter mapping and
map_to_raw_names.py counts the variable as `mapped` on the next run. That is the
whole loop: build -> map -> extend -> fill by hand -> map again.

The merge is IDEMPOTENT and never destroys hand work:
  * rows already in the table keep their `reprocess`, `model`, `long_name`;
  * the original block stays in its original order (taken from --reference-dir),
    previously appended rows keep theirs, only missing variables are appended;
  * re-running with nothing new to add rewrites the files identically.

Appended variables are the "unmapped" ones of out/raw/unmapped.csv, i.e. both
  * true_gap  - no raw name anywhere         -> fill `model`
  * derivable - a slice/aggregate of a field already stored (thetao200 from
                thetao) -> normally NO new model output needed; skip them with
                --true-gap-only.
Their realm / frequency / Division / GB-per-year context is deliberately NOT in
these tables (they stay 4-column reformatter tables): it is in
out/raw/unmapped.csv and out/truegap_{high,medium}.{csv,txt}.

Realms share a table the same way cmip_reformatter groups them
(aerosol/atmosChem -> atm, landIce -> lnd, ocnBgchem -> ocnbgc).

No DR API needed - pure post-processing of out/cmcc_variables_mapped.csv.

Usage:
    python build_cmip7_lookup.py                  # extend ../cmip7-lookup in place
    python build_cmip7_lookup.py --dry-run        # report only, write nothing
    python build_cmip7_lookup.py --true-gap-only  # skip the derivable variables
"""
import argparse
import csv
import os
from collections import defaultdict

from map_to_raw_names import REALM_TO_LOOKUP

FIELDS = ["variable", "reprocess", "model", "long_name"]   # the original format
FAMS = sorted(set(REALM_TO_LOOKUP.values()))


def read_table(path):
    """(order, rows) - row order preserved, rows keyed by variable name."""
    if not os.path.exists(path):
        return [], {}
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("variable") or "").strip()]
    order = [r["variable"].strip() for r in rows]
    return order, {r["variable"].strip(): r for r in rows}


def load_request(mapped_path):
    """req[variable] = dict(category, realms, long_name) over the whole selection."""
    with open(mapped_path, newline="") as f:
        rows = list(csv.DictReader(f))
    req = {}
    for r in rows:
        var = (r.get("cmip6_name") or r.get("out_name") or "").strip()
        if not var:
            continue
        e = req.setdefault(var, {"category": set(), "realms": set(), "long_name": ""})
        e["category"].add(r.get("map_category", ""))
        if r.get("realm"):
            e["realms"].add(r["realm"])
        e["long_name"] = e["long_name"] or r.get("long_name", "")
    return req, len(rows)


def category_of(entry):
    """One category per variable name (true_gap wins - it is the actionable one)."""
    for c in ("true_gap", "derivable", "mapped"):
        if c in entry["category"]:
            return c
    return ""


def families_of(entry):
    return {REALM_TO_LOOKUP[r] for r in entry["realms"] if r in REALM_TO_LOOKUP}


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--lookup-dir", default=os.path.join(here, "..", "cmip7-lookup"),
                    help="tables to extend IN PLACE (default: ../cmip7-lookup)")
    ap.add_argument("--reference-dir",
                    default=os.path.join(here, "..", "cmip_reformatter", "cmip-tables",
                                         "cmip6plus", "variables"),
                    help="the ORIGINAL tables; used to tell the original block from "
                         "our appended rows and to keep its row order. Optional - "
                         "skipped if the clone is not there.")
    ap.add_argument("--mapped", default=os.path.join(here, "out", "cmcc_variables_mapped.csv"))
    ap.add_argument("--true-gap-only", action="store_true",
                    help="append only true_gap variables (skip the derivable ones)")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    req, n_entries = load_request(args.mapped)
    n_cat = defaultdict(int)
    for e in req.values():
        n_cat[category_of(e)] += 1
    print(f"[in]     {n_entries} selected entries -> {len(req)} distinct CMOR names "
          f"({n_cat['mapped']} mapped, {n_cat['derivable']} derivable, "
          f"{n_cat['true_gap']} true_gap)")

    want = {"true_gap"} if args.true_gap_only else {"true_gap", "derivable"}
    to_add = defaultdict(dict)                       # fam -> {var: entry}
    unplaced = []
    for var, e in req.items():
        if category_of(e) not in want:
            continue
        fams = families_of(e)
        if not fams:
            unplaced.append(var)
            continue
        for fam in fams:
            to_add[fam][var] = e

    ref_ok = os.path.isdir(args.reference_dir)
    if not ref_ok:
        print(f"[ref]    {args.reference_dir} not found -> keeping the current row order")

    print(f"\n{'table':22s} {'original':>8s} {'appended':>8s} {'new':>4s} {'to_fill':>7s}")
    tot = [0, 0, 0, 0]
    tables = {}
    for fam in FAMS:
        path = os.path.join(args.lookup_dir, f"{fam}_lookup.csv")
        cur_order, cur = read_table(path)
        ref_order, ref = read_table(os.path.join(args.reference_dir, f"{fam}_lookup.csv"))

        # 1) the original block, in its original order   2) rows appended earlier
        base = ref_order if ref_ok else cur_order
        base_set = set(base)
        appended = [v for v in cur_order if v not in base_set]
        # 3) variables of the request still missing from this table
        known = base_set | set(appended)
        new = sorted(v for v in to_add[fam] if v not in known)

        rows = []
        for var in base + appended + new:
            # existing cells are copied VERBATIM (no re-formatting, no stripping)
            src = cur.get(var) or ref.get(var) or {}
            e = req.get(var)
            reprocess = src.get("reprocess") or ""
            long_name = src.get("long_name") or ""
            rows.append({
                "variable": var,
                # a valid Python literal: cmip_reformatter eval()s this column
                "reprocess": reprocess if reprocess.strip() else "False",
                "model": src.get("model") or "",
                "long_name": long_name if long_name.strip()
                             else (e["long_name"] if e else ""),
            })

        n_todo = sum(1 for r in rows if not r["model"].strip())
        if not args.dry_run:
            with open(path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
        tables[fam] = {r["variable"] for r in rows}
        counts = (len(base), len(appended), len(new), n_todo)
        print(f"{fam + '_lookup.csv':22s} {counts[0]:8d} {counts[1]:8d} "
              f"{counts[2]:4d} {counts[3]:7d}")
        tot = [t + c for t, c in zip(tot, counts)]

    print(f"{'TOTAL':22s} {tot[0]:8d} {tot[1]:8d} {tot[2]:4d} {tot[3]:7d}")
    print("\noriginal = rows of the reference cmip6plus table (order preserved)\n"
          "appended = gap rows added by an earlier run\n"
          "new      = gap rows appended by THIS run (model empty -> fill by hand)\n"
          "to_fill  = rows still waiting for a raw `model` name")
    if unplaced:
        print(f"\n[warn] {len(unplaced)} gap vars with no realm->table family, skipped: "
              f"{', '.join(sorted(unplaced)[:8])}")

    check(req, tables, want)
    if args.dry_run:
        print(f"\n[dry-run] nothing written to {args.lookup_dir}")
    else:
        print(f"\n[write] {args.lookup_dir}/*_lookup.csv  <- fill the empty `model` "
              "cells, then re-run map_to_raw_names.py")


def check(req, tables, want):
    """Verify every requested variable now has a row in the lookup tables.

    Expected present = the mapped ones (they were the seed) + every category we
    append. A `derivable` name is only expected when it was not skipped with
    --true-gap-only."""
    everywhere = set().union(*tables.values()) if tables else set()
    expected = want | {"mapped"}
    present, missing, misplaced = defaultdict(int), defaultdict(list), []
    for var, e in req.items():
        cat = category_of(e)
        if any(var in tables.get(fam, ()) for fam in families_of(e)):
            present[cat] += 1
        elif var in everywhere:
            # present, but only in another component's table (the mapper allows
            # this cross-realm fallback and flags it with * in mapping_detail)
            present[cat] += 1
            misplaced.append(var)
        elif cat in expected:
            missing[cat].append(var)

    n_exp = sum(1 for e in req.values() if category_of(e) in expected)
    n_missing = sum(len(v) for v in missing.values())
    verdict = "complete" if n_missing == 0 else f"{n_missing} MISSING"
    print(f"\n[check]  {n_exp - n_missing}/{n_exp} expected CMOR names present "
          f"-> {verdict}   ({len(everywhere)} rows across {len(tables)} tables)")
    for cat in ("mapped", "derivable", "true_gap"):
        n_cat = sum(1 for e in req.values() if category_of(e) == cat)
        if not n_cat:
            continue
        note = "" if cat in expected else "  (skipped on purpose: --true-gap-only)"
        print(f"           {cat:10s} {present[cat]:4d}/{n_cat:<4d} present{note}")
        if missing.get(cat):
            print(f"           -> missing: {', '.join(sorted(missing[cat])[:10])}")
    if misplaced:
        print(f"           {len(misplaced)} sit in another component's table "
              f"(cross-realm, fine): {', '.join(sorted(misplaced)[:6])}")


if __name__ == "__main__":
    main()
