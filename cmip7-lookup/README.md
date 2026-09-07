# `cmip7-lookup/` — CMOR ↔ raw-model tables, gaps included

The **single source of truth** for "which model field produces this CMIP7
variable". One file per reformatter component — `atm`, `ice`, `lnd`, `ocn`,
`ocnbgc` — inherited from
`cmip_reformatter/cmip-tables/cmip6plus/variables/` and extended by
[`../cmcc_selection/build_cmip7_lookup.py`](../cmcc_selection/build_cmip7_lookup.py)
with every variable of the CMCC request that has no raw name yet.

---

## 1. Structure of a table

Exactly the **original 4 columns**, original row order, original CRLF line
endings — these stay drop-in reformatter tables:

```
variable,reprocess,model,long_name
```

| column | meaning |
|---|---|
| `variable` | CMOR/CMIP6 variable name — the join key with the Data Request |
| `reprocess` | `True`/`False`; `cmip_reformatter` `eval()`s it, so it must stay a Python literal |
| `model` | **raw model field name — the cell to fill.** Several fields → comma-separated inside quotes: `"SOILLIQ, SOILICE"` |
| `long_name` | variable description |

Each file has **two blocks**:

```
variable,reprocess,model,long_name
abs550aer,False,AODABS,Ambient Aerosol Absorption Optical Thickness at 550nm   ┐
...                                                                            │ 1. INHERITED block
zg500,False,Z500,Geopotential Height at 500hPa                                 │    (byte-identical to
zg7h,True,"Z3, PS, T",Geopotential Height                                      ┘     the cmip6plus table)
abs550bc,False,,black carbon aaod@550nm                                        ┐
abs550dust,False,,dust absorption aerosol optical depth @550nm                  │ 2. APPENDED block
...                                                                            │    (model empty →
snw,False,,Surface Snow Amount                                                 ┘     fill by hand)
```

1. **inherited** — the variables the model already produces, copied verbatim from
   the cmip6plus tables (nothing renamed, reordered or reformatted);
2. **appended** — the requested variables with an **empty `model`**, to be
   resolved by hand. Fill `model` (e.g. `snw` → `H2OSNO`) and the variable counts
   as `mapped` on the next `map_to_raw_names.py` run.

Realms share a component the way `cmip_reformatter` groups them:
`atmos`/`aerosol`/`atmosChem` → `atm`, `land`/`landIce` → `lnd`, `ocean` → `ocn`,
`ocnBgchem` → `ocnbgc`, `seaIce` → `ice`.

---

## 2. What is in the tables — the counts

| table | inherited | ...requested | ...**not requested** | appended | true_gap | derivable | rows | to fill |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `atm_lookup.csv` | 77 | 58 | **19** | 141 | 122 | 19 | 218 | 141 |
| `ice_lookup.csv` | 59 | 36 | **23** | 24 | 16 | 8 | 83 | 24 |
| `lnd_lookup.csv` | 112 | 92 | **20** | 122 | 99 | 23 | 234 | 122 |
| `ocn_lookup.csv` | 70 | 54 | **16** | 33 | 32 | 1 | 103 | 33 |
| `ocnbgc_lookup.csv` | 55 | 35 | **20** | 66 | 53 | 13 | 121 | 66 |
| **TOTAL** | **373** | **275** | **98** | **386** | **322** | **64** | **759** | **386** |

### 2.1 Inherited but NOT requested: 98 rows

Of the 373 inherited rows, **98 are variables no High/Medium opportunity asks
for** (19 atm, 23 ice, 20 lnd, 16 ocn, 20 ocnbgc). They are legacy CMIP6/CMIP6+
mappings that came with the tables. They are kept — a working mapping costs
nothing and may be requested later — but they are **not** part of the CMCC CMIP7
request and must not be counted as coverage of it.

The other 275 inherited rows cover **274 requested variables**: `prsn` appears
twice (`atm` with `"PRECSC,PRECSL"` and `ocn` with `prsn`), which is why the row
count is one higher than the variable count.

### 2.2 From the new request: 660 variables, 3 buckets

Every variable of the CMCC request has exactly one row per component:

| bucket | variables | where it is | what to do |
|---|---:|---|---|
| **mapped** | **274** | inherited block, `model` filled | nothing — produced today |
| **derivable** | **64** | appended, `model` empty | usually nothing: it is a slice/aggregate of a field already stored (`thetao200` from `thetao`) → post-processing, **not** a new raw field |
| **true_gap** | **322** | appended, `model` empty | **fill `model`**, or decide to derive / enable / drop |
| **total** | **660** | | |

```
274 mapped (inherited) + 386 appended (322 true_gap + 64 derivable) = 660 requested variables
660 requested + 98 inherited-not-requested + 1 duplicate row (prsn) = 759 rows
```

`build_cmip7_lookup.py` verifies this on every run:

```
[check]  660/660 expected CMOR names present -> complete   (758 rows across 5 tables)
           mapped      274/274  present
           derivable    64/64   present
           true_gap    322/322  present
           1 sit in another component's table (cross-realm, fine): sfdsi
```

(`sfdsi` is requested as `ocean` but has always lived in `ice_lookup.csv`; the
mapper resolves that across components and flags it with `*` in
`mapping_detail.csv`. 758 = 759 rows counted as distinct names, `prsn` once.)

---

## 3. Checking against the 853 estimated from the request

The request is **853**, the tables hold **660** requested variables. Nothing is
missing: the two numbers count different things.

- **853** = *requests* — one per DR **branded/compound** variable, i.e. per
  `(variable, frequency, statistic)`. That is the unit the volume estimate and
  the model namelist need.
- **660** = *variable names* — the unit a lookup table has one row for, because
  the same physical model field serves every frequency.

```
853 entries in out/cmcc_variables_mapped.csv   (853 distinct compound names)
-193 the same CMOR variable requested at several frequencies / statistics
─────
660 distinct CMOR variable names   = the rows the lookup tables need
```

Per bucket, entries ↔ names:

| bucket | entries (of 853) | names (of 660) | multi-frequency surplus |
|---|---:|---:|---:|
| mapped | 436 | 274 | 162 |
| derivable | 67 | 64 | 3 |
| true_gap | 350 | 322 | 28 |
| **total** | **853** | **660** | **193** |

Where the 193 surplus comes from — how many frequencies each name is requested at:

| entries per name | names | entries |
|---:|---:|---:|
| 1 | 533 | 533 |
| 2 | 89 | 178 |
| 3 | 20 | 60 |
| 4 | 10 | 40 |
| 5 | 6 | 30 |
| 6 | 2 | 12 |
| **total** | **660** | **853** |

The worst cases are `ta` and `ua` (6 entries each: `6hr/inst`, `day/ave`,
`mon/ave`, two branded variants each), then `pr` and `psl` (5). All six `ta`
requests are served by the single raw field `T`, hence one `ta` row.

**Consequence for the hand-filling:** one filled cell can close several gaps.
Writing `H2OSNO` into `snw` (requested at `day` *and* `mon`) resolves 2 of the
350 true-gap entries at once — that is why the mapper still reports the request
in 853/436/67/350 terms while these tables work in 759/373/386 terms.

---

## 4. How to fill a gap

```
snw,False,H2OSNO,Surface Snow Amount
```

Set `reprocess` to `True` if it needs post-processing; quote a multi-field
mapping (`"PRECSC,PRECSL"`). Then re-run the mapper:

```bash
cd cmcc_selection && python map_to_raw_names.py 2>/dev/null
```

For variables to drop, or that the model genuinely cannot produce, leave `model`
empty and record the decision in `cmcc_selection/out/raw/unmapped.csv`
(`decision` column) — these tables are 4-column reformatter tables and carry no
notes of their own.

### Context needed to decide

| question | file |
|---|---|
| realm, frequency, `derivable` vs `true_gap`, base field | `../cmcc_selection/out/raw/unmapped.csv` |
| who asked for it (Division → opportunity → group) | `../cmcc_selection/out/truegap_{high,medium}.{txt,csv}` |
| GB per model-year | `../cmcc_selection/out/volume_by_variable.csv`, `out/heavy_ocean_3hr.csv` |
| everything, per variable | `../cmcc_selection/out/cmcc_variables_mapped.csv` |

Two appended rows carry most of the cost: the 3-hourly ocean `ficeberg`
(85.8 GB/yr) and `hfrunoffds` (85.5 GB/yr) — 76 % of the 224 GB/yr the full gap
would add. Worth deciding before the small ones.

---

## 5. Regenerating

```bash
cd cmcc_selection
python build_cmip7_lookup.py                   # append what is missing, in place
python build_cmip7_lookup.py --dry-run         # preview
python build_cmip7_lookup.py --true-gap-only   # skip the 64 derivable variables
```

**Idempotent, never destroys hand work:** existing cells are copied verbatim, the
inherited block keeps its original order (read from `--reference-dir`, the
cmip_reformatter clone), only variables absent from the table are appended, and a
re-run with nothing new rewrites the files identically. Needs no DR API.
