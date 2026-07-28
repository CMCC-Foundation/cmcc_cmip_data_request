#!/usr/bin/env python
"""
Locate a variable in the Data Request, to reconcile our expansion with the
Airtable opportunity view:
  * which variable GROUPS contain it,
  * which OPPORTUNITIES request it (per the DR itself),
  * and, for a named opportunity, its total variable count + whether the
    variable is in it.

Usage:
    python check_var.py --version v1.2.2.4 --var bigthetao \
        --opportunity "Baseline Climate Variables for Earth System Modelling"
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1.2.2.4")
    ap.add_argument("--var", required=True, help="out_name or CMIP6 short name, e.g. bigthetao")
    ap.add_argument("--opportunity", default=None)
    a = ap.parse_args()

    from data_request_api.content import dreq_content as dc
    from data_request_api.content import dump_transformation as dt
    from data_request_api.query import data_request as dr
    from data_request_api.query import dreq_query as dq

    DR = dr.DataRequest.from_separated_inputs(**dt.get_transformed_content(version=a.version))
    dc.retrieve(a.version)
    meta = dq.get_variables_metadata(dc.load(a.version), a.version, verbose=False)
    meta.pop("Header", None)
    by_uid = {i["uid"]: i for i in meta.values()}

    def names(v):
        i = by_uid.get(getattr(v, "uid", None), {})
        c6 = (i.get("cmip6_compound_name", "") or "").split(".")[-1]
        return i.get("out_name", ""), c6, i.get("frequency", "")

    q = a.var.lower()
    print(f"DR content version: {a.version}")

    print(f"\n== variable GROUPS containing '{a.var}' ==")
    matched_uids, matched_objs = set(), []
    for g in DR.get_variable_groups():
        gname = str(getattr(g, "name", g))
        for v in g.get_variables():
            o, c6, fr = names(v)
            if q in (o.lower(), c6.lower()):
                print(f"  {gname:44s} out_name={o:14s} cmip6={c6:16s} freq={fr}")
                matched_uids.add(getattr(v, "uid", None))
                matched_objs.append(v)
    if not matched_objs:
        print("  (NOT found in any variable group at this version)")

    print(f"\n== OPPORTUNITIES requesting '{a.var}' (per the DR) ==")
    opps = set()
    for v in matched_objs:
        try:
            for op in DR.find_opportunities_per_variable(v):
                opps.add(str(getattr(op, "title", None) or getattr(op, "name", None) or op))
        except Exception as e:  # noqa: BLE001
            print(f"  (find_opportunities_per_variable failed: {e})")
            break
    for o in sorted(opps):
        print(f"  - {o}")
    if not opps:
        print("  (none)")

    if a.opportunity:
        print(f"\n== opportunity '{a.opportunity}' ==")
        try:
            ov = DR.find_variables_per_opportunity(a.opportunity)
            uids = {getattr(v, "uid", None) for v in ov}
            print(f"  total variables in this opportunity: {len(ov)}")
            print(f"  contains '{a.var}': {bool(matched_uids & uids)}")
        except Exception as e:  # noqa: BLE001
            print(f"  (lookup failed - check the exact opportunity title: {e})")


if __name__ == "__main__":
    main()
