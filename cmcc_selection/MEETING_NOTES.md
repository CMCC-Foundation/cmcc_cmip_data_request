# CMIP7 variables — meeting cheat-sheet

Plain-language guide to what we produced and which few files to open.

## The story in one paragraph

CMCC picked a set of **opportunities** (High/Medium priority, from Tomas' table).
Each opportunity asks for **variable groups**; we expanded every group, using the
official **CMIP7 Data Request**, into the actual variables. That gives **853
variables that are in both the Data Request and the CMCC request** (we verified
every requested group was found — nothing dropped). Then we checked which of
those the **model can actually produce**, using the `cmip_reformatter` name tables.

## The numbers

| category | count | meaning |
|---|---|---|
| **mapped** | **436** | in the request AND the model produces it (has a raw model name) → ready |
| **derivable** | **67** | not produced directly, but a slice/average of a field we already save (e.g. `thetao200` from `thetao`) → free, no action |
| **true gap** | **350** | requested, present in the Data Request, but **no model output** for it today |
| **total requested** | **853** | |

Storage (per model-year, uncompressed): **~213 GB** for what we produce today
(≈ 2× CMIP6), **+224 GB** if all true-gaps were added, ~437 GB total. Most of the
true-gap cost is **ocean 3-hourly** fields.

> **"true gap" does NOT mean "missing from our list".** Every requested variable
> is present. True gap = "no current model→CMOR name". Two sub-cases:
> - the model *does* output the field but the reformatter lacks the line
>   (e.g. `snw` → CLM `H2OSNO`) → **quick add**;
> - the model genuinely doesn't output it (e.g. `bigthetao` = conservative
>   temperature; the model writes potential temperature `thetao`) → **derive / enable / drop**.

## The 3 files to open (in `out/`)

1. **`truegap_by_opportunity.csv`** — *the meeting table.*
   One row per **Division + opportunity**, listing the **true-gap variable names**
   it pulls in. Answers "which Division asked for which un-producible variables".
   Columns: `division | opportunity | cmcc_priority | n_true_gap | groups_with_true_gap | true_gap_variables`.

2. **`truegap_provenance.csv`** — same, but broken down **per variable group**
   inside each opportunity (finer detail for whoever owns a group).
   Columns: `division | opportunity | cmcc_priority | group | n_true_gap | true_gap_variables`.

3. **`cmcc_variables_mapped.csv`** — *the master list* (all 853 variables).
   For each variable: DR name, raw model name, `map_category`
   (mapped / derivable / true_gap), realm, frequency, and GB/year.
   Use it to look up any single variable.

## Where the true gaps get fixed: `cmip7-lookup/`

The gaps are not only *reported*, they have a **worksheet**. `cmip7-lookup/`
holds one CMOR→raw table per model component (`atm`, `ice`, `lnd`, `ocn`,
`ocnbgc`), in the same 4-column format the reformatter already uses. Each table
is the original list of variables we produce, **plus** every requested variable
with no raw name appended at the end with an **empty `model`** column:

```
variable,reprocess,model,long_name
zg7h,True,"Z3, PS, T",Geopotential Height     <- end of the original block
abs550bc,False,,black carbon aaod@550nm       <- appended: model to fill
snw,False,,Surface Snow Amount
```

Write the raw model name in `model` (`snw` → `H2OSNO`) and the variable becomes
producible on the next `map_to_raw_names.py` run; leave it empty for the ones to
drop and note the decision in `out/raw/unmapped.csv`. 759 rows: **373 already
mapped, 386 to fill** (322 true gaps + 64 derivable). Which realm, which
Division, how many GB: `out/raw/unmapped.csv` and `out/truegap_*.csv`. Details:
[`../cmip7-lookup/README.md`](../cmip7-lookup/README.md).

## The final "production" table (the shape Tomas asked for)

`out/production/<realm>.csv` — **one CSV per model realm**, three columns exactly
like Tomas' example:

| frequency | time_ave_or_inst | variables |
|---|---|---|
| 6hr | ave | RELHUM, PS, T |

The `variables` column holds the **raw model names** the model must output for that
realm at that frequency/statistic. This is the hand-off table for whoever
configures the model output.

**Two related tables and how they differ:**
- `out/by_realm/<realm>.csv` — the **Data-Request view**: variables in their
  CMIP7/DR names (what was *requested*).
- `out/raw/by_realm/<realm>.csv` — the **detailed model view**: DR names + raw
  model names + the split of what's missing (`derivable` vs `true_gap`) + GB/year.
  `production/` is just its `variables_raw` column, cleaned up.

## What weighs the most (size drivers)

Cost per variable = `horizontal points × vertical levels × timesteps/year × 4 B`.
On the CMCC-ESM3 grid, a **single variable** costs roughly (uncompressed):

| field type | monthly | daily | 3-hourly |
|---|---|---|---|
| **3-D ocean** (360×291×75) | 0.38 GB | 11.5 GB | **92 GB** |
| **3-D atmos** (48600×58) | 0.14 GB | 4.1 GB | 33 GB |
| 2-D ocean | 0.005 GB | 0.15 GB | 1.2 GB |
| 2-D atmos | 0.002 GB | 0.07 GB | 0.6 GB |

So **frequency and 3-D matter enormously**: one 3-hourly 3-D ocean field ≈ 92 GB/yr
— by itself almost a whole CMIP6 model-year. That is why the true-gap cost (224 GB)
is dominated by a handful of **ocean sub-daily 3-D** fields. See the biggest
individual variables with:
```bash
head -12 out/volume_by_variable.csv     # sorted largest-first
```

(The `raw/by_realm/*.csv` files carry the same info plus the GB columns.)

## Don't read the CSV in the terminal — make a readable summary

The clearest view is the printed summary of the provenance script. Save it to a
text file and open THAT (it's a Division → opportunity → group → variable-names tree):

```bash
cd /users_home/cmcc/gc02720/dr_cmip7/cmcc_selection
python truegap_provenance.py > truegap_summary.txt 2>/dev/null
less truegap_summary.txt          # or open it in an editor
```

`truegap_summary.txt` reads like:

```
### ESYDA   (200 distinct true_gap variables)
  [high  ] Baseline Climate Variables for Earth System Modelling
        baseline_fixed        2   mrsofc, rootd
        baseline_monthly      3   bigthetao, rluscs, snw
  ...
```

i.e. for each **Division**, each **opportunity** it owns, each **group**, and the
exact **true-gap variable names** — which is precisely the "who asked for what,
and what's the gap" view for the discussion.

## The 5 Baseline true-gap variables (spelled out)

Baseline groups are split by **output frequency** (see next section). The 5
baseline variables flagged true-gap are:

| group | variable | full name | likely status |
|---|---|---|---|
| baseline_fixed | `mrsofc` | Capacity of Soil to Store Water (field capacity) | maybe addable (CLM soil params) |
| baseline_fixed | `rootd` | Maximum Root Depth | maybe addable (CLM) |
| baseline_monthly | `bigthetao` | Sea Water **Conservative** Temperature (TEOS-10) | real gap — model writes `thetao` (potential) |
| baseline_monthly | `rluscs` | Surface Upwelling **Clear-Sky** Longwave Radiation | maybe derivable (CAM clear-sky fluxes) |
| baseline_monthly | `snw` | Surface Snow Amount (snow water equivalent) | quick add — CLM `H2OSNO` exists |

So of the 5, only `bigthetao` is a genuine "model doesn't produce it" case; the
others are likely a reformatter line or a simple derivation. **None is missing
from the request** — all 131 baseline variables are present.

### What "fixed" and "monthly" mean

The baseline opportunity lists the *same* physical variables at several **output
frequencies**, one group per frequency:

- **`baseline_fixed`** → **time-invariant** fields, written **once** for the whole
  run (they never change in time): grid geometry, land fraction, soil field
  capacity (`mrsofc`), root depth (`rootd`). Storage cost ≈ nil.
- **`baseline_monthly`** → **monthly** values (one per month, 12/year) — usually
  monthly means.
- (`baseline_daily` → daily; `baseline_subdaily` → 6-hourly/3-hourly.)

Same variable can appear in more than one of these (e.g. `tas` monthly *and*
daily) — those are distinct entries, not duplicates.

## Talking points

- Everything CMCC requested is present in the Data Request (coverage verified).
- 436 ready now; 67 come for free (derivable).
- 350 true-gaps need a per-Division decision: **add a reformatter line** (if the
  model already outputs it), **derive**, **enable a model diagnostic**, or **drop**.
- Biggest gaps by Division: **ESYDA** (carbon/BGC, ocean, fire, sea-ice),
  then **ICR / ESYDA-ICR** (hydrology, agriculture), **CLIVAP** (dynamics: EP-flux
  / Eulerian-mean diagnostics, downscaling), **EIEE** (energy/health impacts).
- Aerosol & atmospheric-chemistry variables are almost entirely true-gap (the
  model config doesn't output them) — a clear drop-or-scope decision.
