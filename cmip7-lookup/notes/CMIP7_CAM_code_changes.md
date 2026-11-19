# CAM6.3 code changes for the CMIP7 Data Request (v1.2.2.5) variable mapping

This document lists the source code changes made to CAM6.3 to provide the CMIP7
atmosphere variables (DECK + Fast Track selection, mapping in `atm_lookup.csv`,
decisions and tests in `atm_lookup_notes.md`).

- **Base:** source tree in `src_tar.gz` (CAM `src/`).
- **Cumulative patch:** `cam_cmip7_mods_cumulative/cumulative.patch` (apply from the
  directory containing `src/` with `patch -p1 < cumulative.patch`); the modified files are
  also in `cam_cmip7_mods_cumulative/src/`.
- **Scope:** diagnostics only. No change modifies the model state, tendencies or
  fluxes; every change adds history fields, fixes metadata, or changes how existing
  diagnostics are computed.
- **Namelist:** no new namelist variables. New fields are requested through
  `fincl`, existing namelists (e.g. `phys_grid_ctem_opts`) are unchanged.
- **New dependency:** `zonal_mean_mod.F90` calls the LAPACK routine `DGESV`.

## Summary of modified files

| # | File | Change (short) | New history fields |
|---|---|---|---|
| 1 | `src/physics/cam/cam_diagnostics.F90` | pressure-level fields "where air"; 10 m wind components; heat indices; RH units | T850air, T500air, T250air, U850air, U500air, U250air, V850air, V500air, V250air, Z500air, UAS, VAS, HEATIDX, HEATIDXMX, WBGT, WBGTMX |
| 2 | `src/physics/cam/conv_water.F90` | total grid-mean cloud ice and liquid (stratiform + convective + radiative snow) | CLITOT, CLWTOT |
| 3 | `src/chemistry/utils/modal_aero_wateruptake.F90` | aerosol number concentration, PM2.5 3D, surface PM1/PM2.5/PM10 | CONCCN, MMRPM25, SFPM25, SFPM1, SFPM10 |
| 4 | `src/physics/cam/aerosol_optics_cam.F90` | dust and sulfate absorption AOD; SSA before night masking; long names of `*dn` fields | AODABSDUSTdn, AODABSSO4dn, AODABSDUST, AODABSSO4 |
| 5 | `src/physics/cam/aer_rad_props.F90` | day-night visible optical depth of bulk aerosols | ODVdn_\<aerosol\> (e.g. ODVdn_VOLC_MMR) |
| 6 | `src/chemistry/utils/prescribed_ozone.F90` | total ozone column of the prescribed ozone | TOZ |
| 7 | `src/chemistry/mozart/mo_srf_emissions.F90` | biomass burning surface emission flux per species | SFBB_\<species\> |
| 8 | `src/physics/rrtmg/radlw.F90`, `src/physics/rrtmg/radiation.F90` | LW upward flux at the top of the atmosphere (top of the RRTMG extra layer) | FLUTOA, FLUTOAC |
| 9 | `src/physics/cam/cloud_cover_diags.F90`, `src/physics/cam/cloud_diagnostics.F90` | total convective cloud cover | CLDTOTCONV |
| 10 | `src/physics/cam_dev/micro_pumas_cam.F90` | liquid cloud cover seen from TOA; cloud-top CCN | CLDLIQTOT, ACTCCN01, ACTCCN02 |
| 11 | `src/physics/cam/microp_aero.F90`, `src/physics/cam/ndrop.F90` | pbuf fields for CCN at S = 0.1 % and 0.2 % | (none, used by #10) |
| 12 | `src/physics/cam/phys_grid_ctem.F90` | potential temperature reference pressure fix; longitude-sampling correction of the zonal-mean bins | (existing Uzm, Vzm, Wzm, THzm, UVzm, UWzm, VTHzm, WTHzm) |
| 13 | `src/utils/zonal_mean_mod.F90` | optional longitude-sampling correction (LON_HARMONICS) in the zonal average | (none, used by #12) |

---

## 1. `src/physics/cam/cam_diagnostics.F90`

### 1a. Temperature, wind and geopotential on pressure levels, missing below the surface ("where air")

- **CMIP7 variables:**
  - `ta`, `ua`, `va` `tpt-p3-hxy-air`: air temperature, eastward and northward wind at 850, 500 and 250 hPa, 6-hourly instantaneous;
  - `ta` `tavg-850hPa-hxy-air`: daily mean temperature at 850 hPa;
  - `zg` `tavg-500hPa-hxy-air`: daily mean geopotential height at 500 hPa.
- **New fields:**
  - T850air, T500air, T250air (temperature, K);
  - U850air, U500air, U250air (zonal wind, m/s);
  - V850air, V500air, V250air (meridional wind, m/s);
  - Z500air (geopotential height, m).
- **Routines:** `diag_init_dry` (addfld), `diag_phys_writeout_dry` (computation).
- **Explanation:** the CMIP7 "where air" cell method (CF area type `air`) requires
  missing values where the pressure level is below the surface. The CAM single-level
  fields (T850, U850, Z500, ...) are extrapolated below ground, so they do not satisfy
  this requirement. The new fields work as follows:
  - the interpolation is the same as for the CAM fields (`vertinterp`; ECMWF extrapolation for T and Z, log-pressure interpolation for Z, lowest value for U and V);
  - the result is set to `fillvalue` where the level pressure is greater than PS;
  - the fields are registered with `flag_xyfill=.true.`, so time averages use only the valid samples.

  Computed only when the field is active (`hist_fld_active`). This replaces 3D output
  for these variables (data volume reduction).
- **Test:**
  - T, U, V (hourly instantaneous, 1970-01-02): the mask is exactly p > PS, the values are identical to T850/U850/... where defined, and the offline interpolation agrees within single-precision rounding.
  - Z500air (6-hourly instantaneous): identical to Z500 where defined; the offline ln(p) interpolation of Z3 agrees
    within single-precision rounding (max |d| 7.6e-4 m). No column had PS < 500 hPa in the test sample, so the mask was not
    exercised for Z500air (same code as the T/U/V fields, where it is verified).

### 1b. 10 m wind components

- **CMIP7 variables:** `uas`, `vas`, the eastward and northward 10 m wind (mean and instantaneous).
- **New fields:** UAS, VAS (m/s).
- **Routine:** `diag_surf`.
- **Explanation:**
  - The fields are computed as UAS = U10 · u_bot/|V_bot| and VAS = U10 · v_bot/|V_bot|, with the components set to 0 if |V_bot| < 1e-6 m/s.
  - U10 is the 10 m wind speed from the coupler; u_bot, v_bot and |V_bot| are the wind components and speed at the lowest model level.
  - The computation runs every time step, with the state at the end of `tphysbc` (the state used by the coupler to compute U10).
  - Means of the components cannot be rebuilt offline from mean U10 and mean UBOT/VBOT.
- **Test:** |(UAS, VAS)| = U10 to 1e-7 relative (hourly instantaneous); monthly means consistent.

### 1c. Heat stress indices

- **CMIP7 variables:**
  - `noaahi2m`: 2 m NOAA heat index, daily mean and maximum;
  - `wbgt2m`: 2 m wet-bulb globe temperature, daily mean and maximum.
- **New fields:**
  - HEATIDX and HEATIDXMX (NOAA heat index and its maximum over the output period, degC);
  - WBGT and WBGTMX (simplified wet-bulb globe temperature and its maximum, degC).
- **Routine:** `diag_surf`.
- **Explanation:**
  - HEATIDX uses the NOAA (Rothfusz) formula with TREFHT in degF and RHREFHT in %, converted to degC. It is set to `fillvalue` (`flag_xyfill`) where TREFHT < 299.817 K, the range of validity defined in the DR.
  - WBGT = 0.567 T + 0.393 e + 3.94, with T = TREFHT in degC and e the vapour pressure in hPa from QREFHT and PS.
  - The maxima use the `X` averaging flag on the time-step values.
- **Test:** instantaneous recomputation exact (max 5e-5 degC); WBGTMX >= WBGT everywhere.

### 1d. Relative humidity fields (pre-existing local changes in the user's version; units fixed here)

- **CMIP7 variables:** `hurs`, the 2 m relative humidity (mean, minimum, maximum, instantaneous).
- **Fields:** RHREFHTMN and RHREFHTMX (daily minimum and maximum of RHREFHT, RH w.r.t. liquid water); RHCFMIPHT, RHCFMIPHTMN and RHCFMIPHTMX (2 m RH w.r.t. water above 273 K and w.r.t. ice below).
- **Explanation:**
  - These fields and the `hist_fld_active` guards on the 3D RHI/RHCFMIP computation were already in the version of `cam_diagnostics.F90` provided by the user. They are not in the base tree, so they appear in the cumulative patch.
  - The change made here is in the units of RHREFHT, RHREFHTMN/MX and RHCFMIPHT/MN/MX: `fraction` → `percent`, because the values are computed as q/qs·100.
  - A `use ... fillvalue` was also added to the module header (needed by 1a and 1c).

## 2. `src/physics/cam/conv_water.F90`

- **CMIP7 variables:** `cli`, `clw`, the mass fraction of cloud ice and cloud liquid water (3D).
- **New fields:** CLITOT, CLWTOT (kg/kg, 3D).
- **Routines:** `conv_water_register`/`conv_water_init` (indices, addfld), `conv_water_4rad` (computation).
- **Explanation:** grid-mean cloud condensate as seen by radiation, referred to the mass of air including all water phases, as the DR definition requires:
  - CLITOT = (CLDICE + GCIMRDP + GCIMRSH + ICSWP·CLDFSNOW·g/Δp) / (1 + cond);
  - CLWTOT = (CLDLIQ + GCLMRDP + GCLMRSH) / (1 + cond).

  The terms are:
  - CLDICE, CLDLIQ: stratiform cloud ice and liquid (which also contain the condensate detrained by deep convection);
  - GC\*MRDP and GC\*MRSH: deep and shallow convective in-plume condensate;
  - ICSWP·CLDFSNOW: radiative snow, from pbuf fields set by PUMAS. The QSNOW pbuf field cannot be used because it exists only with SILHS.
  - cond = CLDLIQ + CLDICE + RAINQM + SNOWQM + GRAUQM: the CAM wet mixing ratios are relative to dry air + vapour, hence the 1/(1 + cond) factor.

  Computed only when the fields are active.
- **Test (1970-01):** ratio 1.011 against the sum of the output components (difference due to the snow of the last substep).

## 3. `src/chemistry/utils/modal_aero_wateruptake.F90`

- **CMIP7 variables:**
  - `conccn`: aerosol number concentration (3D);
  - `mmrpm2p5`: PM2.5 mass mixing ratio (3D);
  - `sfpm25`, `sfpm1`, `sfpm10`: near-surface PM2.5, PM1 and PM10.
- **New fields:**
  - CONCCN (m-3, 3D): sum over the modes of the interstitial number mixing ratio times air density;
  - MMRPM25 (kg/kg, 3D): dry aerosol mass below 2.5 µm;
  - SFPM25, SFPM1, SFPM10 (kg/kg, lowest model level): ambient (dry + water) aerosol mass below 2.5, 1 and 10 µm.
- **Routines:** `modal_aero_wateruptake_init` (addfld), `modal_aero_wateruptake_dr` (computation).
- **Explanation:**
  - The size cut is the one of the CAM PM25 diagnostic: lognormal cumulative fraction (erf) around the number median diameter of each mode.
  - MMRPM25 uses the dry diameter and dry mass; the surface fields use the wet diameter `dgncur_awet` and the wet mass `maer + qaerwat`.
  - The number-median cut was kept on purpose, for consistency with the CAM PM25 field; a cut on the volume median diameter was evaluated and not adopted.
- **Test (1970-01):**
  - CONCCN and MMRPM25 agree with the offline reconstruction (median relative difference 1.5e-4);
  - SFPM1 ≤ SFPM25 ≤ SFPM10 everywhere.

## 4. `src/physics/cam/aerosol_optics_cam.F90`

- **CMIP7 variables:**
  - `abs550dust`, `abs550so4`: dust and sulfate absorption optical depth at 550 nm;
  - the day-and-night fields used for `od550*`, `abs550*`, `load*`.
- **New fields:** AODABSDUSTdn and AODABSSO4dn (day and night), plus the day-only twins AODABSDUST and AODABSSO4.
- **Routines:** `aerosol_optics_cam_init` (addfld), `aerosol_optics_cam_sw` (computation).
- **Explanation:**
  - Dust and sulfate absorption AOD are computed with the same species partitioning as the existing AODABSBC: `abs<species> · dopaer · (1 − palb)`.
  - SSAVIS is now normalised before the night masking, so SSAVISdn is valid at night.
  - The long names of the `*dn` fields were corrected from "day only" to "day night".
- **Test (1970-01):** AODABSDUSTdn non-negative and ≤ AODDUSTdn; dust is 31 % of the global absorption AOD.

## 5. `src/physics/cam/aer_rad_props.F90`

- **CMIP7 variables:** `aod550volso4`, the stratospheric volcanic sulfate aerosol optical depth at 550 nm.
- **New fields:** ODVdn_\<aerosol\>, one per bulk (prescribed) aerosol, e.g. ODVdn_VOLC_MMR.
- **Explanation:** visible-band optical depth written before the night masking. The existing ODV_\<aerosol\> fields are day only.
- **Test (after fixing the input file):** no missing values; mean relative difference to the day-only field 0.5 %.

## 6. `src/chemistry/utils/prescribed_ozone.F90`

- **CMIP7 variables:** `toz`, the total ozone column (daily and monthly).
- **New field:** TOZ (m at STP; 1 DU = 1e-5 m).
- **Explanation:**
  - The column of the prescribed ozone is computed every time step as Σ(mmr·Δp_dry)/g and converted kg/m2 → mol/m2 → DU → m.
  - This avoids writing daily 3D ozone.
- **Test (1970-01):** global mean 289 DU, plausible distribution.

## 7. `src/chemistry/mozart/mo_srf_emissions.F90`

- **CMIP7 variables:** `emibbbc`, `emibboa`, `emibbso2`, `emibbdms`, the biomass burning emission fluxes of black carbon, organic aerosol, SO2 and DMS.
- **New fields:** SFBB_\<species\> (kg/m2/s), for example SFBB_bc_a4, SFBB_pom_a4, SFBB_SO2, SFBB_DMS.
- **Explanation:**
  - Emission files whose name contains `_bb_` are flagged as biomass burning.
  - Their flux is accumulated per species in the emission loop, with the same unit conversion as the total SF\<species\>.
  - The unit-conversion branch was rewritten so that the conversion factor (`mfactor`) is applied once for both the total and the biomass burning flux. The total flux is unchanged.
- **Test (1970-01):** SFBB ≤ SF everywhere, no negatives, plausible spatial pattern.

## 8. `src/physics/rrtmg/radlw.F90`, `src/physics/rrtmg/radiation.F90`

- **CMIP7 variables:** `rlut`, `rlutcs`, the TOA outgoing longwave radiation, all-sky and clear-sky.
- **New fields:** FLUTOA, FLUTOAC (W/m2).
- **Explanation:**
  - `rrtmg_lw` returns, through new optional arguments, the upward LW flux at the top of the RRTMG extra layer (`uflx`/`uflxc` at `rrtmg_levs+1`), which is the actual top of the atmosphere.
  - The existing FLUT/FLUTC are at the model top interface.
  - `radiation.F90` adds the fields to the radiation output type, registers them (`sampling_seq='rad_lwsw'`) and writes them.
- **Test (1970-01):** FLUTOA − FLUT global mean 0.16 W/m2; the TOA energy balance with FSNTOA − FLUTOA is consistent.

## 9. `src/physics/cam/cloud_cover_diags.F90`, `src/physics/cam/cloud_diagnostics.F90`

- **CMIP7 variables:** `cltc`, the convective cloud cover percentage.
- **New field:** CLDTOTCONV (fraction).
- **Explanation:**
  - `cloud_cover_diags_out` gets an optional argument `concld` and computes the total cover of the convective cloud fraction CONCLD, with the same overlap as CLDTOT (`cldsav`, now public).
  - `cloud_diagnostics.F90` reads CONCLD from pbuf, if present, and passes it.
- **Test:** CLDTOTCONV ≤ CLDTOT, zero where FREQZM = 0, spatial correlation with FREQZM 0.97.

## 10. `src/physics/cam_dev/micro_pumas_cam.F90`

- **CMIP7 variables:**
  - `cldnvi`: column-integrated cloud droplet number, via cldnvi = CDNUMC/CLDLIQTOT offline;
  - `ccn`: cloud condensation nuclei concentration at liquid cloud top, via ccn = ACTCCN02/FCTL offline.
- **New fields:**
  - CLDLIQTOT (fraction): liquid cloud cover seen from TOA, with max-random overlap (`cldovrlap` + `cldsav`) applied to the liquid cloud fraction where liquid is present (icwmrst > 1e-7 kg/kg);
  - ACTCCN01, ACTCCN02 (m-3): CCN at S = 0.1 % and 0.2 % in the cloud-top layer, converted to STP and weighted by the cloud-top liquid fraction, like ACTREL/FCTL.
- **Explanation:**
  - The CCN values come from the pbuf fields CCN_S01/CCN_S02 (see #11).
  - ACTCCN01/02 are not computed with sub-columns (`use_subcol_microp`).
- **Test (1970-01):** CLDLIQTOT ≤ CLDTOT (within sampling); ACTCCN02 ≥ ACTCCN01, zero where FCTL = 0.

## 11. `src/physics/cam/microp_aero.F90`, `src/physics/cam/ndrop.F90`

- **Purpose:** support for #10.
- **Explanation:**
  - `microp_aero.F90` registers the physics-buffer fields CCN_S01 and CCN_S02 (CCN at S = 0.1 % and 0.2 %) and initialises them to 0.
  - `ndrop.F90` copies them from the `ccn(:,:,3)` and `ccn(:,:,4)` arrays computed by `ccncalc`.
  - If the fields are not registered (index −1), nothing changes.

## 12. `src/physics/cam/phys_grid_ctem.F90`

- **CMIP7 use:** online zonal-mean ingredients for the Transformed Eulerian Mean diagnostics: `epfy` and `epfz` (Eliassen-Palm flux components), `vtem` and `wtem` (residual circulation velocities), `psitem` (residual mass streamfunction), `utendepfd` (zonal wind tendency from the EP flux divergence) and related terms, from Uzm, Vzm, Wzm, THzm, UVzm, UWzm, VTHzm, WTHzm.
- **Explanation:**
  - **Potential temperature fix:** θ is now computed as T·(1e5/p_mid)^(R/cp), using the composition-dependent `cappav`. The previous version used `state%exner`, which with the SE dynamical core is relative to the surface pressure; this gave THzm errors of 11–48 K.
  - **Zonal-mean bins:** `ZAobj%init` is called with `LON_HARMONICS = (/4, 8, 12/)` (see #13), to remove the cubed-sphere sampling signature.
- **Test:** THzm consistent with the offline zonal mean after the θ fix. Latitudinal zig-zag at high latitudes reduced; roughness index from 0.098 to 0.020.

## 13. `src/utils/zonal_mean_mod.F90`

- **Purpose:** support for #12.
- **Explanation:**
  - New optional argument `LON_HARMONICS` of `ZonalAverage_t%init`, with the new routines `lon_sampling_correction` and `lon_factor`.
  - **Problem:** on the cubed sphere the columns of each latitude bin sample longitude non-uniformly, with the 4-fold symmetry of the cube. Zonal wavenumbers 4, 8, 12 of the data therefore leak into the bin averages.
  - **Correction:** at initialisation the column weights of each bin are corrected once, with minimum-norm coefficients, so that the weighted longitude sampling has no component at the given wavenumbers.
  - **Implementation details:**
    - global sums with `shr_reprosum`;
    - solution with LAPACK `DGESV` and a small diagonal regularisation;
    - a bin is left unchanged if its system is singular or if any corrected weight would fall below 5 % of the original;
    - the weight normalisation is recomputed and a summary is written to the log.
  - Run-time cost of the bin averages unchanged. Without the argument the behaviour is the previous one.

---

## Post-processing relations used with the new fields (no code)

- cldnvi = CDNUMC / CLDLIQTOT; ccn = ACTCCN02 / FCTL; reffsclwtop = ACTREL / FCTL;
  cdnc = AWNC / FREQL (ratios of time means, missing where the denominator is 0).
- loadso4 = BURDENSO4dn · 96.06/115.11 (MAM4 so4_a\* are NH4HSO4).
