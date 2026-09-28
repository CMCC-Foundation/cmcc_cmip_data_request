#!/usr/bin/env python
"""
Turn the per-realm PRODUCTION tables into CESM history namelists:
`user_nl_cam` (CAM6, atmosphere) and `user_nl_clm` (CLM5, land).

Input  : out/production/<realm>.csv   (frequency | time_ave_or_inst | variables)
         i.e. the raw model field names the CMIP7 request needs, per realm.
Output : out/namelists/user_nl_cam, out/namelists/user_nl_clm, tapes.csv

Realms are folded into components the way the model is built:
    CAM  <- atmos, aerosol, atmosChem          CLM  <- land, landIce

How the mapping works
---------------------
One history tape per requested output frequency:

    frequency   nhtfrq   meaning
    mon           0      monthly means (CESM default tape cadence)
    day         -24      daily
    6hr          -6
    3hr          -3
    1hr          -1
    yr        -8760      365 days - ONLY correct on a NO_LEAP calendar

`mfilt` (samples per file) is derived from --days-per-file, so every tape
rolls over at the same wall-clock cadence (default: one file per 30 days;
monthly and annual tapes always get mfilt = 1).

The requested statistic becomes an explicit per-field flag, so a tape can mix
them: `'TREFHT:A'` average, `'PS:I'` instantaneous, `'TREFHTMX:X'` maximum,
`'TREFHTMN:M'` minimum. A field can only appear ONCE per tape, so when the same
field is requested at one frequency with two statistics (CAM needs PS, T, PSL,
U and V at 6hr both averaged and instantaneous) the extra copy goes to a second
tape of the same frequency - that is what `6hr` splitting in the report means.

`empty_htapes` is set, so the model writes ONLY what the Data Request asks for.

What is deliberately left out
-----------------------------
  * `fx` (time-invariant) variables - area, land fraction and the like are
    written on every history file by the model itself, or come from the domain
    file; they are listed in the report, not in a tape.
  * everything that is not `mapped`: the production tables only carry fields the
    model already writes. The new CMIP7 variables have no raw name yet (see
    cmip7-lookup/), so they cannot go in a namelist until someone fills them in.

Field names are NOT validated against the model's master field list - pass
--valid-fields with a list (one name per line, e.g. from `ncdump -h` of an
existing history file) to have them checked.

Usage:
    python make_namelists.py
    python make_namelists.py --days-per-file 365 --outdir out/namelists
    python make_namelists.py --valid-fields cam_master_fields.txt
"""
import argparse
import csv
import os
import textwrap
from collections import defaultdict, OrderedDict

COMPONENTS = OrderedDict([
    ("cam", {"realms": ["atmos", "aerosol", "atmosChem"], "model": "CAM6",
             "prefix": "", "max_tapes": 10}),
    ("clm", {"realms": ["land", "landIce"], "model": "CLM5",
             "prefix": "hist_", "max_tapes": 6}),
])

# frequency -> (nhtfrq, samples per day). nhtfrq < 0 is hours, 0 is monthly.
FREQ = OrderedDict([
    ("mon", (0, None)),
    ("day", (-24, 1)),
    ("6hr", (-6, 4)),
    ("3hr", (-3, 8)),
    ("1hr", (-1, 24)),
    ("yr", (-8760, None)),
])
# requested statistic -> CESM history averaging flag
FLAG = {"ave": "A", "inst": "I", "max": "X", "min": "M", "clim": "A"}
SKIP_FREQ = {"fx"}                      # time-invariant: not a history tape

# CMIP's MONTHLY tasmax/tasmin are the monthly MEAN OF THE DAILY extreme, not the
# monthly extreme - so on a monthly tape CAM must write its own averaged-daily-max
# fields, averaged (A), not TREFHTMX with an X flag. Same rule as
# cmip_reformatter/manage_tables.py:fix_lookup_table for APmon/Amon.
MONTHLY_MEAN_OF_DAILY = {"cam": {"TREFHTMX": "TREFMXAV", "TREFHTMN": "TREFMNAV"}}


def read_production(prod_dir, realms):
    """[(frequency, cell, [raw fields])] for the given realms."""
    out = []
    for realm in realms:
        path = os.path.join(prod_dir, f"{realm}.csv")
        if not os.path.exists(path):
            continue
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                fields = [v.strip() for v in r["variables"].split(",") if v.strip()]
                if fields:
                    out.append((r["frequency"].strip(),
                                r["time_ave_or_inst"].strip(), fields, realm))
    return out


def build_tapes(rows, comp, keep_nonstandard=False):
    """Assign fields to tapes: one per frequency, plus an extra tape whenever the
    same field is requested twice at that frequency with different statistics.
    Return ([tape, ...], skipped, notes); tape = dict(freq, fields{name: flag})."""
    by_freq = defaultdict(list)                      # freq -> [(field, flag)]
    skipped, notes = [], []
    fixes = MONTHLY_MEAN_OF_DAILY.get(comp, {})
    for freq, cell, fields, realm in rows:
        if freq in SKIP_FREQ:
            skipped += [{"field": f, "frequency": freq, "cell": cell,
                         "realm": realm, "reason": "time-invariant (fx): written "
                         "with every history file / from the domain file"}
                        for f in fields]
            continue
        if freq not in FREQ:
            skipped += [{"field": f, "frequency": freq, "cell": cell,
                         "realm": realm, "reason": f"frequency '{freq}' has no "
                         "history-tape equivalent - post-process from a finer tape"}
                        for f in fields]
            continue
        flag = FLAG.get(cell)
        if flag is None:
            skipped += [{"field": f, "frequency": freq, "cell": cell,
                         "realm": realm, "reason": f"unknown statistic '{cell}'"}
                        for f in fields]
            continue
        for f in fields:
            # NB: never rebind `flag` here - it is the statistic of the whole row
            field, fl = f, flag
            # CESM history fields are upper case. An all-lower-case name from the
            # lookup tables is a subgrid weight (pfts1d_wtgcell, cols1d, ...), not
            # a history field: the CMIP7 variables behind it (the *Lut set, the
            # vegetation fractions) need CLM 1-D subgrid output, which is a tape
            # setting, not a fincl entry. Keep it out or the build fails.
            if not keep_nonstandard and not any(c.isupper() for c in field):
                skipped.append({"field": field, "frequency": freq, "cell": cell,
                                "realm": realm, "reason": "subgrid weight, not a "
                                "history field - needs 1-D subgrid output "
                                "(hist_dov2xy/hist_type1d_pertape), see the note "
                                "at the end of the namelist"})
                continue
            if freq == "mon" and field in fixes:
                notes.append(f"{field}:{fl} at mon -> {fixes[field]}:A  (CMIP monthly "
                             f"tasmax/tasmin = mean of the daily extreme)")
                field, fl = fixes[field], "A"
            elif freq == "mon" and fl in ("X", "M"):
                notes.append(f"CHECK {field}:{fl} at mon - if the CMIP variable is "
                             f"the monthly MEAN of a daily extreme, this tape "
                             f"should carry the model's averaged-daily field instead")
            by_freq[freq].append((field, fl))

    tapes = []
    for freq in FREQ:                                # keep the canonical order
        if freq not in by_freq:
            continue
        stacks = []                                  # [{field: flag}, ...]
        for field, flag in by_freq[freq]:
            for s in stacks:
                if field not in s:                   # a field may appear once/tape
                    s[field] = flag
                    break
                if s[field] == flag:                 # already requested identically
                    break
            else:
                stacks.append({field: flag})
        for s in stacks:
            tapes.append({"freq": freq, "fields": s})
    return tapes, skipped, notes


def mfilt_of(freq, days_per_file):
    per_day = FREQ[freq][1]
    return 1 if per_day is None else max(1, per_day * days_per_file)


def fmt_list(name, values, width=92):
    """`name = 'A', 'B', ...` wrapped over several lines (valid namelist input)."""
    body = ", ".join(f"'{v}'" for v in values)
    pad = " " * (len(name) + 4)
    lines = textwrap.wrap(body, width=width - len(pad), break_long_words=False)
    return f" {name} = " + ("\n" + pad).join(lines)


def write_namelist(path, comp, tapes, days_per_file, meta, subgrid=()):
    p = COMPONENTS[comp]["prefix"]
    L = [f"! {'-' * 76}",
         f"! {COMPONENTS[comp]['model']} history output for the CMCC CMIP7 "
         f"(AR7 fast-track) data request",
         f"! generated by make_namelists.py from {meta['source']}",
         f"! {meta['n_fields']} distinct fields, {len(tapes)} history tapes "
         f"({', '.join(t['freq'] for t in tapes)})",
         "! Statistic flags: A average, I instantaneous, X maximum, M minimum.",
         f"! {'-' * 76}", ""]
    L.append(f" {p}empty_htapes = .true.")
    L.append(fmt_list(f"{p}nhtfrq", []) if False else
             f" {p}nhtfrq = " + ", ".join(str(FREQ[t['freq']][0]) for t in tapes))
    L.append(f" {p}mfilt  = " +
             ", ".join(str(mfilt_of(t["freq"], days_per_file)) for t in tapes))
    # the per-tape flag is the one most fields on that tape use; every field also
    # carries its own explicit flag, which wins
    pertape = []
    for t in tapes:
        counts = defaultdict(int)
        for fl in t["fields"].values():
            counts[fl] += 1
        pertape.append(max(counts, key=counts.get))
    L.append(f" {p}avgflag_pertape = " + ", ".join(f"'{f}'" for f in pertape))
    L.append("")
    for i, t in enumerate(tapes, start=1):
        nh, mf = FREQ[t["freq"]][0], mfilt_of(t["freq"], days_per_file)
        L.append(f"! h{i-1}: {t['freq']}  ({len(t['fields'])} fields, "
                 f"nhtfrq={nh}, mfilt={mf})")
        vals = [f"{f}:{fl}" for f, fl in sorted(t["fields"].items())]
        L.append(fmt_list(f"{p}fincl{i}", vals))
        L.append("")
    if subgrid:
        L += ["! " + "-" * 76,
              "! NOT configured here - these CMIP7 variables are per-landunit / "
              "per-PFT",
              "! quantities (the *Lut set, vegetation fractions). They need a "
              "dedicated 1-D",
              "! subgrid tape, not a field name, e.g. for tape hN:",
              "!     hist_dov2xy(N) = .false.",
              "!     hist_type1d_pertape(N) = 'PFTS'   ! or 'COLS' / 'LAND'",
              "! and then the ordinary fields on that tape. Decide with the land "
              "group:"]
        for field, vars_ in subgrid:
            L.append(f"!   {field:18s} -> {vars_}")
        L.append("! " + "-" * 76)
    with open(path, "w") as f:
        f.write("\n".join(L).rstrip() + "\n")


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--prod-dir", default=os.path.join(here, "out", "production"))
    ap.add_argument("--detail", default=os.path.join(here, "out", "raw",
                                                     "mapping_detail.csv"),
                    help="mapping_detail.csv, for the CMOR provenance in tapes.csv")
    ap.add_argument("--outdir", default=os.path.join(here, "out", "namelists"))
    ap.add_argument("--days-per-file", type=int, default=30,
                    help="wall-clock days per history file (default 30)")
    ap.add_argument("--keep-nonstandard", action="store_true",
                    help="keep all-lower-case names (subgrid weights) in the fincl "
                         "lists; they are excluded by default because CESM rejects "
                         "them as history fields")
    ap.add_argument("--valid-fields", default="",
                    help="file with one valid model field name per line; unknown "
                         "fields are reported (nothing is checked without it)")
    args = ap.parse_args()

    valid = set()
    if args.valid_fields:
        with open(args.valid_fields) as f:
            valid = {l.strip() for l in f if l.strip() and not l.startswith("#")}

    # CMOR provenance: raw field -> the CMIP7 variables it serves
    serves = defaultdict(set)
    if os.path.exists(args.detail):
        with open(args.detail, newline="") as f:
            for r in csv.DictReader(f):
                for m in r["model"].split(","):
                    if m.strip():
                        serves[m.strip()].add(r["cmip6_name"])

    os.makedirs(args.outdir, exist_ok=True)
    report, unknown = [], defaultdict(list)
    for comp, cfg in COMPONENTS.items():
        rows = read_production(args.prod_dir, cfg["realms"])
        tapes, skipped, notes = build_tapes(rows, comp, args.keep_nonstandard)
        fields = {f for t in tapes for f in t["fields"]}
        path = os.path.join(args.outdir, f"user_nl_{comp}")
        subgrid = sorted({(s["field"], " ".join(sorted(serves.get(s["field"], []))))
                          for s in skipped if "subgrid weight" in s["reason"]})
        write_namelist(path, comp, tapes, args.days_per_file,
                       {"source": os.path.relpath(args.prod_dir, here) +
                        f"/{{{','.join(cfg['realms'])}}}.csv",
                        "n_fields": len(fields)}, subgrid)

        print(f"\n=== {cfg['model']}  ->  {path}")
        print(f"{'tape':6s} {'freq':5s} {'nhtfrq':>7s} {'mfilt':>6s} {'fields':>7s}"
              f"  statistics")
        for i, t in enumerate(tapes):
            counts = defaultdict(int)
            for fl in t["fields"].values():
                counts[fl] += 1
            print(f"h{i:<5d} {t['freq']:5s} {FREQ[t['freq']][0]:7d} "
                  f"{mfilt_of(t['freq'], args.days_per_file):6d} "
                  f"{len(t['fields']):7d}  "
                  + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        print(f"{'':6s} {'TOTAL':5s} {'':7s} {'':6s} {len(fields):7d} distinct fields")
        if len(tapes) > cfg["max_tapes"]:
            print(f"[warn] {len(tapes)} tapes exceeds the {cfg['model']} limit of "
                  f"{cfg['max_tapes']} - merge frequencies or drop one")
        for s in skipped:
            print(f"[skip] {s['field']:16s} {s['frequency']:4s} {s['reason']}")
        for n in notes:
            print(f"[{'fix' if '->' in n else 'chk'}]  {n}")
        if valid:
            miss = sorted(f for f in fields if f not in valid)
            print(f"[check] {len(fields) - len(miss)}/{len(fields)} fields in the "
                  f"master list" + (f"; UNKNOWN: {', '.join(miss)}" if miss else ""))
            unknown[comp] = miss
        # CESM history fields are upper-case; an all-lower-case name is almost
        # always subgrid metadata or a restart/surface-dataset variable that the
        # lookup tables point at, and the model will reject it in a fincl list
        suspect = sorted(f for f in fields if not any(c.isupper() for c in f))
        if suspect:
            print(f"[chk]  not a history field? (all lower case, likely subgrid "
                  f"metadata written automatically): {', '.join(suspect)}")

        for i, t in enumerate(tapes):
            for f, fl in sorted(t["fields"].items()):
                report.append({"component": cfg["model"], "tape": f"h{i}",
                               "frequency": t["freq"],
                               "nhtfrq": FREQ[t["freq"]][0],
                               "mfilt": mfilt_of(t["freq"], args.days_per_file),
                               "field": f, "flag": fl,
                               "in_master_list": ("" if not valid else
                                                  str(f in valid)),
                               "note": ("" if any(c.isupper() for c in f)
                                        else "all lower case - check it is a real "
                                             "history field, not subgrid metadata"),
                               "cmip7_variables": " ".join(sorted(serves.get(f, [])))})
        for s in skipped:
            report.append({"component": cfg["model"], "tape": "(none)",
                           "frequency": s["frequency"], "nhtfrq": "", "mfilt": "",
                           "field": s["field"], "flag": "", "in_master_list": "",
                           "cmip7_variables": " ".join(sorted(serves.get(s["field"], []))),
                           "note": s["reason"]})

    rep = os.path.join(args.outdir, "tapes.csv")
    with open(rep, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["component", "tape", "frequency", "nhtfrq",
                                          "mfilt", "field", "flag", "in_master_list",
                                          "cmip7_variables", "note"])
        w.writeheader()
        w.writerows(report)
    print(f"\n[write] {rep}  (field -> tape -> the CMIP7 variables it serves)")
    print("[note]  copy user_nl_cam / user_nl_clm into the case directory, then "
          "`./preview_namelists` to have CESM validate the field names")


if __name__ == "__main__":
    main()
