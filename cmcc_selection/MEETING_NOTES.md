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

(The `raw/by_realm/*.csv` files are the per-realm production lists — useful later,
not needed for this meeting.)

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
