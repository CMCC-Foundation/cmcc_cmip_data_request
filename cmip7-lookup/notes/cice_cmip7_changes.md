# CICE 6.3.0 (CMCC-ESM3): CMIP7 sea-ice output

This document describes the changes made to CICE 6.3.0 for the CMIP7 sea-ice output, compared
with the original code, and what the post-processing and CMORization have to do with the output.

## Contents

- [Rationale](#rationale)
- [Deliverables](#deliverables)
- [1. Summary](#1-summary)
- [2. New history fields](#2-new-history-fields)
- [3. Changes to existing history fields](#3-changes-to-existing-history-fields)
  - [3.1 Renamed fields](#31-renamed-fields-netcdf-name-and-namelist-flag)
  - [3.2 Definitions](#32-definitions)
- [4. Other code changes](#4-other-code-changes)
  - [4.1 Reset of `evaps` and `evapi`](#41-reset-of-evaps-and-evapi-ice_fluxf90)
  - [4.2 Snow tendency from dynamics](#42-snow-tendency-from-dynamics-ice_fluxf90-ice_step_modf90-nuopccmeps-cice_runmodf90)
  - [4.3 History infrastructure](#43-history-infrastructure-ice_history_sharedf90-ice_historyf90-ice_history_mechredf90)
  - [4.4 Several time samples per history file (`hist_mfilt`)](#44-several-time-samples-per-history-file-hist_mfilt)
  - [4.5 Unchanged](#45-unchanged)
  - [4.6 Modified files](#46-modified-files)
- [5. CESM infrastructure](#5-cesm-infrastructure)
- [6. Output namelist for the CMIP7 experiments](#6-output-namelist-for-the-cmip7-experiments)
- [7. Post-processing and CMORization](#7-post-processing-and-cmorization)
  - [7.1 General rules](#71-general-rules)
  - [7.2 Variable by variable](#72-variable-by-variable)
    - [State](#state)
    - [Thickness categories](#thickness-categories)
    - [Melt ponds and ridges](#melt-ponds-and-ridges)
    - [Ice area and mass tendencies](#ice-area-and-mass-tendencies)
    - [Snow tendencies and precipitation](#snow-tendencies-and-precipitation)
    - [Radiation and heat fluxes](#radiation-and-heat-fluxes)
    - [Fresh water and salt](#fresh-water-and-salt)
  - [7.3 Variables computed offline](#73-variables-computed-offline-not-written-by-cice)
  - [7.4 Variables from other components, or not available](#74-variables-from-other-components-or-not-available)
  - [7.5 Summary of the changes for the post-processing](#75-summary-of-the-changes-for-the-post-processing)
  - [7.6 Reconstruction of the original fields](#76-reconstruction-of-the-original-fields-offline)
- [8. Differences from CICE 6.6.3](#8-differences-from-cice-663)
- [9. Limitations and known behaviours](#9-limitations-and-known-behaviours)
- [10. Verification](#10-verification)
  - [10.1 Test script](#101-test-script)
  - [10.2 Runs](#102-runs)

## Rationale

- **Original code:** CICE 6.3.0, `CMCC-Foundation/CICE` branch `cmcc-esm3` (Icepack included,
  CESM `cime_config`, nuopc/cmeps driver).
- **Reference** for names and conventions: CICE Consortium `main`, CICE 6.6.3 (commit 928e388).
  Where 6.6.3 does not follow the CMIP7 Data Request (DR), the DR is followed (section 8).
- **Configuration** (esm-piControl `ice_in`): `ktherm = 2` (mushy), `kdyn = 1` (EVP),
  `ndtd = 1`, `tr_pond_lvl`, `tr_lvl`, `tr_iage`, `tr_FY`, `tr_aero` (`n_aero = 3`),
  `shortwave = dEdd`, `snwredist = none`, `tr_snow = .false.`, sea-ice BGC off,
  `update_ocn_f = .true.`, `formdrag = .false.`, `kcatbound = 0`, 5 categories, 8 ice and 3 snow
  layers, grid tn1v4 (360 x 291), ice time step 1800 s.
- **Requests:** sea-ice related variables of the selected variable groups
  (`CMIP7-DR-opportunities-Final.csv`): 93 requests (9 Core, 56 High, 28 Medium; 75 monthly,
  16 daily, 2 three-hourly), 73 distinct variables.
- **Verification:** coupled runs on cmcc-esm3 checked with the test script (section 10).

## Deliverables

| File | Content |
|---|---|
| `cice_cmip7_changes.md` | this document |
| `ice_lookup.csv` | the lookup for the post-processing: same columns as the original (`variable`, `reprocess`, `model`, `long_name`, `cmip6_name`, `notes`), one row per CMIP7 variable (73); the notes summarise section 7.2 |
| `cice_cmip7.tar.gz` | the code, the namelists and the scripts (below) |

Content of `cice_cmip7.tar.gz`:

| Path in the tar | Content |
|---|---|
| `cice/` | the modified files, with their path in the CICE repository (list in section 4.6): copy them over the `cmcc-esm3` tree |
| `namelists/user_nl_cice_cmip7_coupled.txt` | output namelist for the coupled CMIP7 experiments (section 6) |
| `namelists/user_nl_cice_cmip7_test.txt` | the same fields with short files, plus the reference fields used by the test script |
| `namelists/user_nl_cice_full_test.txt` | every history field available in the configuration, monthly and daily, for a complete test |
| `scripts/test_cice_cmip7_output.py` | checks of the history output of a run (section 10) |
| `scripts/check_user_nl_cice.py` | checks a `user_nl_cice` against the Fortran namelists, the XML and the mapping |
| `tables/cice_cmip7_mapping.csv` | one row per CMIP7 request (variable and frequency): CICE fields, formula, status, priority per experiment group; input of `check_user_nl_cice.py --mapping` |

## 1. Summary

- 5 new history fields (`sisndmassdyn`, `sisndmasssi`, `sisali`, `sisaltmass`, `siitdsnconc`).
- 7 CMIP fields renamed to the CICE 6.6.3 / DR names.
- About 25 CMIP fields with corrected definitions: signs, units, normalisation, missing terms when
  the ice disappears from a cell within a step.
- Two standard fields corrected (`fsurf_ai`, `fcondtop_ai`) and one CICE 6.3 bug fixed outside the
  history (`evaps`, `evapi` never reset).
- Several time samples per history file (`hist_mfilt`), with files kept open as in CAM.
- CESM XML entries for all the CMIP flags and for `hist_mfilt`.
- No change to the model physics, to Icepack, or to drivers other than nuopc/cmeps.

## 2. New history fields

| Field (flag `f_<name>`) | Definition (accumulated at every step) | Normalisation | Units | DR variable |
|---|---|---|---|---|
| `sisndmassdyn` | `rhos * dvsdtd`; `dvsdtd` = snow volume change in the dynamics (transport and ridging), computed as `dvidtd` | grid-cell mean | kg m-2 s-1 | sisndmassdyn (High) |
| `sisndmasssi` | `-snoice * rho / dt`, `rho = rhos` with `ktherm = 2` (snow thickness lost = snow-ice thickness formed), `rhoi` with `ktherm = 1` | grid-cell mean | kg m-2 s-1 | sisndmasssi (High) |
| `sisali` | `aice * sum_k(S_k) / nilyr` where `aice > puny` | divided by the time sum of `aice` | ppt | sisali (Medium) |
| `sisaltmass` | `rhoi * 1e-3 * sum_k(S_k) * vice / nilyr` | grid-cell mean | kg m-2 | sisaltmass (Medium) |
| `siitdsnconc` | `aicen * snowfracn` where `aicen > puny`, per category | grid-cell mean, x 100 | % | siitdsnconc (Medium) |

`S_k` is the bulk salinity tracer of layer k (prognostic with `ktherm = 2`).

## 3. Changes to existing history fields

### 3.1 Renamed fields (netCDF name and namelist flag)

| Original | New (= CICE 6.6.3) | DR variable |
|---|---|---|
| `sidmasssi` | `sidmassgrowthsi` | sidmassgrowthsi |
| `sidmasslat` | `sidmassmeltlat` | sidmassmeltlat |
| `sndmassubl` (flag `f_sndmasssubl`) | `sisndmasssubl` | sbl |
| `sndmasssnf` | `sisndmasssnf` | prsn |
| `sndmassmelt` | `sisndmassmelt` | snm |
| `sifllatstop` | `sifllattop` | sifllattop |
| `siflsensupbot` | `siflsensbot` (new definition, 3.2) | siflsensbot |

The original names no longer exist: a namelist that sets them fails at namelist read. How to
reconstruct the original fields offline: section 7.6.

### 3.2 Definitions

"Per ice area": time sum divided by the time sum of `aice`, fill value where it is 0.
"Grid-cell": time mean per grid-cell area.

| Field | Original code | Modified code | Reason |
|---|---|---|---|
| `sidmassth`, `sidmassdyn`, `sidconcth`, `sidconcdyn`, `sidmassgrowthbot`, `sidmassgrowthsi`, `sidmassmelttop`, `sidmassmeltbot`, `sidmassmeltlat`, `sidmassevapsubl`, `sisndmassmelt`, `sisndmasssubl`, `sisndmasssnf` | accumulated only where `aice > puny` at the end of the step | accumulated everywhere | the steps in which the ice of a cell melts or is exported completely were lost, and the budget did not close |
| `sidmassgrowthwat` | only where `aice_init > puny` | everywhere | frazil formed in ice-free cells was lost |
| `sidmassmelttop`, `sidmassmeltbot`, `sidmassmeltlat` | `+melt * rhoi / dt` | `-melt * rhoi / dt` | DR: always negative or zero |
| `sisndmassmelt` | `+melts * rhos / dt` | `-melts * rhos / dt` | as above |
| `sidmassevapsubl` | `evapi * rhoi` | `evapi` | `evapi` is already kg m-2 s-1 (values were 917 times too large) |
| `sisndmasssubl` | `evaps * rhos` | `evaps` | as above (330 times) |
| `sisndmasssnf` | `aice * fsnow * rhos` | `aice_init * fsnow` | `fsnow` is already kg m-2 s-1; `aice_init`, the ice area when the flux is applied, as for `snow_ai` |
| `sipr` | `aice * frain`, per ice area | `aice_init * frain`, grid-cell, when melt ponds are on; zero otherwise | DR: rain onto the ice per grid-cell area; with ponds the rain enters the ponds (`icepack_meltpond_lvl`), without ponds it goes directly to the ocean |
| `sifllwutop` | `aice * flwout` (negative) | `-aice * flwout` | DR `rlus` positive upward |
| `siflsensbot` | `aice * fhocn` | `aice * fbot`, per ice area | `fhocn` is the net ice-to-ocean heat flux (meltwater enthalpy and residual energy); the DR asks for the sensible heat flux, which is `fbot` (positive down, negative when the ocean heats the ice) |
| `siflcondtop` | `aice * fcondtop` | `fcondtop` where `aice > puny`, per ice area | `fcondtop` is already a grid-cell mean (`merge_fluxes` adds `fcondtopn * aicen_init`, and no driver passes it to `scale_fluxes`): it was weighted by the ice area twice. Now as `sifllattop` and `siflsenstop` |
| `siflfwdrain` | `aice * (frain + melts + meltt)` | `(rhoi * meltt + rhos * melts) / dt`, per ice area | the original added kg m-2 s-1 to metres per step; rain removed (DR: surface melt and pond drainage). Water stored in the ponds is not removed (section 9) |
| `siflfwbot`, `siflsaltbot` | frazil term `dfresh`/`dfsalt` undefined with `update_ocn_f = .true.`; frazil multiplied by `aice` | frazil term 0 with `update_ocn_f = .true.` (frazil already in `fresh`, `fsalt`), otherwise added as a grid-cell flux | undefined value in this configuration |
| `sitempsnic` | `aice * (Tsnice / aice_init + 273.15)` | `aice * (Tsnice + 273.15)` where `aice > puny` (`Tsfc` where there is no snow), per ice area | `Tsnice` is a cell value in deg C (Icepack `thermo_vertical`), not a sum weighted by `aicen_init`: the division gave values down to -1e11 K where `aice_init` is small |
| `sitempbot` | `aice * (Tbot / aice_init + 273.15)` | `aice * (Tbot + 273.15)` where `aice > puny`, per ice area | as above (`Tbot` from `frzmlt_bottom_lateral`) |
| `sirdgthick` | time mean of `vrdg / ardg`, divided by the mean `aice` | time sum of `vice * (1 - vlvl)` / time sum of `ardg`; fill value where `ardg` = 0 | the original was overestimated by about 1/aice |
| `siitdconc` | fraction | % | DR units (as 6.6.3) |
| `siitdthick` | 0 where the category is never present | fill value there | DR: undefined where there is no ice in the category |
| `siitdsnthick` | snow volume / category ice area | snow volume / snow-covered category area (`siitdsnconc`); fill value where there is no snow | DR: actual snow thickness |
| `snowfracn` | accumulated twice per step | once | written value was twice the mean |
| `hpond_ai` (`ice_history_pond.F90`) | output frequency taken from `f_hpond` | from `f_hpond_ai` | not written when `f_hpond` was off |
| `fsurf_ai`, `fcondtop_ai` (standard fields) | `fsurf * aice_init`, `fcondtop * aice_init` | `fsurf`, `fcondtop` | already grid-cell means (as `siflcondtop`); now equal to the sums over the categories of `fsurfn_ai`, `fcondtopn_ai` |

Long names and comments of the changed fields were updated (sign convention, definition).

## 4. Other code changes

### 4.1 Reset of `evaps` and `evapi` (`ice_flux.F90`)

`init_flux_atm` now sets `evaps` and `evapi` to zero at every time step, as `evap` (as in CICE
6.6.3). Icepack adds the category fluxes to them at every step (`merge_fluxes`); in the original
code they were set to zero only at initialisation, so they were cumulative sums since the start of
the job. They are used only by the history (`sidmassevapsubl`, `sisndmasssubl`).

### 4.2 Snow tendency from dynamics (`ice_flux.F90`, `ice_step_mod.F90`, nuopc/cmeps `CICE_RunMod.F90`)

- New array `dvsdtd` in `ice_flux`, set to `vsno` in `init_history_dyn`.
- `update_state` has a new optional argument `dvsdt`: `(vsno - dvsdt) / dt` after the dynamics,
  as `dvidt` for the ice volume.
- The nuopc/cmeps driver passes `dvsdt = dvsdtd` after the dynamics. The other drivers are not
  modified and still compile (the argument is optional); with them `sisndmassdyn` would be wrong,
  so keep `f_sisndmassdyn = 'x'` there. As `dvidtd`, the tendency is exact only with `ndtd = 1`.

### 4.3 History infrastructure (`ice_history_shared.F90`, `ice_history.F90`, `ice_history_mechred.F90`)

- **Normalisation fields always written.** New helper `hist_stream_union(fdst, fsrc)`, which adds
  to a flag the output frequencies of another flag. `init_hist` uses it so that the fields needed
  for a normalisation are written on the same streams as the fields that need them: `aice` for
  every field averaged over the ice area, `aicen` for `siitdthick`, `siitdsnconc` for
  `siitdsnthick`; `init_hist_mechred` does the same for `ardg` and `sirdgthick`. In the original
  code a missing `aice` gave stale normalisations without warning.
- **New normalisation factors:** `ravgir` (1 / time sum of `ardg`, for `sirdgthick`) and
  `ravgipsn` (1 / time sum of `siitdsnconc` per category, for `siitdsnthick`). `n_ardg` is public
  in `ice_history_mechred`.
- **Guards:** `f_siage` is set to `'x'` when `tr_iage = .false.`, `f_sirdgthick` when
  `tr_lvl = .false.`.
- **`f_cmip`** (switch that turns on all the CMIP fields) includes the new fields; with `'d'` in
  the second position it also writes daily `siflswdtop`, `siflswutop`, `siage`, `sisnhc`,
  `sitempsnic`, `siitdsnconc`, `siitdsnthick`, `aicen`. It must be `'xxxxx'` when the flags are
  set one by one, because it overwrites them.
- **Field name length:** `vname` in the history field type is 24 characters instead of 16, as in
  CICE 6.6. On every stream after the first, CICE appends `_<histfreq>` to the field names
  (`aice_d`); with 16 characters, names of 15 and 16 characters were cut (`sidmassevapsubl_`,
  `sidmassgrowthwat` without suffix).

### 4.4 Several time samples per history file (`hist_mfilt`)

- New namelist array `hist_mfilt(5)` in `setup_nml` (`ice_init.F90`): number of time samples per
  history file for each stream. Default 1 (one file per output time, as in the original code).
  Checked (>= 1), broadcast and printed in the log.
- PIO writer (`io_pio2/ice_history_write.F90`), with `hist_mfilt(ns) > 1`:
  - the first sample creates the file, defines it and writes the time-invariant fields;
  - the file and its PIO decompositions stay open, and each following sample is written as a new
    time record (`time`, `time_bounds`, all the fields);
  - between samples nothing forces a write to disk: PIO keeps the data in its buffers, as in CAM;
  - the file is closed (after `pio_syncfile`) when it holds `hist_mfilt` records, or at the end of
    the run by the new subroutine `ice_close_hist_files`, called in `ModelFinalize` of the
    nuopc/cmeps cap (`ice_comp_nuopc.F90`);
  - a new job always starts a new file, named with the date of its first sample (file naming
    unchanged). With jobs of whole years starting on 1 January and `hist_mfilt = 12, 365`, there
    is one file per year per stream; a job ending during the year leaves a shorter file;
  - initial-condition files (`write_ic`) keep one record per file;
  - the global attributes with the model date (`comment2`, `comment3`) refer to the first record.
- `io_netcdf` and `io_binary` writers: abort with a message if `hist_mfilt > 1`; empty
  `ice_close_hist_files`.
- Limitations: if a job dies before its end (abort, wall-clock limit), the records still in the
  buffers are lost and the open file can be unreadable (as in CAM). Use `hist_mfilt > 1` only
  with the nuopc/cmeps driver, which closes the files, and in CESM builds (`CESMCOUPLED`): without
  it `ice_pio.F90` calls `pio_init` at every new file.

### 4.5 Unchanged

Physics, Icepack, restart files, coupling fields, the drivers other than nuopc/cmeps
(nuopc/dmi, mct, direct, standalone), `buildnml` and `buildlib`.

### 4.6 Modified files

| File | Changes |
|---|---|
| `cime_config/namelist_definition_cice.xml` | section 5 |
| `src/cicecore/cicedynB/analysis/ice_history.F90` | sections 2, 3, 4.3 |
| `src/cicecore/cicedynB/analysis/ice_history_shared.F90` | new flags and indices, `hist_mfilt`, `hist_stream_union`, `vname` length |
| `src/cicecore/cicedynB/analysis/ice_history_mechred.F90` | `ardg` on the streams of `sirdgthick`, public `n_ardg` |
| `src/cicecore/cicedynB/analysis/ice_history_pond.F90` | `hpond_ai` flag |
| `src/cicecore/cicedynB/general/ice_flux.F90` | `dvsdtd`; reset of `evaps`, `evapi` |
| `src/cicecore/cicedynB/general/ice_init.F90` | `hist_mfilt` |
| `src/cicecore/cicedynB/general/ice_step_mod.F90` | optional `dvsdt` in `update_state` |
| `src/cicecore/cicedynB/infrastructure/io/io_pio2/ice_history_write.F90` | files kept open, `ice_close_hist_files` |
| `src/cicecore/cicedynB/infrastructure/io/io_netcdf/ice_history_write.F90` | abort if `hist_mfilt > 1`, empty `ice_close_hist_files` |
| `src/cicecore/cicedynB/infrastructure/io/io_binary/ice_history_write.F90` | as above |
| `src/cicecore/drivers/nuopc/cmeps/CICE_RunMod.F90` | `dvsdt = dvsdtd` after the dynamics |
| `src/cicecore/drivers/nuopc/cmeps/ice_comp_nuopc.F90` | `ice_close_hist_files` in `ModelFinalize` |

## 5. CESM infrastructure

`cime_config/namelist_definition_cice.xml` (the only CESM file changed; `buildnml` is unchanged):

- `hist_mfilt`: `integer(5)`, group `setup_nml`, default `1,1,1,1,1`.
- One entry (`char`, category `history`, group `icefields_nml`, default `'xxxxx'`) for each of the
  67 `f_si*` flags of the Fortran namelist (renamed and new flags included). These flags exist in
  `icefields_nml` but were not in the XML, so `buildnml` rejected them in `user_nl_cice`. With
  default `'xxxxx'` nothing is written unless the flag is set in `user_nl_cice`.
- Entries for 10 other flags of `icefields_nml` that were missing (`f_atmspd`, `f_atmdir`,
  `f_ocnspd`, `f_ocndir`, `f_fbot`, `f_taubx`, `f_tauby`, `f_sigp`, `f_dagedtt`, `f_dagedtd`),
  with default `'mxxxx'`, the default of the Fortran code (runs that do not set them are
  unchanged).
- Entry ids are lower case (`f_sigp`): the `user_nl_cice` parser converts the names to lower
  case, and the comparison with the XML ids is case-sensitive in the CIME version in use.

Rules for `user_nl_cice` (CIME parser): comments only on their own lines, not after a value
(`expected literal value, but got '!'`).

## 6. Output namelist for the CMIP7 experiments

The namelist below (`namelists/user_nl_cice_cmip7_coupled.txt`) writes all the CICE fields needed
by the 93 requests (section 7), on two streams: monthly and daily means, one file per year each.
Each flag is commented with the CMIP7 variables it serves and their best priority; the lines
marked `[Medium only]` can be removed for a Core + High run. CESM defaults that would also go to
the daily stream are set to monthly only. `check_user_nl_cice.py` and the CIME parser report no
errors and no mapped variable left without its fields.

```
histfreq   = 'm','d','x','x','x'
histfreq_n =  1 , 1 , 1 , 1 , 1
! one file per year per stream (noleap calendar, jobs of whole years)
hist_mfilt = 12 ,365, 1 , 1 , 1
! must be off: with f_cmip on, init_hist resets every CMIP flag
! to 'mxxxx' (and f_aicen) after the namelist is read
f_cmip               = 'xxxxx'

! --- State: concentration, thickness, snow, temperature, age, salinity ---
! siarea/siarean NH H, siarea/siareas SH H, siconc C, siconc(d) C, siextent/siextentn NH H, siextent/siextents SH H, simpconc M, simpeffconc M, sirdgconc M, snc/sisnconc H
f_aice               = 'mdxxx'
! sitimefrac C, sitimefrac(d) H
f_icepresent         = 'mdxxx'
! sithick C, sithick(d) H
f_sithick            = 'mdxxx'
! sieqthick/sivol H, simass C, sivol/sivoln NH H, sivol/sivols SH H
f_hi                 = 'mxxxx'
! sisnmass/sisnmassn NH H, sisnmass/sisnmasss SH H, snd/sisnthick C, snd/sisnthick(d) H, snw/sisnmass H
f_hs                 = 'mdxxx'
! snc/sisnconc H, snd/sisnthick C, snd/sisnthick(d) H
f_snowfrac           = 'mdxxx'
! ts/sitemptop C, ts/sitemptop(d) H
f_sitemptop          = 'mdxxx'
! [Medium only] sitempsnic M, sitempsnic(d) M
f_sitempsnic         = 'mdxxx'
! [Medium only] sitempbot M
f_sitempbot          = 'mxxxx'
! siage M, siage(d) H
f_siage              = 'mdxxx'
! [Medium only] sifb M
f_sifb               = 'mxxxx'
! sihc H
f_sihc               = 'mxxxx'
! sisnhc H, sisnhc(d) M
f_sisnhc             = 'mdxxx'
! [Medium only] sisali M
f_sisali             = 'mxxxx'
! [Medium only] sisaltmass M
f_sisaltmass         = 'mxxxx'

! --- Dynamics (B-grid velocities at U points) ---
! siu C, siu(d) H
f_siu                = 'mdxxx'
! siv C, siv(d) H
f_siv                = 'mdxxx'
! sispeed H, sispeed(d) H
f_sispeed            = 'mdxxx'

! --- Thickness categories ---
! normalisation of other fields only
f_aicen              = 'mxxxx'
! [Medium only] siitdconc M
f_siitdconc          = 'mxxxx'
! [Medium only] siitdthick M
f_siitdthick         = 'mxxxx'
! [Medium only] siitdsnconc M, siitdsnconc(d) M
f_siitdsnconc        = 'mdxxx'
! [Medium only] siitdsnthick M, siitdsnthick(d) M
f_siitdsnthick       = 'mdxxx'

! --- Melt ponds (level-ice ponds) and ridges ---
! [Medium only] simpconc M, simprefrozen M, simpthick M
f_apond_ai           = 'mxxxx'
! [Medium only] simpeffconc M
f_apeff_ai           = 'mxxxx'
! [Medium only] simpthick M
f_hpond_ai           = 'mxxxx'
! [Medium only] simprefrozen M
f_ipond_ai           = 'mxxxx'
! [Medium only] sirdgconc M
f_ardg               = 'mxxxx'
! [Medium only] sithick/sirdgthick M
f_sirdgthick         = 'mxxxx'

! --- Energy fluxes over and under sea ice (per ice area) ---
! rsds/siflswdtop H, rsds/siflswdtop(d) H
f_siflswdtop         = 'mdxxx'
! rsus/siflswutop H, rsus/siflswutop(d) H
f_siflswutop         = 'mdxxx'
! rlds/sifllwdtop H
f_sifllwdtop         = 'mxxxx'
! rlus/sifllwutop H
f_sifllwutop         = 'mxxxx'
! siflsenstop H
f_siflsenstop        = 'mxxxx'
! sifllattop H
f_sifllattop         = 'mxxxx'
! siflcondtop H
f_siflcondtop        = 'mxxxx'
! siflcondbot H
f_siflcondbot        = 'mxxxx'
! siflswdbot H
f_siflswdbot         = 'mxxxx'
! siflsensbot H
f_siflsensbot        = 'mxxxx'

! --- Ice mass and area budget (per grid-cell area) ---
! sidmassth H
f_sidmassth          = 'mxxxx'
! sidmassdyn H
f_sidmassdyn         = 'mxxxx'
! sidconcth H
f_sidconcth          = 'mxxxx'
! sidconcdyn H
f_sidconcdyn         = 'mxxxx'
! sidmassgrowthwat H
f_sidmassgrowthwat   = 'mxxxx'
! sidmassgrowthbot H
f_sidmassgrowthbot   = 'mxxxx'
! sidmassgrowthsi H
f_sidmassgrowthsi    = 'mxxxx'
! sidmassmelttop H
f_sidmassmelttop     = 'mxxxx'
! sidmassmeltbot H
f_sidmassmeltbot     = 'mxxxx'
! sidmassmeltlat H
f_sidmassmeltlat     = 'mxxxx'
! evspsbl/sidmassevapsubl H
f_sidmassevapsubl    = 'mxxxx'
! prra/sipr H
f_sipr               = 'mxxxx'

! --- Snow mass budget (per grid-cell area) ---
! prsn/sisndmasssnf H
f_sisndmasssnf       = 'mxxxx'
! snm/sisndmassmelt H
f_sisndmassmelt      = 'mxxxx'
! sbl/sisndmasssubl H
f_sisndmasssubl      = 'mxxxx'
! sisndmasssi H
f_sisndmasssi        = 'mxxxx'
! sisndmassdyn H
f_sisndmassdyn       = 'mxxxx'

! --- Fresh water and salt between ice and ocean (per ice area) ---
! [Medium only] siflfwbot M
f_siflfwbot          = 'mxxxx'
! [Medium only] sfdsi/siflsaltbot M
f_siflsaltbot        = 'mxxxx'
! [Medium only] siflfwdrain M
f_siflfwdrain        = 'mxxxx'

! --- CESM defaults written in other streams: kept monthly only ---
! CESM default 'mdxxx': monthly only
f_congel             = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_daidtd             = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_daidtt             = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_dvidtd             = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_dvidtt             = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_frazil             = 'mxxxx'
! CESM default 'mdhxx': monthly only
f_fswabs             = 'mxxxx'
! CESM default 'mdhxx': monthly only
f_fswdn              = 'mxxxx'
! CESM default 'mdhxx': monthly only
f_fswthru            = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_meltb              = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_meltl              = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_melts              = 'mxxxx'
! CESM default 'mdxxx': monthly only
f_meltt              = 'mxxxx'
! CESM default 'mdhxx': monthly only
f_vicen              = 'mxxxx'
! CESM default 'mdhxx': monthly only
f_vsnon              = 'mxxxx'

! --- Optional: 3-hourly sfdsi (ocean.sfdsi 3hr, High) from CICE instead of the ocean model.
!     To use it, replace the three lines above with
! histfreq   = 'm','d','h','x','x'
! histfreq_n =  1 , 1 , 3 , 1 , 1
! hist_mfilt = 12 ,365,2920, 1 , 1
! and set f_fsalt_ai = 'mxhxx' (monthly as above + 3-hourly)
```

Test namelists (same fields): `user_nl_cice_cmip7_test.txt` with `hist_mfilt = 2, 10` (several
files within a job) and the reference fields used by the test script; `user_nl_cice_full_test.txt`
with every history field of the configuration (219 flags, 234 fields per stream, about 11 GB for
1 + 1 month).

Optional 3-hourly stream for `ocean.sfdsi` 3hr from CICE, if not taken from the ocean model
(section 7.4): `histfreq = 'm','d','h','x','x'`, `histfreq_n = 1,1,3,1,1`,
`hist_mfilt = 12,365,2920,1,1`, `f_fsalt_ai = 'mxhxx'`.

## 7. Post-processing and CMORization

### 7.1 General rules

- **Files.** Monthly stream `case.cice.h.YYYY-MM.nc` (12 records per file with
  `hist_mfilt = 12`), daily stream `case.cice.h.YYYY-MM-DD.nc` (365 records). The streams have
  the same base name: tell them apart by the date format or by the length of `time_bounds`.
  A job that does not end on 31 December leaves a shorter file.
- **Daily names.** On the daily stream (second stream) every field name has the suffix `_d`
  (`aice_d`, `sithick_d`, `siitdsnconc_d`, ...). The lookup gives the base name.
- **Time.** `time` is the end of the averaging period (days since the reference date of the
  file); use `time_bounds` for the CMOR time bounds (and their midpoint as time, if required).
- **Fill value.** 1e30 (`_FillValue` and `missing_value`) over land and where a field is
  undefined (normalisation area zero).
- **Grid.** Native tripolar grid tn1v4 (360 x 291), T points (`TLON`, `TLAT`, `tarea`) except
  `siu`, `siv`, `sispeed` (U points: `ULON`, `ULAT`; `siu`/`siv` along the native grid
  directions, as the DR asks).
- **Thickness categories.** Dimension `nc` (ncat = 5). The variable `NCAT` holds the upper
  thickness bound of each category (`hin_max(1:ncat)`, `kcatbound = 0`); the lower bound of
  category 1 is 0 and of category n the upper bound of n-1. Use them for the CMOR `iceband`
  bounds (the last upper bound is a large number, not a physical limit).
- **Per-ice-area fields** (`sithick`, `siage`, `sifb`, `ts`, `sitemp*`, `siu`, `siv`, `sispeed`,
  `sisali`, the `rs*`, `rl*`, `sifl*` fluxes): written as time sum of `aice*x` divided by the
  time sum of `aice`, fill value where the time-mean `aice` is 0. This is the DR
  `area: time: mean where sea_ice` (mask siconc): no further masking needed. For the top
  fluxes the DR mask is `siconca` (atmosphere grid): the ocean-grid `aice` is used.
- **Grid-cell fields with DR mask=siconc** (`prsn`, `prra`, `sbl`, `snm`, `sisndmasssi`,
  `sisndmassdyn`, `sisnhc`, `siitdconc`): CICE writes 0 where there is no ice; set the fill
  value where the time-mean `aice` (same stream) is 0.
- **Grid-cell fields with `over all_area_types` or `where sea`** (`sidmass*`, `evspsbl`,
  `sieqthick`, `simass`, `snw`, `sisaltmass`, `sihc`, `sidconc*`, `sitimefrac`, `siconc`): copy
  as they are, zeros included.
- **Ratios** (`snd`, `snc`, `simp*`, `sirdgconc`): computed from the time means of the same
  record (ratio of means = ratio of time sums, the same convention used by CICE for `sithick`);
  fill value where the denominator is 0.
- **Units.** No conversion apart from the ones in the table; CICE writes some unit strings in
  another form (`W/m2`, `m/s`, `1/s`, `ppt`): use the DR units in the CMOR metadata
  (`W m-2`, `m s-1`, `s-1`, `1E-03`).
- **Output of the original code** has the errors listed in section 3.2 (signs, units,
  missing melt-out terms, wrong normalisations, `siflcondtop`, `sitempsnic`, `sitempbot`): it
  should not be CMORized with the rules below.

### 7.2 Variable by variable

Columns: CMIP7 variable (frequency, best priority over the selected groups); CICE field(s), as in
`ice_lookup.csv` (`model`); operation; sign; mask; change compared with the original
`ice_lookup.csv` and the output of the original code.


#### State

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.siconc.tavg-u-hxy-u` Sea-Ice Area Percentage (Ocean Grid) | day Core<br>mon Core | `aice*100` | 100 * aice | none | none (0 over open water) | as before |
| `seaIce.sitimefrac.tavg-u-hxy-sea` Fraction of Time Steps with Sea Ice | day High<br>mon Core | `ice_present` | copy | none | none | as before |
| `seaIce.sithick.tavg-u-hxy-si` Sea-Ice Thickness | day High<br>mon Core | `sithick` | copy | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.sieqthick.tavg-u-hxy-si` Sea-Ice Volume per Area | mon High | `hi` | copy (volume per grid-cell area) | none | none | as before |
| `seaIce.simass.tavg-u-hxy-si` Sea-Ice Mass | mon Core | `hi*917` | 917 * hi (rhoi, the density of the CICE mass diagnostics) | none | none | was `simass`, a field that does not exist in CICE 6.3 |
| `seaIce.snw.tavg-u-hxy-si` Snow Mass per Area | mon High | `hs*330` | 330 * hs (rhos) | none | none | was `sisnmass`, a field that does not exist in CICE 6.3 |
| `seaIce.snd.tavg-u-hxy-sn` Snow Thickness | day High<br>mon Core | `hs snowfrac` | hs / snowfrac | none | fill where snowfrac = 0 (DR: where snow) | as before |
| `seaIce.snc.tavg-u-hxy-si` Snow Area Percentage | mon High | `snowfrac aice` | 100 * snowfrac / aice | none | fill where aice = 0 | as before |
| `seaIce.siage.tavg-u-hxy-si` Age of Sea Ice
 | day High<br>mon Medium | `siage` | copy (s) | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.sifb.tavg-u-hxy-si` Sea-Ice Freeboard | mon Medium | `sifb` | copy | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.sihc.tavg-u-hxy-sea` Sea-Ice Heat Content | mon High | `sihc` | copy (J m-2, negative) | none | none | as before |
| `seaIce.sisnhc.tavg-u-hxy-si` Snow Heat Content | day Medium<br>mon High | `sisnhc` | copy (J m-2, negative) | none | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | as before |
| `seaIce.sisali.tavg-u-hxy-si` Sea-Ice Salinity | mon Medium | `sisali` | copy (ppt = 1E-03) | none | none: CICE writes the fill value where the time-mean `aice` = 0 | new field |
| `seaIce.sisaltmass.tavg-u-hxy-si` Mass of Salt in Sea Ice | mon Medium | `sisaltmass` | copy | none | none | new field |
| `seaIce.ts.tavg-u-hxy-si` Surface Temperature of Sea Ice | day High<br>mon Core | `sitemptop` | copy (K) | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.sitempsnic.tavg-u-hxy-si` Temperature at Snow-Ice Interface
 | day Medium<br>mon Medium | `sitempsnic` | copy (K); optionally clip at 273.15 K (about 0.1 % of the points exceed it by up to 0.5 K, transient melting snow) | none | none: CICE writes the fill value where the time-mean `aice` = 0 | values corrected (original code divided the cell value Tsnice by aice_init: down to -1e11 K) |
| `seaIce.sitempbot.tavg-u-hxy-si` Temperature at Ice-Ocean Interface | mon Medium | `sitempbot` | copy (K) | none | none: CICE writes the fill value where the time-mean `aice` = 0 | values corrected (original code divided the cell value Tbot by aice_init) |
| `seaIce.siu.tavg-u-hxy-si` X-Component of Sea-Ice Velocity | day High<br>mon Core | `siu` | copy; U points (ULON, ULAT), native grid directions | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.siv.tavg-u-hxy-si` Y-Component of Sea-Ice Velocity | day High<br>mon Core | `siv` | copy; U points (ULON, ULAT), native grid directions | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.sispeed.tavg-u-hxy-si` Sea-Ice Speed | day High<br>mon High | `sispeed` | copy; U points | none | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |

#### Thickness categories

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.siitdconc.tavg-u-hxy-si` Sea-Ice Area Percentages in Ice Thickness Categories | mon Medium | `siitdconc` | copy (%); category axis `nc`, bounds from `NCAT` | none | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | now in % (was a fraction): remove any factor 100 applied in the post-processing |
| `seaIce.siitdthick.tavg-u-hxy-si` Sea-Ice Thickness in Ice Thickness Categories | mon Medium | `siitdthick` | copy; category axis `nc` | none | none: CICE writes the fill value where the category is never present | fill value instead of 0 where the category is absent |
| `seaIce.siitdsnconc.tavg-u-hxy-si` Snow Area Percentages in Ice Thickness Categories | day Medium<br>mon Medium | `siitdsnconc` | copy (%); category axis `nc` | none | fill where siitdconc = 0 (DR mask=siitdconc) | new field (was `snowfracn`, a fraction of the category ice area) |
| `seaIce.siitdsnthick.tavg-u-hxy-si` Snow Thickness in Ice Thickness Categories
 | day Medium<br>mon Medium | `siitdsnthick` | copy; category axis `nc` | none | none: CICE writes the fill value where there is no snow in the category | now snow volume / snow-covered category area (was per category ice area) |

#### Melt ponds and ridges

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.simpconc.tavg-u-hxy-si` Fraction of Sea Ice Covered by Melt Pond | mon Medium | `apond_ai aice` | 100 * apond_ai / aice | none | fill where aice = 0 | as before |
| `seaIce.simpeffconc.tavg-u-hxy-si` Fraction of Sea Ice Covered by Effective Melt Pond | mon Medium | `apeff_ai aice` | 100 * apeff_ai / aice | none | fill where aice = 0 | as before |
| `seaIce.simpthick.tavg-u-hxy-simp` Melt Pond Depth | mon Medium | `hpond_ai apond_ai` | hpond_ai / apond_ai | none | fill where apond_ai = 0 (DR mask=simpconc) | fields were swapped with simprefrozen in the previous lookup; hpond_ai now written with its own flag |
| `seaIce.simprefrozen.tavg-u-hxy-simp` Thickness of Refrozen Ice on Melt Pond | mon Medium | `ipond_ai apond_ai` | ipond_ai / apond_ai | none | fill where apond_ai = 0 (DR mask=simpconc) | fields were swapped with simpthick in the previous lookup |
| `seaIce.sirdgconc.tavg-u-hxy-si` Fraction of Ridged Sea Ice | mon Medium | `ardg aice` | 100 * ardg / aice | none | fill where aice = 0 | was `sirdgconc`, a field that does not exist in CICE 6.3 |
| `seaIce.sithick.tavg-u-hxy-sir` Ridged Ice Thickness | mon Medium | `sirdgthick` | copy | none | none: CICE writes the fill value where ardg = 0 | now ridged volume / ridged area (was overestimated by about 1/aice) |

#### Ice area and mass tendencies

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.sidconcth.tavg-u-hxy-sea` Sea-Ice Area Fraction Tendency Due to Thermodynamics | mon High | `sidconcth` | copy (s-1) | none | none | now includes the steps where the ice disappears |
| `seaIce.sidconcdyn.tavg-u-hxy-sea` Sea-Ice Area Fraction Tendency Due to Dynamics | mon High | `sidconcdyn` | copy (s-1) | none | none | now includes the steps where the ice disappears |
| `seaIce.sidmassth.tavg-u-hxy-si` Sea-Ice Mass Change from Thermodynamics | mon High | `sidmassth` | copy | none | none | now includes the steps where the ice disappears |
| `seaIce.sidmassdyn.tavg-u-hxy-si` Sea-Ice Mass Change from Dynamics | mon High | `sidmassdyn` | copy | none | none | now includes the steps where the ice disappears |
| `seaIce.sidmassgrowthwat.tavg-u-hxy-si` Sea-Ice Mass Change Through Growth in Supercooled Open Water (Frazil) | mon High | `sidmassgrowthwat` | copy | none | none | now includes frazil in ice-free cells |
| `seaIce.sidmassgrowthbot.tavg-u-hxy-si` Sea-Ice Mass Change Through Basal Growth | mon High | `sidmassgrowthbot` | copy | none | none | as before (melt-out steps included) |
| `seaIce.sidmassgrowthsi.tavg-u-hxy-si` Sea-Ice Mass Change Through Snow-to-Ice Conversion | mon High | `sidmassgrowthsi` | copy | none | none | renamed (was `sidmasssi`) |
| `seaIce.sidmassmelttop.tavg-u-hxy-si` Sea-Ice Mass Change Through Surface Melting | mon High | `sidmassmelttop` | copy | none: now written <= 0 as the DR; remove any sign change in the post-processing | none | sign changed (was positive) |
| `seaIce.sidmassmeltbot.tavg-u-hxy-si` Sea-Ice Mass Change Through Bottom Melting | mon High | `sidmassmeltbot` | copy | none: now written <= 0 as the DR; remove any sign change in the post-processing | none | sign changed (was positive) |
| `seaIce.sidmassmeltlat.tavg-u-hxy-si` Sea-Ice Mass Change Through Lateral Melting | mon High | `sidmassmeltlat` | copy | none: now written <= 0 as the DR; remove any sign change in the post-processing | none | renamed (was `sidmasslat`), sign changed (was positive) |
| `seaIce.evspsbl.tavg-u-hxy-si` Sea-Ice Mass Change Through Evaporation and Sublimation | mon High | `sidmassevapsubl` | copy | flip: CICE writes the rate of change of the ice mass (negative for sublimation); the DR has positive=up: declare the model value as positive down so that CMOR flips it | none | original code: multiplied by rhoi (917 times too large) and cumulative since the start of the job (evapi never reset) |

#### Snow tendencies and precipitation

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.sisndmassdyn.tavg-u-hxy-si` Snow Mass Rate of Change Through Advection by Sea-Ice Dynamics | mon High | `sisndmassdyn` | copy | none | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | new field |
| `seaIce.sisndmasssi.tavg-u-hxy-si` Snow Mass Rate of Change Through Snow-to-Ice Conversion | mon High | `sisndmasssi` | copy (<= 0) | none | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | new field |
| `seaIce.snm.tavg-u-hxy-si` Snow Mass Rate of Change Through Melt | mon High | `sisndmassmelt` | copy | none: now written <= 0 as the DR; remove any sign change in the post-processing | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | renamed (was `sndmassmelt`), sign changed (was positive) |
| `seaIce.sbl.tavg-u-hxy-si` Snow Mass Rate of Change Through Evaporation or Sublimation | mon High | `sisndmasssubl` | copy | none (rate of change, negative for sublimation; no positive attribute in the DR) | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | renamed (was `sndmassubl`); original code: multiplied by rhos and cumulative since the start of the job (evaps never reset) |
| `seaIce.prsn.tavg-u-hxy-si` Snow Mass Change Through Snowfall | mon High | `sisndmasssnf` | copy | none | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | renamed (was `sndmasssnf`), no density factor, weighted by aice_init |
| `seaIce.prra.tavg-u-hxy-si` Rainfall Rate over Sea Ice | mon High | `sipr` | copy | none | fill where the time-mean `aice` = 0 (DR mask=siconc; CICE writes 0 there) | was DISCARD: now written (rain on ice with level-ice ponds) |
| `seaIce.sisndmasswind.tavg-u-hxy-si` Snow Mass Rate of Change Through Wind Drift of Snow | mon High | `DISCARD` | not available (snwredist = none, tr_snow = .false.) | none | none | as before |

#### Radiation and heat fluxes

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.rsds.tavg-u-hxy-si` Downwelling Shortwave Flux over Sea Ice
 | day High<br>mon High | `siflswdtop` | copy | none | none: CICE writes the fill value where the time-mean `aice` = 0 (DR mask=siconca: ocean grid used) | as before |
| `seaIce.rsus.tavg-u-hxy-si` Upwelling Shortwave Flux over Sea Ice | day High<br>mon High | `siflswutop` | copy | none: positive up, as the DR | none: CICE writes the fill value where the time-mean `aice` = 0 (DR mask=siconca) | as before |
| `seaIce.rlds.tavg-u-hxy-si` Downwelling Longwave Flux over Sea Ice | mon High | `sifllwdtop` | copy | none | none: CICE writes the fill value where the time-mean `aice` = 0 (DR mask=siconca) | as before |
| `seaIce.rlus.tavg-u-hxy-si` Upwelling Longwave Flux over Sea Ice | mon High | `sifllwutop` | copy | none: now written positive up as the DR; remove any sign change in the post-processing | none: CICE writes the fill value where the time-mean `aice` = 0 (DR mask=siconca) | sign changed (was negative) |
| `seaIce.siflsenstop.tavg-u-hxy-si` Net Downward Sensible Heat Flux over Sea Ice | mon High | `siflsenstop` | copy | none: positive down | none: CICE writes the fill value where the time-mean `aice` = 0 (DR mask=siconca) | as before |
| `seaIce.sifllattop.tavg-u-hxy-si` Net Latent Heat Flux over Sea Ice | mon High | `sifllattop` | copy | none: positive down | none: CICE writes the fill value where the time-mean `aice` = 0 (DR mask=siconca) | renamed (was `sifllatstop`) |
| `seaIce.siflcondtop.tavg-u-hxy-si` Net Conductive Heat Flux in Sea Ice at the Surface | mon High | `siflcondtop` | copy | none: positive down | none: CICE writes the fill value where the time-mean `aice` = 0 | values corrected (original code weighted the grid-cell flux by the ice area a second time) |
| `seaIce.siflcondbot.tavg-u-hxy-si` Net Conductive Heat Flux in Sea Ice at the Base | mon High | `siflcondbot` | copy | none: positive down | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.siflswdbot.tavg-u-hxy-si` Downwelling Shortwave Flux under Sea Ice | mon High | `siflswdbot` | copy | none: positive down | none: CICE writes the fill value where the time-mean `aice` = 0 | as before |
| `seaIce.siflsensbot.tavg-u-hxy-si` Net Upward Sensible Heat Flux under Sea Ice | mon High | `siflsensbot` | copy | none: positive down (heat from the ocean to the ice is negative) | none: CICE writes the fill value where the time-mean `aice` = 0 | new definition (fbot, the sensible flux) and name (was `siflsensupbot`, fhocn) |

#### Fresh water and salt

| CMIP7 variable | Requests | CICE field(s) | Operation | Sign | Mask | Change |
|---|---|---|---|---|---|---|
| `seaIce.siflfwbot.tavg-u-hxy-si` Freshwater Flux from Sea Ice | mon Medium | `siflfwbot` | copy | none: positive into the ocean | none: CICE writes the fill value where the time-mean `aice` = 0 | frazil term defined (was undefined with update_ocn_f = .true.) |
| `seaIce.siflfwdrain.tavg-u-hxy-si` Freshwater Flux from Sea-Ice Surface | mon Medium | `siflfwdrain` | copy (approximation: pond storage not removed) | none | none: CICE writes the fill value where the time-mean `aice` = 0 | units fixed, rain removed |
| `seaIce.sfdsi.tavg-u-hxy-si` Salt Flux from Sea Ice | mon Medium | `siflsaltbot` | copy | none: positive into the ocean | none: CICE writes the fill value where the time-mean `aice` = 0 | frazil term defined |

### 7.3 Variables computed offline (not written by CICE)

Hemispheric integrals, monthly, from the monthly means of the same file (`tarea` in m2 and
`TLAT` are in every history file):

| CMIP7 variable | Requests | Formula | Units |
|---|---|---|---|
| `seaIce.siarea.tavg-u-hm-u` Sea-Ice Area North | mon nh High<br>mon sh High | sum(aice * tarea) / 1e12 over TLAT > 0 (nh) or TLAT < 0 (sh); 1e6 km2 | 1e6 km2 |
| `seaIce.siextent.tavg-u-hm-u` Sea-Ice Extent North | mon nh High<br>mon sh High | sum(tarea where aice >= 0.15) / 1e12 per hemisphere, from the monthly mean aice; 1e6 km2 | 1e6 km2 |
| `seaIce.sivol.tavg-u-hm-u` Sea-Ice Volume North | mon nh High<br>mon sh High | sum(hi * tarea) / 1e12 per hemisphere; 1e3 km3 | 1e3 km3 |
| `seaIce.sisnmass.tavg-u-hm-si` Snow Mass on Sea Ice North | mon nh High<br>mon sh High | sum(330 * hs * tarea) per hemisphere; kg | kg |

Notes: `nh` = `TLAT > 0`, `sh` = `TLAT < 0`; land cells are fill values and are skipped; the
extent uses the monthly mean concentration (threshold 0.15 on `aice`, i.e. 15 %).

Also derived offline from written fields (section 7.2): `siconc` (100 aice), `simass` (917 hi),
`snw` (330 hs), `snd`, `snc`, `simpconc`, `simpeffconc`, `simpthick`, `simprefrozen`,
`sirdgconc`.

### 7.4 Variables from other components, or not available

| CMIP7 variable | Requests | Source / reason |
|---|---|---|
| `seaIce.siconca.tavg-u-hxy-u` Sea-Ice Area Percentage (Atmospheric Grid) | day High<br>mon High | other component: 100 * ICEFRAC from CAM (atmosphere grid) |
| `land.tslsi.tpt-u-hxy-lsi` Surface Temperature Where Land or Sea Ice | 3hr High | other component: CAM TS, instantaneous, 3hr (land + sea-ice surface temperature) |
| `ocean.sfdsi.tavg-u-hxy-sea` Downward Sea Ice Basal Salt Flux | 3hr High | other component: ocean model (NEMO salt flux received from the sea ice, 3-hour mean of the hourly coupling values; check field, units (g vs kg) and sign in field_def); alternative: CICE fsalt_ai on a 3-hourly stream |
| `ocnBgchem.sialgc.tavg-u-hxy-si` Total Ice Algal Carbon Amount in Sea Ice | mon Medium | not available: sea-ice BGC off |
| `ocnBgchem.sichl.tavg-u-hxy-si` Amount of Total Ice Algae Expressed as Chlorophyll in Sea Ice | mon Medium | not available: sea-ice BGC off |
| `ocnBgchem.sigpp.tavg-u-hxy-si` Gross Primary Productivity in Sea Ice as Carbon Amount Flux | mon Medium | not available: sea-ice BGC off |
| `ocnBgchem.sino3.tavg-u-hxy-si` Dissolved Nitrate Amount in Sea Ice | mon Medium | not available: sea-ice BGC off |
| `ocnBgchem.sisi.tavg-u-hxy-si` Dissolved Silicon Amount in Sea Ice | mon Medium | not available: sea-ice BGC off |

### 7.5 Summary of the changes for the post-processing

- **Sign changes to undo** in the existing post-processing (CICE now writes the DR sign):
  `sidmassmelttop`, `sidmassmeltbot`, `sidmassmeltlat`, `snm` (now <= 0), `rlus` (now >= 0).
- **Sign flip still needed:** `evspsbl` (CICE rate of change of the ice mass, DR positive=up).
- **Renamed CICE fields:** `sidmasssi` -> `sidmassgrowthsi`, `sidmasslat` -> `sidmassmeltlat`,
  `sndmassubl` -> `sisndmasssubl`, `sndmasssnf` -> `sisndmasssnf`, `sndmassmelt` ->
  `sisndmassmelt`, `sifllatstop` -> `sifllattop`, `siflsensupbot` -> `siflsensbot`.
- **New CICE fields:** `sisndmassdyn`, `sisndmasssi`, `sisali`, `sisaltmass`, `siitdsnconc`.
- **Now written** (was DISCARD): `prra` (`sipr`).
- **Values or units changed:** `evspsbl`, `sbl`, `prsn` (no density factor), `siitdconc` (%, no
  factor 100 in post-processing), `siitdsnthick`, `sithick` ridged (`sirdgthick`),
  `siflsensbot`, `siflfwdrain`, `siflcondtop`, `sitempsnic`, `sitempbot`, tendencies at melt-out.
- **Lookup rows corrected:** `simpthick` and `simprefrozen` (fields swapped), `simass`
  (`hi*917`), `snw` (`hs*330`), `sirdgconc` (`ardg aice`), `prra` (`sipr`); new rows for the
  hemispheric integrals, the 3-hourly variables and the BGC variables (DISCARD).


### 7.6 Reconstruction of the original fields (offline)

The original field names no longer exist (a namelist that sets their flags is rejected) and the
original definitions were replaced, not kept as an option. Where needed, for example to compare
with runs of the original code, the original values can be reconstructed offline from the
fields of the modified code. Notation: time means of the same record; `aice` is the time-mean
ice concentration (fraction); "exact" means equal up to the cells and steps with `aice <= puny`
at the end of the step, which the original code skipped.

| Original field | Reconstruction | Fields needed (flag) | Accuracy |
|---|---|---|---|
| `sidmasssi` | `sidmassgrowthsi` | `f_sidmassgrowthsi` | exact; the original skipped the steps where the ice disappears |
| `sidmasslat` | `-sidmassmeltlat` | `f_sidmassmeltlat` | as above |
| `sidmassmelttop`, `sidmassmeltbot` (original sign, >= 0) | `-sidmassmelttop`, `-sidmassmeltbot` | same flags | as above |
| `sndmassmelt` | `-sisndmassmelt` | `f_sisndmassmelt` | as above |
| `sifllatstop` | `sifllattop` | `f_sifllattop` | exact (only the name changed) |
| `sifllwutop` (original sign, <= 0) | `-sifllwutop` | `f_sifllwutop` | exact |
| `siflsensupbot` (`aice * fhocn`, per ice area) | `fhocn_ai / aice` | `f_fhocn_ai`, `f_aice` | exact (ratio of the time means, as the original normalisation) |
| `siitdconc` (fraction) | `siitdconc / 100` | `f_siitdconc` | exact |
| `siitdsnthick` (snow volume per category ice area) | `vsnon / aicen` | `f_vsnon`, `f_aicen` | exact (ratio of the time means, as the original normalisation) |
| `snowfracn` (original value, twice the mean) | `2 * snowfracn` | `f_snowfracn` | exact |
| `sipr` (`aice * frain`, per ice area) | `rain_ai / 8640 / aice` (`rain_ai` in cm/day of water) | `f_rain_ai`, `f_aice` | approximate (`aice_init` instead of `aice` in the weight); with ponds also `sipr / aice` |
| `sndmasssnf` (`aice * fsnow * rhos`) | `330 * sisndmasssnf` | `f_sisndmasssnf` | approximate (`aice_init` instead of `aice`) |
| `sndmassubl` (`evaps * rhos`) | `330 * sisndmasssubl` | `f_sisndmasssubl` | not the original values: in the original code `evaps` was never reset, so the field was a sum since the start of the job; the reconstruction gives the per-step value with the original factor |
| `sidmassevapsubl` (original, `evapi * rhoi`) | `917 * sidmassevapsubl` | `f_sidmassevapsubl` | as `sndmassubl` (`evapi` never reset) |
| `fsurf_ai`, `fcondtop_ai` (original, weighted again by `aice_init`) | `fsurf_ai * aice`, `fcondtop_ai * aice` | `f_fsurf_ai`, `f_fcondtop_ai`, `f_aice` | approximate (product of time means) |

Not reconstructable, and not useful because the original values were wrong:
- `sirdgthick`: time mean of a ratio computed at every step;
- `siflcondtop`: time mean of `aice * fcondtop`;
- `sitempsnic`, `sitempbot`: division of cell values by `aice_init`;
- `siflfwdrain`: sum of quantities with different units;
- `siflfwbot`, `siflsaltbot`: undefined frazil term;
- `sidmassgrowthwat`: frazil of ice-free cells excluded; it can be approximated by the new field.

The fields used only for a reconstruction (`fhocn_ai`, `rain_ai`, `vsnon`, `aicen`,
`fsurf_ai`, `fcondtop_ai`) are not all in the CMIP7 namelist of section 6: add their flags
(monthly) if needed. `user_nl_cice_full_test.txt` writes all of them.

## 8. Differences from CICE 6.6.3

| Field | 6.6.3 | Here | Reason |
|---|---|---|---|
| `siflsensbot` | `aice * fhocn` | `aice * fbot` | DR: sensible heat flux |
| `sipr` | non-zero only with topographic ponds | non-zero with any pond scheme | rain also enters level-ice ponds |
| `sifllwutop` | negative | positive upward | DR positive up |
| `sisndmasssnf` | `fsnow` (whole cell) | `aice_init * fsnow` | DR: snowfall onto sea ice |
| `sisndmasssi` | `-rhos * snoice` always | depends on `ktherm` | with `ktherm = 1` the snow mass converted is `rhoi * snoice` |
| `siitdsnconc` | `snowfracn` (fraction of the category ice area) | `aicen * snowfracn` | DR: percentage of the grid cell |
| `sidmassevapsubl` | `rho_ice * evapi` | `evapi` | units (not checked against the Icepack of 6.6) |
| `snowfracn` | accumulated twice | once | bug |
| `siflfwdrain` | `aice * (melts + meltt)` | `(rhoi * meltt + rhos * melts) / dt` | units |
| `siflcondtop`, `fsurf_ai`, `fcondtop_ai` | weighted twice by the ice area (nuopc driver) | grid-cell flux | bug |

Not ported from 6.6.3: its general normalisation options (`avg_ice_present`) and the fields
`siconc`, `simass`, `sisnmass`, `sivol`, `sisnconc`, `sirdgconc`, `sitimefrac`; the
corresponding DR variables are derived exactly in the post-processing (sections 7.2, 7.3).

## 9. Limitations and known behaviours

Not implemented (they need changes to Icepack or to the physics, excluded):
- `siflfwdrain` exact: the water stored in or released from the melt ponds is not accounted for.
- `sitempsnic`: `Tsnice` is the value of the last category computed in the step, not a mean over
  the categories (Icepack does not aggregate it).
- `sisndmasswind`: needs `tr_snow = .true.` and snow redistribution.
- Sea-ice BGC variables: need CICE BGC on.

Behaviours of CICE 6.3 left unchanged, relevant for the post-processing and the tests:
- `sitempsnic`: `Tsnice` is computed after the temperature solver and before the melt
  (`thickness_changes`); with `ktherm = 2` the temperature of melting snow can be a fraction of a
  degree above 0 C (up to 273.7 K, about 0.1 % of the points in the tests).
- In a step where the ice of a cell disappears completely, the CMIP fluxes averaged over the ice
  area (`aice > puny` at the end of the step) do not count that step, while the grid-cell fluxes
  of CICE (`*_ai`) do. The mass and area tendencies count it (section 3.2).
- Conventions of the per-ice-area fluxes: `siflcondbot`, `sitempbot`, `sistr*dtop`, `sialb`,
  `siflswutop` use `aice * x / aice_init` (flux per ice area at the start of the step, weighted by
  the final area), while `sifllattop`, `siflsenstop`, `siflcondtop` accumulate the grid-cell flux;
  they differ only where the ice area changes within a step.
- `alvdr_ai`, `alidr_ai`, `alvdf_ai`, `alidf_ai`, `albsni`: accumulated at every step (albedo 1
  in the dark) but divided by the number of sunlit steps, so they can exceed 100 %.
- `sialb`: fill value also where there was no sunlit step in the period (polar night).
- `Tref`, `Qref`: divided by `aice` in `scale_fluxes` but summed with `aicen_init` weights, so
  very large where the ice almost disappears within a step.
- `Tsnz`: accumulated also for categories without snow, where the mushy snow temperature of a
  zero enthalpy is far above 0 C.
- `dagedtt`: excludes the ageing of the step (`offset = dt`), and where the ice disappears within
  a step keeps the initial age instead of a rate.
- `sistreave`, `sistremax`: built from `sig1`, `sig2`, normalised by the ice strength, so
  dimensionless, but labelled N m-1 (not requested by CMIP7).

## 10. Verification

### 10.1 Test script

`scripts/test_cice_cmip7_output.py` reads the history files of a run and checks them:

```
python3 test_cice_cmip7_output.py <hist dir> --case <case> --histfreq m,d --mfilt 2,10 \
        --user-nl <case>/user_nl_cice
```

`<hist dir>` is the run directory, or `<DOUT_S_ROOT>/ice/hist` after the short-term archiving.
The streams are recognised from the length of their averaging period, the `_d` names are read as
the base names, and every check runs only if its fields are in the files. Needs numpy and
netCDF4 (or scipy). Exit status 1 if a check fails. Groups of checks:

- **files:** records per file not above `hist_mfilt`, shorter files only at the end of a job,
  increasing time, contiguous `time_bounds`;
- **fields:** with `--user-nl`, every field requested on each stream is present (with the
  normalisation fields forced by the code); no original names left;
- **units:** units of the 234 fields that the configuration can write;
- **mask:** fields averaged over an area defined exactly where the time mean of that area is > 0;
- **equal** (relations that hold by construction; FAIL above 1e-4 relative to the field maximum
  on more than 0.1 % of the points): CMIP mass and area terms against `dvidt*`, `daidt*`,
  `frazil`, `congel`, `snoice`, `melt*`, `snow_ai`, `rain_ai`; `sithick * aice = hi`;
  sums over the categories (`aicen`, `vicen`, `vsnon`, `siitdconc`, `siitdsnconc = snowfrac`,
  `ardgn`, `vrdgn`); `siitdthick * aicen = vicen`; `sirdgthick * ardg = vrdg`;
  `alvl + ardg = aice`; `fswup = fswdn - fswabs_ai`; `siflfwbot`, `siflsaltbot`, `siflswdbot`
  against `fresh_ai`, `fsalt_ai`, `fswthru_ai`; `sifllattop`, `siflsenstop`, `siflcondtop`
  against the category sums of `flatn_ai`, `fsensn_ai`, `fcondtopn_ai`; `fsurf_ai`,
  `fcondtop_ai`, `fmeltt_ai` against their category sums;
- **approx** (WARN only): relations with `aice_init` instead of `aice`, or products of means;
- **budget:** `rhoi * d(hisnap)/dt = sidmassth + sidmassdyn` and
  `d(aisnap)/dt = sidconcth + sidconcdyn` (exact), `sidmassth` = sum of the CMIP mass terms,
  global ice transport ~ 0, ice age and global snow mass (approximate);
- **ineq:** inequalities that hold by construction (mean speed >= speed of the mean velocity,
  `aice <= sitimefrac`, `snowfrac <= aice`, ...);
- **ranges:** fractions, signs and physical ranges, with the DR signs.

The script was also checked on synthetic files that emulate step by step the accumulation and
normalisation of the modified code (all checks pass), with errors injected on purpose (each one
reported as FAIL).

### 10.2 Runs

Coupled runs of cmcc-esm3:
- With the final code, `user_nl_cice_full_test.txt` (all 234 fields, monthly and daily),
  1 + 1 month with restart, `hist_mfilt = 2, 10`: results below.
- With the same history writer and `user_nl_cice_cmip7_coupled.txt`, 2 years: one file per year
  per stream, 12 and 365 records, all requested fields present.
- Results of the 1 + 1 month run: all the exact relations, masks, units and inequalities hold;
  the ice mass and area budgets from the snapshots close exactly (relative difference about
  1e-7, also in the cells where the ice disappears), as the sum of the CMIP mass terms. The only
  values out of range are `sitempsnic` slightly above 273.15 K (Icepack behaviour, section 9; the
  script reports it as WARN) and `Tref`, `Qref` (section 9). The approximate checks of the melt
  ponds and of the global snow mass give WARN (differences of 5-18 %, expected for products of
  time means).
- `ice.log` at the end of each job: the files still open are closed by `ModelFinalize`
  (`Closed history file ... (n time records)`), without PIO errors.
