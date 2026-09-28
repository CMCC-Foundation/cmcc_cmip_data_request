# CMCC CMIP7 output-variable table — runbook

Turns the internal DR selection (`CMCC_CMIP7-DR-opportunities-Final`) into a
consolidated, per-realm list of CMIP7 output variables, cross-checked against the
official CMIP7 Data Request via `data_request_api`.

## Where to run
On the CMCC server / any env where `data_request_api` is pip-installed
(the laptop clone has the source but not the deps, so it can't load the DR).

```bash
conda activate <env-with-CMIP7-data-request-api>
cd dr_cmip7/cmcc_selection
```

## Step 1 — sanity-check the parse (no API needed)
```bash
python build_cmcc_cmip7_table.py --parse-only
# -> 30 High/Medium opportunities, 118 group references
```

## Step 2 — build the tables
```bash
python build_cmcc_cmip7_table.py --version v1.2.2.2 --outdir out
```
Version `v1.2.2.2` matches the internal file header (`DR-V1.2.2.2`).

Outputs in `out/`:
| file | contents |
|------|----------|
| `cmcc_groups_crosscheck.csv` | one row per requested group: matched / typo? / unmatched / ignored(note?), suggestion, tier, #vars |
| `cmcc_variables.csv`         | one row per **unique** variable: compound name, out_name, frequency, cell (ave/inst), realm, tier(s), source groups/opportunities |
| `by_realm/<realm>.csv`       | `frequency \| cell \| n \| variables` — the CMCC production-list shape |

**Read `cmcc_groups_crosscheck.csv` first** — every `typo?`/`unmatched` row is a
group name in the internal file that did not match the DR (rename, typo, or a
free-text note that leaked through the comma split, e.g. the `not…` fragment in
"Ocean Extremes"). Fix the internal file or accept, then re-run.

## Step 3 — map to model raw names (`cmip7-lookup/`)
`cmcc_variables.csv` / `by_realm/*.csv` carry **CMOR** `out_name`s. Map them to
raw model names (RELHUM/PS/T…) with the in-repo lookup tables — no clone needed:
```bash
cd cmcc_selection && python map_to_raw_names.py 2>/dev/null
# reads ../cmip7-lookup/*_lookup.csv   (--lookup-dir to point elsewhere)
```
Outputs under `out/raw/`: `by_realm/*.csv` (raw names), `mapping_detail.csv`
(audit; `lookup` = `<component>:<table set>`, `*` = realm mismatch), and
**`unmapped.csv`** — selected vars with no raw-model equivalent = production gap
to triage. `out/production/*.csv` is the hand-off table (raw names only).

Optional: `--fallback-lookup-dir ../cmip_reformatter/cmip-tables/cmip6/variables`
pulls in ~23 names the cmip6plus tables lack (`co2`, `fco2nat`, `rtmt`, some
land-carbon), for which you need the reformatter clone:
```bash
git clone https://github.com/CMCC-Foundation/cmip_reformatter.git   # in dr_cmip7/
```

## Step 4 — data-volume estimate (CMIP6 ref ≈ 100 GB / model-year)
Reuses the DR size math but with a PER-REALM grid (atmos vs ocean) and totals
over our exact selection. Grids are set in the script (HGRID/VLEV; default
CMCC-ESM2: CAM5.3 288×192 L30, NEMO ORCA1 362×292 L50 — edit for other configs):
```bash
python estimate_volume.py --version v1.2.2.4 2>/dev/null
```
Prints GB/model-year totals + per-realm + per-frequency, split request (all 853)
vs producible (mapped 497); writes `out/volume_by_variable.csv`.

## Step 5 — push the gaps into the lookup tables (to fill by hand)
```bash
python build_cmip7_lookup.py       # --dry-run to preview, --true-gap-only to skip derivable
```
Appends every requested variable with no raw name to
`../cmip7-lookup/<component>_lookup.csv` as a row with an **empty `model`**,
keeping the original 4-column format and the original block byte-identical (row
order taken from `--reference-dir`, the cmip6plus tables). Fill `model` → re-run
step 3 and the variable becomes `mapped`. Idempotent (existing cells copied
verbatim, only missing variables appended) and it verifies that every requested
CMOR name has a row. Needs no API — see
[`../cmip7-lookup/README.md`](../cmip7-lookup/README.md).

## Step 6 — CESM history namelists (no API)
```bash
python make_namelists.py                  # --days-per-file 365, --valid-fields ...
```
Turns `out/production/<realm>.csv` into `out/namelists/user_nl_cam` (CAM6: atmos +
aerosol + atmosChem) and `out/namelists/user_nl_clm` (CLM5: land + landIce), plus
`tapes.csv` (field → tape → the CMIP7 variables it serves). One history tape per
requested frequency (`nhtfrq`/`mfilt` from `--days-per-file`), the statistic as an
explicit per-field flag (`'TREFHT:A'`, `'PS:I'`, `'TREFHTMX:X'`), `empty_htapes`
set. A frequency gets a second tape when one field is requested there both
averaged and instantaneous (CAM 6hr). Copy into the case and run
`./preview_namelists` — that is what actually validates the field names.

## Step 7 — gap provenance / heavy variables (no API)
```bash
python truegap_provenance.py > truegap_summary.txt 2>/dev/null   # Division -> opp -> group -> vars
python find_heavy_vars.py --realm ocean --freq 3hr               # out/heavy_ocean_3hr.csv
```

## Tuning knobs
- `KEEP_PRIORITIES` in the script — currently `{high, medium}` (CMCC per-opportunity priority).
- `tier_of()` — parses `tier1/tier2` from group names for the tier split.
- `time_cell()` — collapses `cell_methods`/`temporal_shape` to `ave|inst|clim|max|min`.
