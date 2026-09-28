# CMCC CMIP7 output-variable selection

Turn the internal **CMCC CMIP7 data-request selection** into a concrete list of
model output variables — cross-checked against the official CMIP7 Data Request,
translated to the model's raw variable names, and sized in GB/model-year.

All the tooling lives in [`cmcc_selection/`](cmcc_selection/). This page is the
30-second guide; [`cmcc_selection/RUNBOOK.md`](cmcc_selection/RUNBOOK.md) has the
details and tuning knobs.

## Repository organization

| path | what it is |
|------|------------|
| `CMCC_CMIP7-DR-opportunities-Final*` | the internal CMCC selection (source of truth): opportunities, CMCC priority, variable groups |
| `cmcc_selection/` | our scripts + outputs |
| `cmip7-lookup/` | **the CMOR→raw-name tables we maintain** — mappings *and* the 322 true-gap rows to fill by hand ([details](cmip7-lookup/README.md)) |
| `CMIP7_DReq_Software` | upstream CMIP7 Data Request API (git submodule) |
| `cmip_reformatter/` | the reformatter itself (clone; gitignored). `cmip7-lookup/` was seeded from its `cmip-tables/cmip6plus/variables/`; `cmip-tables/cmip6/variables/` has ~23 extra names (`co2`, `fco2nat`, `rtmt`, land-carbon…) usable via `--fallback-lookup-dir` |

## Setup (once, on the server)

To get the project's code, along with the CMIP7 Data Request Software, use the following command

`git clone --recurse-submodules https://github.com/giovanniconti83/dr_cmip7`

If you already cloned the project and forgot `--recurse-submodules`, the folder CMIP7_DReq_Software will be empty, 
but the submodule content can be initialized by running
`git submodule update --init`

The working environment can be setup using the provided anaconda3 `environment.yml` file:

`conda env create -f environment.yml`

The environment is called `cmcc-dr-cmip7` by default, but it is possible to use the option `--name SOME_ENVIRONMENT_NAME` to define a custom name. 
You should then activate the conda python environment using the command:

`conda activate cmcc-dr-cmip7`

To update your environment with following changes to the env file use

`conda env update -f environment.yml`

## Run it — 5 commands

```bash
cd cmcc_selection

# 1) select + expand + cross-check   -> the CMOR variable list   [needs the DR API]
python build_cmcc_cmip7_table.py --version v1.2.2.4 --outdir out 2>/dev/null

# 2) translate to raw model names     -> the production list
python map_to_raw_names.py 2>/dev/null
#    reads ../cmip7-lookup/*_lookup.csv
#    (optionally pull in the older cmip6 table for names it lacks:
#     --fallback-lookup-dir ../cmip_reformatter/cmip-tables/cmip6/variables )

# 3) estimate data volume             -> GB / model-year          [needs the DR API]
python estimate_volume.py --version v1.2.2.4 2>/dev/null

# 4) push the gaps back into the lookup tables, to be filled by hand
python build_cmip7_lookup.py            # --dry-run to preview

# 5) turn the production tables into CESM history namelists
python make_namelists.py                # -> out/namelists/user_nl_cam, user_nl_clm
```

(`2>/dev/null` just hides harmless `modeling_realm_-_primary` API warnings.)

Steps 1 and 3 need `data_request_api` (run them on the server env); steps 2 and 4
and every `truegap_*`/`find_heavy_vars` script are pure post-processing and run
anywhere.

### The gap-closing loop

`build_cmip7_lookup.py` appends every requested variable that has no raw name to
`cmip7-lookup/<component>_lookup.csv` as a row with an **empty `model`** column,
keeping the tables in their original 4-column reformatter format
(`variable,reprocess,model,long_name`) with the original block untouched:

```
zg7h,True,"Z3, PS, T",Geopotential Height     <- end of the original block
abs550bc,False,,black carbon aaod@550nm       <- appended: fill `model`
```

Fill `model` with the raw model field name → the next `map_to_raw_names.py` run
counts the variable as `mapped` and puts it in `out/production/`. 759 rows now:
**373 mapped, 386 to fill** (322 true_gap + 64 derivable). The merge is
idempotent — existing cells are copied verbatim, only missing variables are
appended — and it ends with a coverage check (`660/660 expected CMOR names
present`). Realm/Division/GB context stays in `out/raw/unmapped.csv` and
`out/truegap_*.csv`. See [`cmip7-lookup/README.md`](cmip7-lookup/README.md).

## What you get (in `cmcc_selection/out/`)

| file | contents |
|------|----------|
| `cmcc_variables.csv` | **one row per unique CMOR variable** — compound name, `cmip6_name`, `out_name`, frequency, cell (ave/inst), realm, tier, and which groups/opportunities requested it |
| `cmcc_variables_mapped.csv` | same + `raw_name`, `in_reformatter`, `map_category` (mapped/derivable/true_gap), `GB_per_year` (physical), `GB_per_year_counted` (0 for derivable) |
| `cmcc_groups_crosscheck.csv` | **one row per requested group** — matched / aliased / unresolved, + variable count (the audit trail) |
| `by_realm/<realm>.csv` | per realm: `frequency \| cell \| n \| variables_dr \| GB_per_year` (DR names) |
| `raw/by_realm/<realm>.csv` | per realm: `variables_dr \| variables_raw \| variables_unmapped_derivable \| variables_unmapped_true_gap \| GB_per_year_raw \| GB_per_year_true_gap` — the production list |
| `raw/mapping_detail.csv` | every directly-mapped DR var → raw name, which lookup, `reprocess` flag |
| `raw/unmapped.csv` | **triage sheet** for vars with no direct raw mapping — see below |
| `volume_by_variable.csv` | per-variable GB/model-year, largest first |
| `namelists/user_nl_cam`, `namelists/user_nl_clm` | CESM history namelists: one tape per frequency, statistic as a per-field flag, `empty_htapes` set |
| `namelists/tapes.csv` | audit: field → tape → the CMIP7 variables it serves, plus what was left off a tape and why |

### Mapping outcomes (three buckets)

Each selected variable ends up in exactly one bucket:

- **mapped** — its exact CMIP6 name has a raw `model` name in `cmip7-lookup/` →
  produced directly (`tasmax→TREFHTMX`, `chlos→chl` with `reprocess`).
- **derivable** — the CMIP6 name is absent but its *base field* (the `out_name`)
  is in the lookup → produce the base raw var and post-process
  (`thetao200` from `thetao`; `base_raw` column names it).
- **true_gap** — neither is known → not producible as-is (`co2s`, hemispheric
  sea-ice scalars, most `aerosol`/`atmosChem`). These now also sit in
  `cmip7-lookup/` as empty-`model` rows to fill in (step 4 above); a lookup row
  whose `model` is still empty is ignored by the mapper, so the variable keeps
  showing up as a gap until someone resolves it.

`raw/unmapped.csv` lists the **derivable** and **true_gap** ones, sorted by
realm then category, with columns `realm | category | cmip6_name | out_name |
base_raw | frequency | cell | decision | …`. Fill the empty **`decision`**
column (`drop` / `add` / `derive`) with the colleague to resolve the gaps. The
run also prints a per-realm `mapped | derivable | true_gap` summary.

> **CMIP6 vs CMIP7 names.** CMIP7 uses *branded* variables: the daily max of
> `tas` has `out_name=tas` (+ `cell=max`), not `tasmax`. We therefore key both the
> display and the reformatter join on `cmip6_name` (`tasmax`, `mrsos`, …) — the
> name the reformatter lookups use — so no branded variable is hidden under or
> mis-mapped to its root.

## Do we have ALL the CMCC-requested variables?

The CMCC request is defined at the **variable-group** level, so "we have every
requested variable" ⇔ "every requested group was found in the DR and fully
expanded." Two things make that easy to trust:

**1. The build refuses to under-deliver.** `build_cmcc_cmip7_table.py` prints a
coverage line and **exits non-zero** if any requested group is left unresolved:

```
[check] 115 matched, 2 aliased, 0 unresolved
```

`matched` = group found verbatim in the DR · `aliased` = renamed group remapped
(see `ALIASES` in the script) · `unresolved` = a group we could NOT place → the
run aborts so it can never silently drop one. A clean run with `0 unresolved`
means **every group in every High/Medium opportunity was expanded in full.**

**2. One-command audit.** List anything that is not `matched`/`aliased` — it
should only be free-text notes that leaked from the CSV (e.g. a stray `not`),
never a real group:

```bash
cd cmcc_selection
python -c "
import csv, collections
rows = list(csv.DictReader(open('out/cmcc_groups_crosscheck.csv')))
print('status counts:', dict(collections.Counter(r['status'] for r in rows)))
leftover = [r for r in rows if r['status'] not in ('matched','aliased')]
print(f'{len(leftover)} not matched/aliased (expect only note fragments):')
for r in leftover:
    print('   ', r['status'], '|', r['group_requested'], '|', r['opportunity'])
"
```

**Optional sanity cross-check** against the CMCC file's own *total variables*
column — print our unique-variable count per opportunity and eyeball it (small
differences are expected: DR version drift + de-duplication of shared variables):

```bash
python -c "
import csv, collections
c = collections.Counter()
for r in csv.DictReader(open('out/cmcc_variables.csv')):
    for o in r['opportunities'].split(';'):
        c[o] += 1
for o, n in sorted(c.items()): print(f'{n:5d}  {o}')
"
```

> Note: variable *coverage* is guaranteed by group coverage above. `raw/unmapped.csv`
> is a **different** question — those variables ARE requested and present, they
> just don't yet have a raw-model translation (drop them, or extend the
> `cmip_reformatter` lookups).

## Data volume, and how it compares to CMIP6

`estimate_volume.py` prints a `GB / model-year` table and writes the cost into
`cmcc_variables_mapped.csv` (`GB_per_year`, `GB_per_year_counted`) and into every
`by_realm/*.csv`. "Per model-year" = GB written for **each simulated year** (a
100-year run ≈ 100×).

**Three categories, and how they count toward storage:**

- **mapped** — produced directly → counts its full size (`GB_per_year_raw`).
- **derivable** — a slice/aggregate of an already-stored field (e.g. `thetao200`
  from `thetao`) → **counts 0 GB**, because you don't store it separately.
- **true_gap** — not produced at all → counts only as a *potential* cost if you
  add it (`GB_per_year_true_gap`).

So the per-`(frequency,cell)` row in `raw/by_realm/*.csv` carries
`GB_per_year_raw` (stored today) and `GB_per_year_true_gap` (extra if added);
derivable variables are listed but add nothing. The printed TOTAL (v1.2.2.4,
853 vars: 436 mapped, 67 derivable, 350 true_gap; uncompressed):

```
=== GB / model-year (compression=1.0) ===  produced  true_gap    total
TOTAL                                        212.71    224.34    437.05
```

- **produced ≈ 213 GB/yr** — the mapped variables you write today.
- **true_gap ≈ 224 GB/yr** — extra storage to satisfy the still-missing request.
- **total ≈ 437 GB/yr** — full request, with derivable counted free (≈ 34 GB of
  the old naive 471 was derivable double-counting).

**vs CMIP6 (~100 GB/model-year):** produced ≈ **2×**, full request ≈ **4.4×**.

**Where the cost sits:** the true_gap is almost entirely **ocean sub-daily** —
`ocean` = 186 of the 224 GB true_gap, and by frequency `3hr` alone = 174 GB. Two
3-hourly ocean variables account for 76 % of the whole gap cost: `ficeberg`
(85.8 GB/yr) and `hfrunoffds` (85.5 GB/yr) — see the `GB_per_year` column of
`cmip7-lookup/ocn_lookup.csv`, or `out/heavy_ocean_3hr.csv`. So
the expensive part of the request is ocean 3-hourly (mostly 3-D) fields; that is
the single biggest lever if the volume needs trimming. By contrast `atmos` is
almost fully producible today (124 produced / 2 true_gap), and `6hr`/`1hr` have
no true_gap at all.

**Compression.** These figures are `--compression 1.0` = **uncompressed** (size
on disk during the run, before `parallel_nc_compress.sh`). Pass e.g.
`--compression 0.5` for the archived/deflated size (≈ 235 GB/yr request,
≈ 106 GB/yr producible). Measured raw model output is ~uncompressed (ratio ≈ 1.0);
the real deflate ratio can be plugged in once measured on a compressed file.

## Key facts / decisions

- **Priority** = CMCC per-opportunity (High + Medium): all variables of every
  listed group, no per-variable DR-priority filtering. → 30 opportunities,
  ~118 group references, **853 unique variables**, each falling into one of the
  three mapping buckets above (see the run's per-realm summary / `unmapped.csv`).
- **DR version**: the CMCC file was authored against ~v1.2.2.2 but we build
  against **v1.2.2.4**; two renamed groups are remapped via `ALIASES`
  (`omip_geometry_physics → omip_scalars_high_priority`,
  `hydro_modelling_PET_daily → WaterResourcesPET_daily`).
- **Volume grid** (in `estimate_volume.py`): CMCC-ESM3, calibrated from a real
  B1850 run — atmos/land SE grid `ncol=48600` L58, ocean/ice NEMO 360×291 L75,
  float32, raw output ~uncompressed (pass `--compression 0.5` for archived size).
  Validated: `thetao` mon = 377 MB/yr, `zos` mon = 5 MB/yr match the real files.
  Edit `HGRID`/`VLEV` for other configs. `inspect_sim.py` re-derives these from
  any archive.
