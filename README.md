# CMCC CMIP7 data request

Tools to turn the internal **CMCC CMIP7 data-request selection** into a concrete
list of model output variables:

1. read which Data Request (DR) *opportunities* and *variable groups* CMCC
   is interested in,
2. expand them with the official [CMIP7 Data Request API](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software)
   into the full list of CMIP7 variables,
3. translate the CMIP7 names into the **raw variable names of the CMCC-ESM3 model**
   (via lookup tables), and
4. estimate the **data volume** (GB per model-year) of the selection.

## Repository layout

| path | what it is |
|------|------------|
| `CMCC_CMIP7-DR-opportunities-Final.csv` | **The CMCC selection (source of truth).** One row per DR opportunity, with the responsible person/division, the CMCC priority (`High`, `Medium`, `Low`, `No Interest`) and the DR variable groups requested. |
| `configurations/esm3-cmip7-full.yml` | Run configuration: input CSV, DR version, lookup directory, group filters, model grid sizes for the volume estimate. |
| `generate_raw_mapping_from_dr.py` | **Main pipeline.** Selection CSV → DR variables → raw model variable lists. |
| `variable_sizes_summary.py` | Estimates the data volume (GB/year) of the selected variables, per realm. |
| `create_cmip7_lookup.py` | Builds a new set of CMIP7 lookup tables from the DR output and a reference (CMIP6plus) set of tables. |
| `cmip6plus-lookup/` | Reference lookup tables (`atm`, `ice`, `lnd`, `ocn`, `ocnbgc`) from the `cmip_reformatter`: CMIP6plus variable → raw model field. All 373 rows are filled in. Treat as read-only. |
| `cmip7-lookup/` | **The CMIP7 lookup tables we maintain.** Same 4-column format as the reference, extended with the requested variables that still need a raw name. See [`cmip7-lookup/README.md`](cmip7-lookup/README.md). |
| `CMIP7_DReq_Software/` | Upstream CMIP7 Data Request software (git submodule). |
| `environment.yml` | Conda environment (`cmcc-dr-cmip7`). |

## Setup

Clone the repository together with the Data Request submodule:

```bash
git clone --recurse-submodules https://github.com/CMCC-Foundation/cmcc_cmip_data_request
```

If you cloned without `--recurse-submodules`, `CMIP7_DReq_Software/` is empty;
fill it with:

```bash
git submodule update --init
```

Create and activate the conda environment (default name `cmcc-dr-cmip7`, use
`--name` to pick another):

```bash
conda env create -f environment.yml
conda activate cmcc-dr-cmip7

# later, to pick up changes in environment.yml
conda env update -f environment.yml
```

The environment installs `CMIP7-data-request-api`, which downloads the Data Request
content for the requested version the first time it is used, so the first run of
`generate_raw_mapping_from_dr.py` and `variable_sizes_summary.py` needs network access.

## Workflow

Both scripts take the **configuration file** as their only argument. The output
directory is named after the config file (`esm3-cmip7-full.yml` →
`esm3-cmip7-full/`), created in the current directory.

```bash
# 1) selection -> DR variables -> raw model variable lists
python generate_raw_mapping_from_dr.py configurations/esm3-cmip7-full.yml

# 2) data volume of the variables that have a raw mapping
python variable_sizes_summary.py configurations/esm3-cmip7-full.yml
```

Step 2 reads the output of step 1, so run them in this order and from the same
directory. Both need `data_request_api`.

### Step 1: `generate_raw_mapping_from_dr.py`

1. **Parse the selection CSV.** Every opportunity row is read together with its
   priority and list of variable groups. Free-text notes in brackets are
   stripped from group names. `select_groups` / `exclude_groups` from the config
   filter the groups.
2. **Load the Data Request** for `dreq_version` and index its variable groups.
3. **Expand the groups** into variables. Only global-region (`glb`) variables are
   kept; a variable requested by several groups/opportunities is stored once, with
   all its groups, opportunities, priorities and tiers recorded. Two groups
   renamed between DR versions are remapped through `ALIASES` in the script
   (`omip_geometry_physics → omip_scalars_high_priority`,
   `hydro_modelling_PET_daily → WaterResourcesPET_daily`).
4. **Look each variable up** in `cmip7-lookup/<component>_lookup.csv`. The realm is
   mapped to a lookup component the way the reformatter groups them:

   | DR realm | lookup table |
   |----------|--------------|
   | `atmos`, `aerosol`, `atmosChem` | `atm` |
   | `land`, `landIce` | `lnd` |
   | `ocean` | `ocn` |
   | `ocnBgchem` | `ocnbgc` |
   | `seaIce` | `ice` |

   Rows whose `model` is `DISCARD` are skipped.
5. **Write the outputs** to `esm3-cmip7-full/`:

| file | contents |
|------|----------|
| `cmcc_data_request.csv` | One row per DR compound variable requested by CMCC: `compound_name`, `cmip6_name`, `out_name`, `frequency`, `time_oper` (`ave`/`inst`/`max`/`min`/`clim`/`fixed`), `realm`, `cmip6_table`, `long_name`, `dimensions`, `tiers`, `groups`, `opportunities`, `priorities`, `cell_methods`. |
| `cmcc_data_selected.csv` | The subset of the above that has an entry in the lookup tables, same columns. This is the input of the volume estimate. |
| `<comp>_raw_list.txt` | One file per component (`atm`, `ice`, `lnd`, `ocn`, `ocnbgc`): the raw model fields to output, grouped by frequency and time operation. This is the production list. |

A `<comp>_raw_list.txt` looks like:

```
mon
operation: ave
FLNS, FLNT, PS, ...

day
operation: max
TREFHTMX
```

### Step 2: `variable_sizes_summary.py`

For every row of `cmcc_data_selected.csv` it computes the uncompressed size of one
model-year as

```
GB/year = (product of the spatial dimensions) x (time steps per year) x 4 bytes / 1024^3
```

and prints a table by realm (variable count, GB/yr, TB/yr) and a total. Notes:

- Time steps per year come from the frequency (`mon` = 12, `day` = 365, `3hr` = 2920, `fx` = 1, ...).
- Dimension sizes come from the DR; the grid of the model is set in the config:
  - `spatial_defaults` gives `[lon, lat, lev]` per realm. The defaults describe CMCC-ESM3:
    atmosphere/land on a spectral-element grid with 48 600 columns and 58 levels,
    ocean/sea ice on a 360×291 NEMO grid with 75 levels.
  - `other_dims` gives sizes for dimensions that are not on those grids
    (`sdepth`, `soilpools`, `spectband`, `alevel`, `olevel`, ...).
- Values are 4-byte floats with **no compression** (factor 1.0). Multiply by the
  expected deflate ratio for archived size.
- Only mapped variables are counted: the estimate is "what we can produce today",
  not the full request.

### Configuration reference

`configurations/esm3-cmip7-full.yml`:

| key | meaning |
|-----|---------|
| `input_csv` | The selection CSV (`CMCC_CMIP7-DR-opportunities-Final.csv`). |
| `dreq_version` | Data Request version to query, e.g. `v1.2.2.5`. |
| `lookup_dir` | Directory with the `*_lookup.csv` tables (`cmip7-lookup`). |
| `select_groups` | If non-empty, process **only** these variable groups. |
| `exclude_groups` | Variable groups to skip. |
| `spatial_defaults` | `[lon, lat, lev]` per realm, used for the volume estimate. |
| `other_dims` | Fallback sizes for non-standard dimensions. |

To try a different selection (for example only the baseline groups), copy the file
under a new name and edit it. The new name becomes the output directory:

```yaml
select_groups: [baseline_monthly, baseline_daily, baseline_fixed, baseline_subdaily]
```

## The selection CSV

`CMCC_CMIP7-DR-opportunities-Final.csv` is organised by area (Atmosphere, Earth
system, Impacts & Adaptation, Land & Land-Ice, Ocean & Sea-Ice). Columns:
person, division, opportunity name, CMCC priority, DR variable groups, and the
total number of variables. The first row is the baseline opportunity
(`Baseline Climate Variables for Earth System Modelling`). Of the 48 opportunities,
21 are `High`, 9 `Medium` and 18 `No Interest`.

> Note that `parse_cmcc_csv` currently reads **every** row that has an opportunity name
> and group list, whatever its priority; rows without groups (such as `No Interest`)
> contribute nothing. Use `exclude_groups` / `select_groups` to narrow the selection.

## The lookup tables

Each `*_lookup.csv` has four columns:

```
variable,reprocess,model,long_name
```

| column | meaning |
|--------|---------|
| `variable` | CMIP6/CMOR variable name (the join key with the Data Request's `cmip6_name`). |
| `reprocess` | `True`/`False`: whether the reformatter has to post-process the raw field. Must stay a Python literal. |
| `model` | Raw CMCC-ESM3 field(s). Several fields are comma-separated and quoted: `"SOILLIQ, SOILICE"`. |
| `long_name` | Variable description. |

`cmip6plus-lookup/` holds the original, fully mapped tables (373 rows). `cmip7-lookup/`
contains those rows plus the requested CMIP7 variables that have no raw name yet,
with an **empty `model`** (386 rows to fill, out of 759):

| table | rows | filled | to fill |
|-------|-----:|-------:|--------:|
| `atm_lookup.csv` | 218 | 77 | 141 |
| `ice_lookup.csv` | 83 | 59 | 24 |
| `lnd_lookup.csv` | 234 | 112 | 122 |
| `ocn_lookup.csv` | 103 | 70 | 33 |
| `ocnbgc_lookup.csv` | 121 | 55 | 66 |

To close a gap, fill the `model` cell (for example `snw,False,H2OSNO,Surface Snow Amount`)
and re-run step 1: the variable is then included in the raw lists. More detail on the
table structure, counts and how to decide on a gap is in
[`cmip7-lookup/README.md`](cmip7-lookup/README.md).

### Regenerating the tables: `create_cmip7_lookup.py`

Builds `<comp>_lookup.csv` from `cmcc_data_request.csv` (output of step 1) and the
reference tables: variables whose CMIP6 name is in `cmip6plus-lookup/` get its
`reprocess` and `model`; the others are written with `model` set to `DISCARD`.

```bash
python create_cmip7_lookup.py \
    --mapped esm3-cmip7-full/cmcc_data_request.csv \
    --lookup-dir cmip7-lookup \
    --reference-dir cmip6plus-lookup \
    --force
```

| option | default | meaning |
|--------|---------|---------|
| `--mapped` | `dr-cmip7-full/cmcc_data_request.csv` | output of step 1 (note: the default path is not the one step 1 now writes, pass it explicitly) |
| `--lookup-dir` | `cmip7-lookup` | tables to write |
| `--reference-dir` | `cmip6plus-lookup` | reference tables |
| `-f`, `--force` | off | overwrite existing tables; without it the script stops if a table exists |

> **Caution.** `--force` **replaces** the tables in `--lookup-dir`, including any `model`
> cells filled in by hand. It also writes a fifth column (`cmip6_name`) and marks
> unmapped variables `DISCARD` rather than leaving `model` empty, so its output is not
> identical to the committed `cmip7-lookup/` tables. Write to a different
> `--lookup-dir` first and compare.

## Variable names: CMIP6 vs CMIP7

CMIP7 uses *branded* variables: the daily maximum of near-surface temperature is a
branded variant of `tas` rather than a variable called `tasmax`. The lookup tables are keyed on
the **CMIP6 name** (`cmip6_name`, e.g. `tasmax`), which is the name the reformatter
uses. One lookup row therefore serves a variable at every frequency and statistic
it is requested at, which is why there are fewer table rows than compound variables.

## Known caveats

- A lookup row with an **empty** `model` is not skipped by `generate_raw_mapping_from_dr.py`
  (only `DISCARD` is), so unfilled rows can produce an empty entry in the raw lists.
  Fill the row, set it to `DISCARD`, or remove it.
- `create_cmip7_lookup.py` and `generate_raw_mapping_from_dr.py` do not share a
  default output directory; pass paths explicitly as shown above.
- The volume estimate covers only variables that have a lookup entry.

## Requirements

Python with the packages in `environment.yml` (`numpy`, `pyyaml`, `requests`,
`openpyxl`, `pooch`, `bs4`, `pytest`, `coverage`) and `CMIP7-data-request-api`
(installed with pip by the environment file).
