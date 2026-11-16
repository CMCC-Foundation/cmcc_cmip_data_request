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

Appended variables are the "unmapped" ones of out/raw/unmapped.csv.
Their realm / frequency / Division / GB-per-year context is deliberately NOT in
these tables (they stay 4-column reformatter tables): it is in
out/raw/unmapped.csv and out/truegap_{high,medium}.{csv,txt}.

Realms share a table the same way cmip_reformatter groups them
(aerosol/atmosChem -> atm, landIce -> lnd, ocnBgchem -> ocnbgc).

No DR API needed - pure post-processing of out/cmcc_variables_mapped.csv.

Usage:
    python build_cmip7_lookup.py                  # extend ../cmip7-lookup in place
"""
import argparse
import csv
import os
from collections import defaultdict

# DR modeling_realm -> reformatter lookup family (file is <fam>_lookup.csv)
REALM_TO_LOOKUP = {
    "atmos": "atm", "aerosol": "atm", "atmosChem": "atm",
    "land": "lnd", "landIce": "lnd",
    "ocean": "ocn", "ocnBgchem": "ocnbgc",
    "seaIce": "ice",
}

FIELDS = ["variable", "reprocess", "model", "long_name", "cmip6_name"]   # updated: format
FAMS = sorted(set(REALM_TO_LOOKUP.values()))


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
    ap.add_argument("--lookup-dir", default=os.path.join(here, "cmip7-lookup"),
                    help="tables to extend IN PLACE (default: out/cmip7-lookup)")
    ap.add_argument("--reference-dir",
                    default=os.path.join(here, "cmip6plus-lookup"),
                    help="the ORIGINAL tables; used to tell the original block from "
                         "our appended rows and to keep its row order. Optional - "
                         "skipped if the clone is not there.")
    ap.add_argument("--mapped", default=os.path.join(here, "dr-cmip7-full", "cmcc_data_request.csv"),
                    help="path to mapped variables CSV file")
    ap.add_argument("-f", "--force", action="store_true",
                    help="force overwrite of existing lookup tables")
    args = ap.parse_args()

    os.makedirs(args.lookup_dir, exist_ok=True)

    if not os.path.exists(args.mapped):
        print(f"File not found: {args.mapped}")
        return

    req, n_entries = load_request(args.mapped)
    
    ref_ok = os.path.isdir(args.reference_dir)
    if not ref_ok:
        print(f"[ref]    {args.reference_dir} not found. Stop.")
        return

    print(f"\n{'table':22s} {'mapped':>8s} {'new':>8s}")
    tot = [0, 0]
    tables = {}
    for fam in FAMS:
        # load cmip reference lookup table for realm
        ref_order, ref = read_table(os.path.join(args.reference_dir, f"{fam}_lookup.csv"))

        # get local dict of variables for this realm
        fam_req = {d:req[d] for d in req.keys() if req[d]['realm']==fam}

        # loop on fam_req and fill output
        map_dict = {}
        new_dict = {}
        for var in fam_req.keys():
            var_cmip6 = fam_req[var]['cmip6_name']
            if var_cmip6 in ref.keys():
                map_dict[var] = {
                           'variable': var,
                           'reprocess': ref[var_cmip6]['reprocess'],
                           'model': ref[var_cmip6]['model'],
                           'long_name': fam_req[var]['long_name'],
                           'cmip6_name': var_cmip6,
                }
            else:
                new_dict[var] = {
                           'variable': var,
                           'reprocess': "False",
                           'model': "DISCARD",
                           'long_name': fam_req[var]['long_name'],
                           'cmip6_name': var_cmip6,
                }

        # sort by key
        map_dict = {k: v for k, v in sorted(map_dict.items(), key=lambda item: item[0])}
        new_dict = {k: v for k, v in sorted(new_dict.items(), key=lambda item: item[0])}

        # collate dicts
        fam_out = dict(map_dict, **new_dict)

        # write dicts
        path = os.path.join(args.lookup_dir, f"{fam}_lookup.csv")
        written = write_dicts(path, fam_out, force=args.force)
        if not written:
            return
                
        tables[fam] = {r["variable"] for r in fam_out.values()}
        counts = (len(map_dict), len(new_dict))
        print(f"{fam + '_lookup.csv':22s} {counts[0]:8d} {counts[1]:8d} ")
        tot = [t + c for t, c in zip(tot, counts)]

    print(f"{'TOTAL':22s} {tot[0]:8d} {tot[1]:8d}")
    print("\nmapped = variables already in reference cmip6plus table\n"
          "new  = variables still waiting for a raw `model` name")

    print(f"\n[write] {args.lookup_dir}/*_lookup.csv  <- fill the empty `model` "
          "cells, then re-run map_to_raw_names.py")


def write_dicts(path, fam_out, force=False):
    """Write collated dictionary to CSV file at path. Return False if exists and force is False."""
    if os.path.exists(path) and not force:
        print(f"File {path} already exists. Use --force / -f to overwrite. Stopping process.")
        return False

    rows = [fam_out[d] for d in fam_out.keys()]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return True


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
        var = '.'.join((r.get("compound_name" or "")).split('.')[:3]).strip()
        if not var:
            continue
        e = req.setdefault(var, {"cmip6_name": None, "realm": None, "long_name": "", 'raw': ""})
        e["cmip6_name"] = r.get("cmip6_name", "")
        if r.get("realm"):
            e["realm"] = families_of([r["realm"]])
        else:
            raise SystemExit (f"ERROR: Cannot find realm for variable: {var}")
        e["long_name"] = e["long_name"] or r.get("long_name", "")
    return req, len(rows)


def families_of(entry):
    return [REALM_TO_LOOKUP[r] for r in entry if r in REALM_TO_LOOKUP][0]


if __name__ == "__main__":
    main()
