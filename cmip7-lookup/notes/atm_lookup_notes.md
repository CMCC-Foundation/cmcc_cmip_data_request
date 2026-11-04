# CAM6.3 mapping for the CMIP7 atmosphere variables (DECK and Fast Track) - notes

Data Request v1.2.2.5. Mapping table: `atm_lookup.csv` (same order). `DISCARD` = not available in the model. Confidence: high / medium / low.

Post-processing ratios of time means: missing where the denominator is 0.

Summary: 177 variables: 140 resolved, 0 with open or pending points, 0 still to review, 37 DISCARD (AMIP configuration).

## Configuration facts (atm_in)

- Chemistry package `ghg_mam4`: CO2 transported without chemistry; CH4, N2O, CFC11, CFC12 prognostic with first-order loss rates prescribed from file (`bndtvg` = noaamisc.r8.nc); surface concentrations from `flbc_file` (CMIP7 CR-CMIP-1-0-0, species CO2, CH4, N2O, CFC11, CFC12, CFC11eq).
- Radiation (`rad_climate`): `A:CO2`, `A:N2O`, `A:CH4`, `A:CFC12` (prognostic tracers); `N:CFC11STAR` (CFC11-equivalent, prescribed); `N:ozone` (prescribed, CMIP7 FZJ-CMIP-ozone-2-0, monthly); `N:VOLC_MMR` (prescribed volcanic aerosol); MAM4 modes.
- Oxidants for aerosol chemistry (`tracer_cnst`): O3, OH, NO3, HO2, HALONS prescribed (CMIP6 ensemble average, 1849-2015); not used by radiation.
- Aerosol and precursor emissions: separate input files per sector (CEDS anthropogenic, BB4CMIP7 biomass burning), summed in the model.
- `water_species_in_air` = Q, CLDLIQ, CLDICE, RAINQM, SNOWQM, GRAUQM; `graupel_in_rad` = .false.

## Open or pending points

- none

## Still to review

- none

## Fallback and accessory output (atm_output_fallback.csv)

For variables whose definition or CAM implementation changed between CAM/CMIP6 and CMIP7, the CAM-style or CMIP6-style
version is also saved, in the same streams (frequency and time method) as the CMIP7 variable, for safety and for comparisons
with previous simulations. These fields are not part of the CMIP7 mapping (column "model" of atm_lookup.csv) and are listed,
with stream, priority and volume, in atm_output_fallback.csv (built by volume/build_fallback_table.py; AMIP: +13.9 GB/yr
uncompressed). Groups:
- "where air" pressure-level fields: T850, T500, T250, U850, U500, U250, V850, V500, V250 (6hr instantaneous), T850 and Z500 (daily):
  CAM-style, extrapolated or lowest-level value below ground.
- OLR at top of model (FLUT, FLUTC) instead of top of atmosphere (FLUTOA, FLUTOAC).
- reference-height RH w.r.t. liquid water at all temperatures (RHREFHT, RHREFHTMN, RHREFHTMX) instead of water/ice (RHCFMIPHT*).
- lowest-level wind (UBOT, VBOT) to rebuild other uas/vas definitions with U10.
- CAM surface PM2.5 (PM25_SRF, dry, kg/m3) instead of SFPM25 (ambient, kg/kg).
- day-only aerosol diagnostics (AODVIS, AODABS, AOD<species>, AODABS<species>, BURDEN<species>, ODV_VOLC_MMR) instead of the
  day-night (dn) fields.
- accessory 3D monthly: CLDICE, CLDLIQ (stratiform cloud ice/liquid, CMIP6-style cli/clw).
Not needed as separate fields: pr tmax (CMIP6: maximum of hourly means) can be rebuilt offline from the hourly mean pr;
tauu/tauv: TAUX and TAUBLJX are both in the main table.
DECISION (output namelists, namelist/generate_fincl.py): at sub-daily frequencies (6hr, 3hr, 1hr) only the fields expressly
requested by the DR for the experiment are written; the sub-daily fallback fields of atm_output_fallback.csv (T/U/V at
850/500/250 hPa 6hr, RHREFHT 6hr/3hr, UBOT/VBOT 6hr/3hr/1hr, PM25_SRF 1hr) are not written (option --fallback-subdaily to
restore them). Monthly and daily fallback fields are kept.

## Realm: aerosol

### `aerosol.abs550aer.tavg-u-hxy-u`

- **CMIP6 name:** abs550aer
- **Long name:** Ambient Aerosol Absorption Optical Thickness at 550nm
- **CAM fields:** `AODABSdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.od550aer.tavg-u-hxy-u`

- **CMIP6 name:** od550aer
- **Long name:** Ambient Aerosol Optical Thickness at 550nm
- **CAM fields:** `AODVISdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant, defined at all times, consistent with area: time: mean; used by CESM2 for CMIP6 od550aer (CESM forum). AODVIS is day-only. Only modal (MAM4) aerosols: prescribed volcanic aerosol (VOLC_MMR, bulk) is handled in aer_rad_props.F90 and excluded, as requested by DR.

### `aerosol.abs550bc.tavg-u-hxy-u`

- **CMIP6 name:** abs550bc
- **Long name:** black carbon aaod@550nm
- **CAM fields:** `AODABSBCdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.abs550dust.tavg-u-hxy-u`

- **CMIP6 name:** abs550dust
- **Long name:** dust absorption aerosol optical depth @550nm
- **CAM fields:** `AODABSDUSTdn`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** ok
- **Notes:** NEW online field (aerosol_optics_cam.F90): dust share of the absorption optical depth at 550 nm, day and night, with the same partitioning as AODABSBCdn (volume x imaginary refractive index per species, aerosol water attributed by hygroscopicity). Day-only twin AODABSDUST. (previously DISCARD: No per-species dust absorption AOD.) TEST 1970-01: non-negative, <= AODDUSTdn everywhere; global mean 7.8e-4; dust SSA at 550 nm 0.94 (ratio of means), median 0.956 where AOD > 1e-4; 31% of the global absorption AOD (BC 57%, rest 12%).

### `aerosol.abs550so4.tavg-u-hxy-u`

- **CMIP6 name:** abs550so4
- **Long name:** sulfate aaod@550nm
- **CAM fields:** `AODABSSO4dn`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** ok
- **Notes:** NEW online field (aerosol_optics_cam.F90): sulfate share of the absorption optical depth at 550 nm, day and night, same partitioning as AODABSBCdn; very small because of the tiny imaginary refractive index of sulfate (includes the share of aerosol water absorption). Day-only twin AODABSSO4. (previously DISCARD: No per-species sulfate absorption AOD.) TEST 1970-01: global mean 2.9e-10, essentially zero as expected (sulfate SSA = 1.0000).

### `aerosol.ccn.tavg-u-hxy-ccl`

- **CMIP6 name:** ccn
- **Long name:** Cloud Condensation Nuclei Concentration at Liquid Cloud Top
- **CAM fields:** `ACTCCN02, FCTL`
- **Reprocess:** True
- **Confidence:** medium
- **Status:** ok
- **Notes:** DECISION: ccn = mean(ACTCCN02)/mean(FCTL) (S=0.2%), missing where FCTL = 0; ACTCCN01 (S=0.1%) also saved for internal analysis. New fields ACTCCN01/ACTCCN02 (micro_pumas_cam.F90, cam_dev): in the same cloud-top loop as ACTREL/FCTL (uppermost liquid layer seen from TOA), accumulate CCN converted to m-3 and to STP (DR standard_name ..._at_stp_in_air) times liquid cloud-top fraction; same sampling as FCTL, so the ratio is exact. CCN from ndrop ccncalc (interstitial + cloud-borne aerosol, phase=3), passed via new pbuf fields CCN_S01/CCN_S02 (microp_aero.F90 register/init, ndrop.F90). Not computed with subcolumns in microphysics. Supersaturation: not prescribed by CMIP7 (DR dimensions only longitude latitude time; the relative_humidity coordinate sentence is the generic CF definition) nor by CMIP6/AerChemMIP; 0.2% chosen as the most common reference in multi-model/observation CCN evaluations (AeroCom/ACTRIS); document in the CMOR comment (relative_humidity = 100.2%). DR cell_methods label "where convective_cloud" contradicts its own explanation (liquid-topped cloud seen from TOA), the explanation is followed. Not affected by the CLDLIQTOT fix: the cloud-top loop already requires liquid presence (icwmrst > 1e-7 kg/kg) and the weight liqcldf (= AST) is the fraction over which the model assumes liquid to be spread, as for FCTL/ACTREL. TEST (amip 1970-01): ACTCCN02 >= ACTCCN01 everywhere, zero where FCTL = 0; ccn S=0.2% median 67 cm-3 at STP (p05 2, p95 318), mean land 136 / ocean 84; S=0.1% median 46. Plausible orders of magnitude for cloud-top values, no reference available.

### `aerosol.cdnc.tavg-al-hxy-u`

- **CMIP6 name:** cdnc
- **Long name:** Cloud Liquid Droplet Number Concentration
- **CAM fields:** `AWNC, FREQL`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** cdnc = AWNC/FREQL (ratio of monthly means). micro_pumas_cam.F90 (cam_dev): every microphysics step, where stratiform liquid cloud fraction liqcldf > 0.01 and in-cloud liquid mmr > 5e-5 kg/kg, AWNC accumulates icwnc*liqcldf (in-cloud droplet number, m-3) and FREQL accumulates liqcldf; the ratio is the liquid-cloud-fraction-weighted in-cloud mean "in liquid water clouds" (DR). Set to missing where FREQL = 0. Stratiform liquid only (convective droplets not represented). Units m-3 as in DR.

### `aerosol.cfc114.tavg-al-hxy-u`

- **CMIP6 name:** cfc114
- **Long name:** Mole Fraction of CFC114
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `aerosol.conccn.tavg-al-hxy-u`

- **CMIP6 name:** conccn
- **Long name:** Aerosol Number Concentration
- **CAM fields:** `CONCCN`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online 3D field CONCCN (modal_aero_wateruptake.F90) = sum over modes of naer (#/kg, interstitial) times air density, m-3: exact (no product of means), interstitial only as in the CF aerosol definition (cloud droplets excluded). TEST (amip 1970-01): CONCCN vs sum(num_a)*rho from monthly means: median relative difference 1.5e-4 (p01/p99 -7%/+4%, product of means); lowest level median 327 cm-3, ocean 343, land 1617 cm-3. Resolved.

### `aerosol.emibbbc.tavg-u-hxy-u`

- **CMIP6 name:** emibbbc
- **Long name:** total emission rate of black carbon aerosol mass from all biomass burning
- **CAM fields:** `SFBB_bc_a4`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: SFBB_bc_a4 (black carbon, mass as C). DR/CF: tendency of the atmosphere (column) content due to emission only ("due_to_" = single term of the total tendency; transport and removal excluded), 2D, kg m-2 s-1, vertical integral of all emissions from fires. New online field (mo_srf_emissions.F90): in the per-file emission loop, the flux of the files with "_bb_" in the name (BB4CMIP7 biomass burning files in srf_emis_specifier) is accumulated separately, with the same time interpolation and unit conversion (molecules/cm2/s x mw of the model species) as the total emission. No biomass burning elevated emissions in ext_frc_specifier (only energy and continuous volcanic), so the surface flux is the vertical integral. Relies on the "_bb_" file naming convention. TEST (amip 1970-01, January rate annualised): 1.70 Tg/yr of 7.22 total; no negatives, SFBB <= SF everywhere, maxima in SE Asia and Central Africa. Resolved.

### `aerosol.emibbch4.tavg-u-hxy-u`

- **CMIP6 name:** emibbch4
- **Long name:** total emission of CH4 from all biomass burning
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** CH4 is driven by prescribed surface concentrations (flbc), no CH4 emissions in the model.

### `aerosol.emibbco.tavg-u-hxy-u`

- **CMIP6 name:** emibbco
- **Long name:** total emission rate of CO from all biomass burning
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** No CO species in the ghg_mam4 mechanism.

### `aerosol.emibbdms.tavg-u-hxy-u`

- **CMIP6 name:** emibbdms
- **Long name:** total emission of DMS from all biomass burning
- **CAM fields:** `SFBB_DMS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: SFBB_DMS (mass of DMS, fire emissions only; ocean DMS is a separate source). DR/CF: tendency of the atmosphere (column) content due to emission only ("due_to_" = single term of the total tendency; transport and removal excluded), 2D, kg m-2 s-1, vertical integral of all emissions from fires. New online field (mo_srf_emissions.F90): in the per-file emission loop, the flux of the files with "_bb_" in the name (BB4CMIP7 biomass burning files in srf_emis_specifier) is accumulated separately, with the same time interpolation and unit conversion (molecules/cm2/s x mw of the model species) as the total emission. No biomass burning elevated emissions in ext_frc_specifier (only energy and continuous volcanic), so the surface flux is the vertical integral. Relies on the "_bb_" file naming convention. TEST (amip 1970-01): 0.0061 Tg/yr, equal to SFDMS (file-based DMS emissions are only biomass burning; ocean DMS is not part of SFDMS). Resolved.

### `aerosol.emibboa.tavg-u-hxy-u`

- **CMIP6 name:** emibboa
- **Long name:** total emission of organic aerosol from all biomass burning
- **CAM fields:** `SFBB_pom_a4`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: SFBB_pom_a4 (primary particulate organic matter, as DR). SOA precursors from fires (SOAE) are gases and not included. DR/CF: tendency of the atmosphere (column) content due to emission only ("due_to_" = single term of the total tendency; transport and removal excluded), 2D, kg m-2 s-1, vertical integral of all emissions from fires. New online field (mo_srf_emissions.F90): in the per-file emission loop, the flux of the files with "_bb_" in the name (BB4CMIP7 biomass burning files in srf_emis_specifier) is accumulated separately, with the same time interpolation and unit conversion (molecules/cm2/s x mw of the model species) as the total emission. No biomass burning elevated emissions in ext_frc_specifier (only energy and continuous volcanic), so the surface flux is the vertical integral. Relies on the "_bb_" file naming convention. TEST (amip 1970-01): 17.1 Tg/yr of 36.3 total, consistent with SFBB_bc_a4 footprint. Resolved.

### `aerosol.emibbso2.tavg-u-hxy-u`

- **CMIP6 name:** emibbso2
- **Long name:** total emission rate of SO2 from all biomass burning
- **CAM fields:** `SFBB_SO2`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: SFBB_SO2 (mass of SO2). Primary sulfate from fires (so4_a1 bb file) is not SO2 and not included. DR/CF: tendency of the atmosphere (column) content due to emission only ("due_to_" = single term of the total tendency; transport and removal excluded), 2D, kg m-2 s-1, vertical integral of all emissions from fires. New online field (mo_srf_emissions.F90): in the per-file emission loop, the flux of the files with "_bb_" in the name (BB4CMIP7 biomass burning files in srf_emis_specifier) is accumulated separately, with the same time interpolation and unit conversion (molecules/cm2/s x mw of the model species) as the total emission. No biomass burning elevated emissions in ext_frc_specifier (only energy and continuous volcanic), so the surface flux is the vertical integral. Relies on the "_bb_" file naming convention. TEST (amip 1970-01): 1.94 Tg/yr of 135 total. Resolved.

### `aerosol.emibbvoc.tavg-u-hxy-u`

- **CMIP6 name:** emibbvoc
- **Long name:** total emission rate of NMVOC from all biomass burning
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Only scaled SOA precursor emissions (SOAE) from fires, not total NMVOC.

### `aerosol.hcfc22.tavg-al-hxy-u`

- **CMIP6 name:** hcfc22
- **Long name:** Mole Fraction of HCFC22
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `aerosol.hfc125.tavg-al-hxy-u`

- **CMIP6 name:** hfc125
- **Long name:** Mole Fraction of HFC125
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `aerosol.hfc134a.tavg-al-hxy-u`

- **CMIP6 name:** hfc134a
- **Long name:** Mole Fraction of HFC134a
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `aerosol.lwp.tavg-u-hxy-u`

- **CMIP6 name:** lwp
- **Long name:** Liquid Water Path
- **CAM fields:** `TGCLDLWP`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Liquid only, incl. deep convective liquid (conv_water_in_rad=1).

### `aerosol.mmrpm2p5.tavg-al-hxy-u`

- **CMIP6 name:** mmrpm2p5
- **Long name:** PM2.5 Mass Mixing Ratio
- **CAM fields:** `MMRPM25`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online 3D field MMRPM25 (modal_aero_wateruptake.F90) = PM2.5 dry mass mixing ratio, i.e. PM25 without the air density factor: exact. CAVEAT for the CMOR comment: CAM size cut uses the lognormal CDF with the number median dry geometric diameter; a mass cut should use the volume median diameter (larger by exp(3 ln^2 sigma)) and DR refers to aerodynamic diameter: both suggest an overestimate of PM2.5, mainly for coarse modes (dust, sea salt). TEST (amip 1970-01): MMRPM25*rho vs PM25: median relative difference 1.5e-4 (p01/p99 -3%/+3%, product of means); lowest level median 2.0e-8 kg/kg (~24 ug/m3), high for remote areas, consistent with the suspected overestimate of the CAM PM2.5 size cut (caveat above). Resolved (caveat to be documented). DECISION (PM size cut): keep the number-median cut (same formulation as the CAM PM25 diagnostic, for consistency with CAM/CESM); it overestimates the mass below the cut (mass median diameter = Dn*exp(3 ln^2 sigma); geometric, not aerodynamic, diameter): to be documented in the CMOR comment.

### `aerosol.o3.tmax-h2m-hxy-u`

- **CMIP6 name:** sfo3max
- **Long name:** Daily Maximum O3 Volume Mixing Ratio near-surface
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** DECISION: DISCARD. Ozone is prescribed (monthly CMIP7 dataset interpolated in time): no diurnal cycle, the daily maximum of near-surface ozone is not a model-simulated quantity.

### `aerosol.od550bb.tavg-u-hxy-u`

- **CMIP6 name:** od550bb
- **Long name:** Aerosol Optical Depth at 550nm Due to Biomass Burning
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `aerosol.od550bc.tavg-u-hxy-u`

- **CMIP6 name:** od550bc
- **Long name:** Black Carbon Optical Thickness at 550nm
- **CAM fields:** `AODBCdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.od550dust.tavg-u-hxy-u`

- **CMIP6 name:** od550dust
- **Long name:** Dust Optical Thickness at 550nm
- **CAM fields:** `AODDUSTdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.od550no3.tavg-u-hxy-u`

- **CMIP6 name:** od550no3
- **Long name:** Nitrate Aerosol Optical Depth at 550nm
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** No nitrate aerosol in MAM4.

### `aerosol.od550oa.tavg-u-hxy-u`

- **CMIP6 name:** od550oa
- **Long name:** Total Organic Aerosol Optical Depth at 550nm
- **CAM fields:** `AODPOMdn, AODSOAdn`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.od550so4.tavg-u-hxy-u`

- **CMIP6 name:** od550so4
- **Long name:** Sulfate Aerosol Optical Depth at 550nm
- **CAM fields:** `AODSO4dn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.od550soa.tavg-u-hxy-u`

- **CMIP6 name:** od550soa
- **Long name:** Particulate Organic Aerosol Optical Depth at 550nm
- **CAM fields:** `AODSOAdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.od550ss.tavg-u-hxy-u`

- **CMIP6 name:** od550ss
- **Long name:** Sea-Salt Aerosol Optical Depth at 550nm
- **CAM fields:** `AODSSdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `aerosol.sfpm1.tavg-h2m-hxy-u`

- **CMIP6 name:** sfpm1
- **Long name:** Near-surface PM1.0 Mixing Ratio
- **CAM fields:** `SFPM1`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** ok
- **Notes:** NEW online field (modal_aero_wateruptake.F90): ambient (dry + water) aerosol mass mixing ratio at the lowest model level below 1 um, same formulation as SFPM25 (erf size cut on the wet number-median diameter of each MAM4 mode; tends to overestimate the mass below the cut). The DR accepts the lowest model level as best estimate of the near-surface value. (previously DISCARD: Only PM2.5 diagnostic.) TEST 1970-01: SFPM1 <= SFPM25 <= SFPM10 everywhere; global mean SFPM1/SFPM25/SFPM10 = 1.3e-8/4.9e-8/1.0e-7 kg/kg; median SFPM1/SFPM25 = 0.25. Possible improvement: size cut on the volume (mass) median diameter Dn*exp(3 ln^2 sigma) instead of the number median, which overestimates the mass below the cut (especially for dust and sea salt). DECISION (PM size cut): keep the number-median cut (same formulation as the CAM PM25 diagnostic, for consistency with CAM/CESM); it overestimates the mass below the cut (mass median diameter = Dn*exp(3 ln^2 sigma); geometric, not aerodynamic, diameter): to be documented in the CMOR comment.

### `aerosol.sfpm10.tavg-h2m-hxy-u`

- **CMIP6 name:** sfpm10
- **Long name:** Near-surface PM10 Mixing Ratio
- **CAM fields:** `SFPM10`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** ok
- **Notes:** NEW online field (modal_aero_wateruptake.F90): as SFPM1 with a 10 um cut. Coarse dust and sea-salt modes can have a substantial mass above 10 um: quality depends on the coarse-mode representation. Note: the DR also requests a 3D PM10 mass mixing ratio on model levels (sfpm10.tavg-al-hxy-u, mon, High for amip), not in this table. (previously DISCARD: Only PM2.5 diagnostic.) TEST 1970-01: median SFPM10/SFPM25 = 1.8; ocean mean SFPM10 > land (wet sea salt); largest ratio 6.5 in the Arctic Ocean; monthly-mean maxima ~1e4 ug/m3 (indicative, ambient, number-median cut). DECISION (PM size cut): keep the number-median cut (same formulation as the CAM PM25 diagnostic, for consistency with CAM/CESM); it overestimates the mass below the cut (mass median diameter = Dn*exp(3 ln^2 sigma); geometric, not aerodynamic, diameter): to be documented in the CMOR comment.

### `aerosol.sfpm25.tavg-h2m-hxy-u`

- **CMIP6 name:** sfpm25
- **Long name:** Near-surface PM2.5 Mixing Ratio
- **CAM fields:** `SFPM25`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online 2D field SFPM25 (modal_aero_wateruptake.F90): PM2.5 ambient (wet) mass mixing ratio at the lowest model level (AerChemMIP best estimate) = sum over modes of (dry mass maer + aerosol water qaerwat) times mass fraction below 2.5 um computed on the wet diameter, same formulation as PM25 (same caveat as mmrpm2p5). Ambient conditions of the lowest model level: document instead of the relative_humidity/air_temperature scalar coordinates. TEST (amip 1970-01): ambient/dry ratio median 2.0 (ocean 2.1, land 1.2); 857 points slightly below dry (min -3.7%, deserts: wet growth moves mass above 2.5 um), as expected; ambient median 48 ug/m3, max 4252 ug/m3 (dust). Resolved (same size-cut caveat as mmrpm2p5). DECISION (PM size cut): keep the number-median cut (same formulation as the CAM PM25 diagnostic, for consistency with CAM/CESM); it overestimates the mass below the cut (mass median diameter = Dn*exp(3 ln^2 sigma); geometric, not aerodynamic, diameter): to be documented in the CMOR comment.

### `aerosol.toz.tavg-u-hxy-u`

- **CMIP6 name:** toz
- **Long name:** Total Column Ozone
- **CAM fields:** `TOZ`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online 2D field TOZ (prescribed_ozone.F90): column of the prescribed ozone, sum(mmr*pdeldry)/g converted kg/m2 -> mol/m2 -> DU -> m (1 DU = 1e-5 m), every time step; DR units m. Avoids daily 3D ozone (toz requested daily and monthly). Ozone is prescribed (climatology/forcing interpolated in time). TEST (amip 1970-01): global mean 289 DU (min 238, max 398); tropics 253, 30-60N 349, 60-90N 372, 60-90S 313 DU: plausible January distribution. Resolved.

## Realm: atmos

### `atmos.areacella.ti-u-hxy-u`

- **CMIP6 name:** areacella
- **Long name:** Grid-Cell Area for Atmospheric Grid Variables
- **CAM fields:** `AREA`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok

### `atmos.cl.tavg-al-hxy-u`

- **CMIP6 name:** cl
- **Long name:** Percentage Cloud Cover
- **CAM fields:** `CLOUD, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID).

### `atmos.cli.tavg-al-hxy-u`

- **CMIP6 name:** cli
- **Long name:** Mass Fraction of Cloud Ice
- **CAM fields:** `CLITOT, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Sum: stratiform + deep convective (conv_water_in_rad=1) + radiatively active snow (PUMAS qsout). Option: single online field (CLITOT) to avoid 3 extra 3D fields. Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID). DECISION: online field CLITOT (conv_water.F90, conv_water_4rad, every physics step) = (CLDICE + GCIMRDP + GCIMRSH + ICSWP*CLDFSNOW*g/pdel) / (1 + total condensate), i.e. grid-mean water seen by radiation (stratiform incl. condensate detrained by ZM, verified in clubb_intr.F90; ZM in-plume water from ICWMRDP x DP_FRAC, phase split with the stratiform ice fraction as in radiation) referred to the mass of air including all water phases as in the DR comment (state%q are wet mixing ratios relative to dry air + vapour; condensate = CLDLIQ + CLDICE + RAINQM + SNOWQM + GRAUQM). Rain and graupel excluded (not in radiation). PS only for the hybrid formula terms (with SE the true pressure is PMID). TEST 1970-01: first version used the QSNOW pbuf field, which exists only with SILHS: snow was missing (CLITOT/reference = 0.25, QSNOW = 75% of the reference ice). FIX: snow seen by radiation, ICSWP*CLDFSNOW*g/pdel (pbuf fields set by PUMAS before radiation in tphysac); equals QSNOW (qsout) where CLDFSNOW >= 1e-4. CLWTOT test OK (median relative difference -7.5e-5, sampling within the time step). ACCESSORY OUTPUT (not part of the mapping): save CLDICE (and optionally QSNOW, to separate snow from convective ice) monthly, to recover the original stratiform field exactly and the added part (convective + snow) by difference, for comparisons with previous CMIP (check how CESM2 defined cli/clw for CMIP6). Reconstruction from the added components instead (e.g. CLITOT - QSNOW) is inaccurate for ice: CLDICE is only ~21% of CLITOT (Jan 1970), GCIMRDP ~4%, and QSNOW differs from the radiative snow. TEST after fix (1970-01): CLITOT / (CLDICE + GCIMRDP + GCIMRSH + QSNOW)/(1+cond) sum ratio 1.011, median relative difference -0.3%, p01/p99 -26%/+17%. Expected: CLITOT uses the snow of the last macro/micro substep (pbuf ICSWP, CLDFSNOW, the values used by radiation), while the history field QSNOW averages the outfld calls of all substeps; CLITOT also excludes snow where PUMAS sets CLDFSNOW = 0 (ice-only stratiform cloud without convection), as radiation does. Components unchanged (diagnostic only, no feedback). Status: verified.

### `atmos.clivi.tavg-u-hxy-u`

- **CMIP6 name:** clivi
- **Long name:** Ice Water Path
- **CAM fields:** `TGCLDIWP, TMSNOWQM`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** TGCLDIWP (incl. deep convective ice) + snow burden (radiation uses ICSWP*CLDFSNOW from PUMAS qsout; small differences).

### `atmos.clt.tavg-u-hxy-lnd`

- **CMIP6 name:** clt
- **Long name:** Total Cloud Cover Percentage
- **CAM fields:** `CLDTOT, LANDFRAC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** CLDTOT: cldsav (cloud_cover_diags.F90) on CLOUD = min(ast + deepcu, 1) (stratiform incl. shallow + deep convective), maximum-random overlap with the radiation regions, clouds between ~50 and 1200 hPa, sampled on radiation time steps. Fraction to %. Mean where land: value = CLDTOT, set to missing where LANDFRAC = 0.

### `atmos.clt.tavg-u-hxy-u`

- **CMIP6 name:** clt
- **Long name:** Total Cloud Cover Percentage
- **CAM fields:** `CLDTOT`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** CLDTOT: cldsav (cloud_cover_diags.F90) on CLOUD = min(ast + deepcu, 1) (stratiform incl. shallow + deep convective), maximum-random overlap with the radiation regions, clouds between ~50 and 1200 hPa, sampled on radiation time steps. Fraction to %. TEST (amip 1970-01): global mean 0.73, plausible pattern (near-overcast Southern Ocean/Arctic/Maritime Continent, clear subtropical highs and deserts).

### `atmos.clw.tavg-al-hxy-u`

- **CMIP6 name:** clw
- **Long name:** Mass Fraction of Cloud Liquid Water
- **CAM fields:** `CLWTOT, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Sum: stratiform + deep convective liquid; rain not radiatively active. Option: online CLWTOT. Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID). DECISION: online field CLWTOT (conv_water.F90, conv_water_4rad, every physics step) = (CLDLIQ + GCLMRDP + GCLMRSH) / (1 + total condensate), i.e. grid-mean water seen by radiation (stratiform incl. condensate detrained by ZM, verified in clubb_intr.F90; ZM in-plume water from ICWMRDP x DP_FRAC, phase split with the stratiform ice fraction as in radiation) referred to the mass of air including all water phases as in the DR comment (state%q are wet mixing ratios relative to dry air + vapour; condensate = CLDLIQ + CLDICE + RAINQM + SNOWQM + GRAUQM). Rain and graupel excluded (not in radiation). PS only for the hybrid formula terms (with SE the true pressure is PMID). ACCESSORY OUTPUT (not part of the mapping): save CLDLIQ monthly, to recover the original stratiform field exactly and the added part (convective + snow) by difference, for comparisons with previous CMIP (check how CESM2 defined cli/clw for CMIP6). Reconstruction from the added components instead (e.g. CLITOT - QSNOW) is inaccurate for ice: CLDICE is only ~21% of CLITOT (Jan 1970), GCIMRDP ~4%, and QSNOW differs from the radiative snow.

### `atmos.clwvi.tavg-u-hxy-u`

- **CMIP6 name:** clwvi
- **Long name:** Condensed Water Path
- **CAM fields:** `TGCLDCWP, TMSNOWQM`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Condensed (liquid + ice) water path + radiatively active snow.

### `atmos.evspsbl.tavg-u-hxy-lnd`

- **CMIP6 name:** evspsbl
- **Long name:** Evaporation Including Sublimation and Transpiration
- **CAM fields:** `QFLX, LANDFRAC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** QFLX is the surface water flux (kg m-2 s-1); mean where land.

### `atmos.evspsbl.tavg-u-hxy-u`

- **CMIP6 name:** evspsbl
- **Long name:** Evaporation Including Sublimation and Transpiration
- **CAM fields:** `QFLX`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** QFLX is the surface water flux (kg m-2 s-1); avoids LHFLX/latent heat conversion.

### `atmos.hfls.tavg-u-hxy-u`

- **CMIP6 name:** hfls
- **Long name:** Surface Upward Latent Heat Flux
- **CAM fields:** `LHFLX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** LHFLX = cam_in%lhf from the coupler (includes sublimation), positive up as in DR.

### `atmos.hfss.tavg-u-hxy-u`

- **CMIP6 name:** hfss
- **Long name:** Surface Upward Sensible Heat Flux
- **CAM fields:** `SHFLX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** SHFLX, positive up as in DR.

### `atmos.hur.tavg-p19-hxy-air`

- **CMIP6 name:** hur
- **Long name:** Relative Humidity
- **CAM fields:** `RHCFMIP, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.hur.tavg-p19-hxy-u`

- **CMIP6 name:** hur
- **Long name:** Relative Humidity
- **CAM fields:** `RHCFMIP, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: treated as "where air" like the other plev variables (mask where plev > PS, no extrapolation), although DR cell_methods lack "where air" (kept CMIP6 "time: mean", possibly an oversight). Interpolate offline with PMID.

### `atmos.hurs.tavg-h2m-hxy-u`

- **CMIP6 name:** hurs
- **Long name:** Near-Surface Relative Humidity
- **CAM fields:** `RHCFMIPHT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Custom field. NOTE: in cam_diagnostics.F90 RHCFMIPHT/MN/MX are registered with units "fraction" but the values are in percent (ftem = q/qs*100): fix the addfld units; DR hurs is in %, no conversion needed.

### `atmos.hurs.tmax-h2m-hxy-u`

- **CMIP6 name:** hursmax
- **Long name:** Daily Maximum Near-Surface Relative Humidity
- **CAM fields:** `RHCFMIPHTMX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Custom field. NOTE: in cam_diagnostics.F90 RHCFMIPHT/MN/MX are registered with units "fraction" but the values are in percent (ftem = q/qs*100): fix the addfld units; DR hurs is in %, no conversion needed.

### `atmos.hurs.tmin-h2m-hxy-u`

- **CMIP6 name:** hursmin
- **Long name:** Daily Minimum Near-Surface Relative Humidity
- **CAM fields:** `RHCFMIPHTMN`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Custom field. NOTE: in cam_diagnostics.F90 RHCFMIPHT/MN/MX are registered with units "fraction" but the values are in percent (ftem = q/qs*100): fix the addfld units; DR hurs is in %, no conversion needed.

### `atmos.hurs.tpt-h2m-hxy-u`

- **CMIP6 name:** hurs
- **Long name:** Near-Surface Relative Humidity
- **CAM fields:** `RHCFMIPHT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Custom field, instantaneous. NOTE: in cam_diagnostics.F90 RHCFMIPHT/MN/MX are registered with units "fraction" but the values are in percent (ftem = q/qs*100): fix the addfld units; DR hurs is in %, no conversion needed.

### `atmos.hus.tavg-p19-hxy-u`

- **CMIP6 name:** hus
- **Long name:** Specific Humidity
- **CAM fields:** `Q, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: treated as "where air" like the other plev variables (mask where plev > PS, no extrapolation), although DR cell_methods lack "where air" (kept CMIP6 "time: mean", possibly an oversight). Interpolate offline with PMID.

### `atmos.hus.tpt-al-hxy-u`

- **CMIP6 name:** hus
- **Long name:** Specific Humidity
- **CAM fields:** `Q, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID).

### `atmos.huss.tavg-h2m-hxy-u`

- **CMIP6 name:** huss
- **Long name:** Near-Surface Specific Humidity
- **CAM fields:** `QREFHT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.huss.tpt-h2m-hxy-u`

- **CMIP6 name:** huss
- **Long name:** Near-Surface Specific Humidity
- **CAM fields:** `QREFHT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.pfull.tavg-al-hxy-u`

- **CMIP6 name:** pfull
- **Long name:** Pressure at Model Full-Levels
- **CAM fields:** `PMID`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** SE: PMID is not hyam*P0 + hybm*PS (errors up to 2.5 hPa), so PMID is output directly.

### `atmos.pr.tavg-u-hxy-u`

- **CMIP6 name:** pr
- **Long name:** Precipitation
- **CAM fields:** `PRECT`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** m/s to kg m-2 s-1.

### `atmos.prc.tavg-u-hxy-u`

- **CMIP6 name:** prc
- **Long name:** Convective Precipitation
- **CAM fields:** `PRECC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DR: liquid + solid; PRECC is convective precipitation (liq + ice).

### `atmos.prsn.tavg-u-hxy-u`

- **CMIP6 name:** prsn
- **Long name:** Snowfall Flux
- **CAM fields:** `PRECSC, PRECSL`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok

### `atmos.prw.tavg-u-hxy-u`

- **CMIP6 name:** prw
- **Long name:** Water Vapor Path
- **CAM fields:** `TMQ`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** TMQ = sum(Q*pdel/g) with Q = water vapour only (cam_diagnostics.F90): matches DR (water vapour only).

### `atmos.ps.tavg-u-hxy-u`

- **CMIP6 name:** ps
- **Long name:** Surface Air Pressure
- **CAM fields:** `PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.ps.tpt-u-hxy-u`

- **CMIP6 name:** ps
- **Long name:** Surface Air Pressure
- **CAM fields:** `PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.psl.tavg-u-hxy-u`

- **CMIP6 name:** psl
- **Long name:** Sea Level Pressure
- **CAM fields:** `PSL`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** cpslec.F90: ECMWF formulation (NCAR NT-396).

### `atmos.psl.tpt-u-hxy-u`

- **CMIP6 name:** psl
- **Long name:** Sea Level Pressure
- **CAM fields:** `PSL`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.rlds.tavg-u-hxy-u`

- **CMIP6 name:** rlds
- **Long name:** Surface Downwelling Longwave Radiation
- **CAM fields:** `FLDS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.rldscs.tavg-u-hxy-u`

- **CMIP6 name:** rldscs
- **Long name:** Surface Downwelling Clear-Sky Longwave Radiation
- **CAM fields:** `FLDSC`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.rls.tavg-u-hxy-u`

- **CMIP6 name:** rls
- **Long name:** Net Longwave Surface Radiation
- **CAM fields:** `FLNS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** rls is positive down (net downward LW): rls = -FLNS.

### `atmos.rlus.tavg-u-hxy-u`

- **CMIP6 name:** rlus
- **Long name:** Surface Upwelling Longwave Radiation
- **CAM fields:** `FLNS, FLDS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** FLNS + FLDS.

### `atmos.rlut.tavg-u-hxy-u`

- **CMIP6 name:** rlut
- **Long name:** TOA Outgoing Longwave Radiation
- **CAM fields:** `FLUTOA`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new field FLUTOA = uflx(:,rrtmg_levs+1) (radlw.F90/radiation.F90), LW upward flux at the top of the RRTMG extra layer (TOA), as DR asks; FLUT is at the top of the model. TEST (amip 1970-01): FLUTOA - FLUT global mean 0.16 W/m2 (0.003-0.27, max over Antarctica); global net balance TOM 10.56, hybrid FSNTOA-FLUT 10.90, consistent TOA FSNTOA-FLUTOA 10.74 W/m2.

### `atmos.rlutcs.tavg-u-hxy-u`

- **CMIP6 name:** rlutcs
- **Long name:** TOA Outgoing Clear-Sky Longwave Radiation
- **CAM fields:** `FLUTOAC`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new field FLUTOAC = uflxc(:,rrtmg_levs+1), clear-sky LW upward flux at TOA. TEST (amip 1970-01): FLUTOAC - FLUTC global mean 0.16 W/m2 (0.003-0.27).

### `atmos.rsds.tavg-u-hxy-u`

- **CMIP6 name:** rsds
- **Long name:** Surface Downwelling Shortwave Radiation
- **CAM fields:** `FSDS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.rsdscs.tavg-u-hxy-u`

- **CMIP6 name:** rsdscs
- **Long name:** Surface Downwelling Clear-Sky Shortwave Radiation
- **CAM fields:** `FSDSC`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.rsdt.tavg-u-hxy-u`

- **CMIP6 name:** rsdt
- **Long name:** TOA Incident Shortwave Radiation
- **CAM fields:** `SOLIN`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Direct field; equal to FSNTOA + FSUTOA.

### `atmos.rss.tavg-u-hxy-u`

- **CMIP6 name:** rss
- **Long name:** Net Shortwave Surface Radiation
- **CAM fields:** `FSNS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** FSNS (net downward SW), positive down as in DR.

### `atmos.rsus.tavg-u-hxy-u`

- **CMIP6 name:** rsus
- **Long name:** Surface Upwelling Shortwave Radiation
- **CAM fields:** `FSDS, FSNS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** FSDS - FSNS.

### `atmos.rsuscs.tavg-u-hxy-u`

- **CMIP6 name:** rsuscs
- **Long name:** Surface Upwelling Clear-Sky Shortwave Radiation
- **CAM fields:** `FSDSC, FSNSC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** FSDSC - FSNSC.

### `atmos.rsut.tavg-u-hxy-u`

- **CMIP6 name:** rsut
- **Long name:** TOA Outgoing Shortwave Radiation
- **CAM fields:** `FSUTOA`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** FSUTOA is at the top of the RRTMG extra layer (TOA): matches DR.

### `atmos.rsutcs.tavg-u-hxy-u`

- **CMIP6 name:** rsutcs
- **Long name:** TOA Outgoing Clear-Sky Shortwave Radiation
- **CAM fields:** `SOLIN, FSNTOAC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** SOLIN - FSNTOAC, both at TOA (equivalent to FSUTOA + SWCF).

### `atmos.sfcWind.tavg-h10m-hxy-u`

- **CMIP6 name:** sfcWind
- **Long name:** Near-Surface Wind Speed
- **CAM fields:** `U10`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified).

### `atmos.sfcWind.tmax-h10m-hxy-u`

- **CMIP6 name:** sfcWindmax
- **Long name:** Daily Maximum Near-Surface Wind Speed
- **CAM fields:** `U10`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** ok
- **Notes:** PROPOSED: U10 with avg flag X on the daily tape (fincl U10:X): daily max of time-step values, no code change. WSPDSRFMX is at the lowest model level. VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified).

### `atmos.sfcWind.tmaxavg-h10m-hxy-u`

- **CMIP6 name:** sfcWindmax
- **Long name:** Daily Maximum Near-Surface Wind Speed
- **CAM fields:** `U10`
- **Reprocess:** True
- **Confidence:** medium
- **Status:** ok
- **Notes:** PROPOSED: monthly mean of the daily U10:X (offline, exact). WSPDSRFMX is at the lowest model level. VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified).

### `atmos.sftlf.ti-u-hxy-u`

- **CMIP6 name:** sftlf
- **Long name:** Percentage of the Grid Cell Occupied by Land (Including Lakes)
- **CAM fields:** `LANDFRAC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Fraction to %.

### `atmos.ta.tavg-850hPa-hxy-air`

- **CMIP6 name:** ta850
- **Long name:** Air Temperature
- **CAM fields:** `T850air`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air". DECISION: derived offline from the daily 3D field (needed anyway for plev19 daily), consistent with the plev19 product; online masked single-level field would only improve accuracy, not save 3D output. DECISION: online 2D field T850air (cam_diagnostics.F90: same interpolation as T850, ECMWF extrapolation between the lowest model level and the surface, fillvalue where 850 hPa is below the surface) in the daily mean stream: exact "where air" time mean (only above-ground time steps are averaged, flag_xyfill). CAM-style fallback (no mask, extrapolated below ground): also save T850 in the same stream (2D, ~0.07 GB/yr).

### `atmos.ta.tavg-p19-hxy-air`

- **CMIP6 name:** ta
- **Long name:** Air Temperature
- **CAM fields:** `T, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.ta.tavg-p39-hy-air`

- **CMIP6 name:** ta
- **Long name:** Zonal Mean Air Temperature
- **CAM fields:** `T, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.ta.tpt-al-hxy-u`

- **CMIP6 name:** ta
- **Long name:** Air Temperature
- **CAM fields:** `T, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID).

### `atmos.ta.tpt-p3-hxy-air`

- **CMIP6 name:** ta
- **Long name:** Air Temperature
- **CAM fields:** `T850air, T500air, T250air`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous: masking with instantaneous PS is exact. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact. DECISION (applied): use the new online 2D fields T850air, T500air, T250air (cam_diagnostics.F90: same interpolation as T850/T500/T250, fillvalue where p > PS, "where air"), requested as instantaneous (:I) in the 6-hourly stream, instead of the 3D T + PMID: the 6-hourly instantaneous stream drops from ~67 to ~3.7 GB/yr (whole table ~149 -> ~86 GB/yr, uncompressed). TEST (1970-01-02, hourly instantaneous): mask exactly p > PS (850 hPa: 4.37% of columns missing, 0 mismatches); identical to the CAM unmasked fields where defined; offline linear interpolation of the 3D fields agrees within single-precision rounding (max |d| 7e-5 K for T, 2e-5 m/s for U, V). Fields verified. Request as instantaneous in the 6-hourly stream (T850air:I, T500air:I, T250air:I). CAM-style fallback (no mask, below ground T extrapolated / U, V lowest-level value): also save T850:I, T500:I, T250:I in the same 6-hourly stream (~0.85 GB/yr for the 3 fields). Offline reconstruction of the CAM-style values below ground from bottom-level fields is not exact (no lowest-level pressure field; UBOT/VBOT written at a different point of the time step) and not possible for time means.

### `atmos.tas.tavg-h2m-hxy-u`

- **CMIP6 name:** tas
- **Long name:** Near-Surface Air Temperature
- **CAM fields:** `TREFHT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.tas.tmax-h2m-hxy-u`

- **CMIP6 name:** tasmax
- **Long name:** Daily Maximum Near-Surface Air Temperature
- **CAM fields:** `TREFHTMX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** TREFHTMX (flag X) on the daily tape: daily max of time-step values.

### `atmos.tas.tmaxavg-h2m-hxy-u`

- **CMIP6 name:** tasmax
- **Long name:** Daily Maximum Near-Surface Air Temperature
- **CAM fields:** `TREFMXAV`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** TREFMXAV: online average of TREFHT daily maximum.

### `atmos.tas.tmin-h2m-hxy-u`

- **CMIP6 name:** tasmin
- **Long name:** Daily Minimum Near-Surface Air Temperature
- **CAM fields:** `TREFHTMN`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** TREFHTMN (flag M) on the daily tape: daily min of time-step values.

### `atmos.tas.tminavg-h2m-hxy-u`

- **CMIP6 name:** tasmin
- **Long name:** Daily Minimum Near-Surface Air Temperature
- **CAM fields:** `TREFMNAV`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** TREFMNAV: online average of TREFHT daily minimum.

### `atmos.tas.tpt-h2m-hxy-u`

- **CMIP6 name:** tas
- **Long name:** Near-Surface Air Temperature
- **CAM fields:** `TREFHT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.tauu.tavg-u-hxy-u`

- **CMIP6 name:** tauu
- **Long name:** Surface Downward Eastward Wind Stress
- **CAM fields:** `TAUX, TAUBLJX`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** SIGN VERIFIED: tauu = -TAUX (atm_import_export.F90: cam_in%wsx = -Faxx_taux, stress on the atmosphere; DR positive down). TAUBLJX (Beljaars turbulent orographic form drag, do_beljaars active, TMS not active) has the same sign convention (added to wsx in vertical_diffusion.F90). DECISION: save both; choose in post-processing/CMORization between -TAUX (turbulent surface stress only) and -(TAUX + TAUBLJX) (total stress). They coincide over ocean. RESOLVED: both fields saved; choice made in post-processing.

### `atmos.tauv.tavg-u-hxy-u`

- **CMIP6 name:** tauv
- **Long name:** Surface Downward Northward Wind Stress
- **CAM fields:** `TAUY, TAUBLJY`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** SIGN VERIFIED: tauv = -TAUY (atm_import_export.F90: cam_in%wsy = -Faxx_tauy, stress on the atmosphere; DR positive down). TAUBLJY (Beljaars turbulent orographic form drag, do_beljaars active, TMS not active) has the same sign convention (added to wsy in vertical_diffusion.F90). DECISION: save both; choose in post-processing/CMORization between -TAUY (turbulent surface stress only) and -(TAUY + TAUBLJY) (total stress). They coincide over ocean. RESOLVED: both fields saved; choice made in post-processing.

### `atmos.ts.tavg-u-hxy-u`

- **CMIP6 name:** ts
- **Long name:** Surface Temperature
- **CAM fields:** `TS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** TS: radiative surface temperature from the coupler (in AMIP over ocean: prescribed SST).

### `atmos.ts.tpt-u-hxy-u`

- **CMIP6 name:** ts
- **Long name:** Surface Temperature
- **CAM fields:** `TS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok

### `atmos.ua.tavg-p19-hxy-air`

- **CMIP6 name:** ua
- **Long name:** Eastward Wind
- **CAM fields:** `U, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.ua.tpt-al-hxy-u`

- **CMIP6 name:** ua
- **Long name:** Eastward Wind
- **CAM fields:** `U, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** 6hrLev instantaneous on model levels (also the usual lateral boundary conditions for regional models, e.g. CORDEX: requirements not verified). Keep. NOTE: rv850 is not in this CSV; if added, the 6hr-mean version would need online masked U850/V850 ("where air"), the instantaneous one can be derived from these fields. Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID).

### `atmos.ua.tpt-p3-hxy-air`

- **CMIP6 name:** ua
- **Long name:** Eastward Wind
- **CAM fields:** `U850air, U500air, U250air`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous: masking exact. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact. DECISION (applied): use the new online 2D fields U850air, U500air, U250air (cam_diagnostics.F90: same interpolation as U850/U500/U250, fillvalue where p > PS, "where air"), requested as instantaneous (:I) in the 6-hourly stream, instead of the 3D U + PMID: the 6-hourly instantaneous stream drops from ~67 to ~3.7 GB/yr (whole table ~149 -> ~86 GB/yr, uncompressed). TEST (1970-01-02, hourly instantaneous): mask exactly p > PS (850 hPa: 4.37% of columns missing, 0 mismatches); identical to the CAM unmasked fields where defined; offline linear interpolation of the 3D fields agrees within single-precision rounding (max |d| 7e-5 K for T, 2e-5 m/s for U, V). Fields verified. Request as instantaneous in the 6-hourly stream (U850air:I, U500air:I, U250air:I). CAM-style fallback (no mask, below ground T extrapolated / U, V lowest-level value): also save U850:I, U500:I, U250:I in the same 6-hourly stream (~0.85 GB/yr for the 3 fields). Offline reconstruction of the CAM-style values below ground from bottom-level fields is not exact (no lowest-level pressure field; UBOT/VBOT written at a different point of the time step) and not possible for time means.

### `atmos.uas.tavg-h10m-hxy-u`

- **CMIP6 name:** uas
- **Long name:** Eastward Near-Surface Wind
- **CAM fields:** `UAS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field UAS = U10*UBOT/sqrt(UBOT^2+VBOT^2) computed every time step in diag_surf (cam_diagnostics.F90; 0 if lowest-level wind < 1e-6 m/s). U10 is the coupler field Sx_u10, a speed from Monin-Obukhov similarity driven by the lowest-level wind speed, so the lowest-level direction is consistent (component code not verified). TEST (1 month, monthly means): no consistency violation (|mean vector| <= mean U10 everywhere); naive offline reconstruction from means would give rms error 2.6 m/s, up to 10 m/s in storm tracks. Instantaneous identity test still to be done. VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified). TEST (hourly instantaneous): |(UAS,VAS)| = U10 to 1e-7 relative. Angles up to 180 deg with respect to the output UBOT/VBOT: UAS/VAS use the state at the end of tphysbc (diag_surf, the state exported to the coupler that produced U10), while UBOT/VBOT are written later in tphysac (diag_phys_writeout), so at weak wind the two directions can differ; the UAS/VAS direction is the consistent one. U10/|Vbot| median 1.01, large at weak wind (0.5 m/s minimum in the flux scheme). Angle to output UBOT/VBOT decreases with wind speed (median 12 deg below 0.5 m/s, 1.5 deg above 5 m/s; p99 15 deg above 5 m/s), consistent with the different points of the time step (CLUBB applies momentum tendencies to the lowest level in tphysac before UBOT is written).

### `atmos.uas.tpt-h10m-hxy-u`

- **CMIP6 name:** uas
- **Long name:** Eastward Near-Surface Wind
- **CAM fields:** `UAS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field UAS = U10*UBOT/sqrt(UBOT^2+VBOT^2) computed every time step in diag_surf (cam_diagnostics.F90; 0 if lowest-level wind < 1e-6 m/s). U10 is the coupler field Sx_u10, a speed from Monin-Obukhov similarity driven by the lowest-level wind speed, so the lowest-level direction is consistent (component code not verified). TEST (1 month, monthly means): no consistency violation (|mean vector| <= mean U10 everywhere); naive offline reconstruction from means would give rms error 2.6 m/s, up to 10 m/s in storm tracks. Instantaneous identity test still to be done. VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified).

### `atmos.va.tavg-p19-hxy-air`

- **CMIP6 name:** va
- **Long name:** Northward Wind
- **CAM fields:** `V, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.va.tpt-al-hxy-u`

- **CMIP6 name:** va
- **Long name:** Northward Wind
- **CAM fields:** `V, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** 6hrLev instantaneous on model levels (also the usual lateral boundary conditions for regional models, e.g. CORDEX: requirements not verified). Keep. NOTE: rv850 is not in this CSV; if added, the 6hr-mean version would need online masked U850/V850 ("where air"), the instantaneous one can be derived from these fields. Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID).

### `atmos.va.tpt-p3-hxy-air`

- **CMIP6 name:** va
- **Long name:** Northward Wind
- **CAM fields:** `V850air, V500air, V250air`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous: masking exact. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact. DECISION (applied): use the new online 2D fields V850air, V500air, V250air (cam_diagnostics.F90: same interpolation as V850/V500/V250, fillvalue where p > PS, "where air"), requested as instantaneous (:I) in the 6-hourly stream, instead of the 3D V + PMID: the 6-hourly instantaneous stream drops from ~67 to ~3.7 GB/yr (whole table ~149 -> ~86 GB/yr, uncompressed). TEST (1970-01-02, hourly instantaneous): mask exactly p > PS (850 hPa: 4.37% of columns missing, 0 mismatches); identical to the CAM unmasked fields where defined; offline linear interpolation of the 3D fields agrees within single-precision rounding (max |d| 7e-5 K for T, 2e-5 m/s for U, V). Fields verified. Request as instantaneous in the 6-hourly stream (V850air:I, V500air:I, V250air:I). CAM-style fallback (no mask, below ground T extrapolated / U, V lowest-level value): also save V850:I, V500:I, V250:I in the same 6-hourly stream (~0.85 GB/yr for the 3 fields). Offline reconstruction of the CAM-style values below ground from bottom-level fields is not exact (no lowest-level pressure field; UBOT/VBOT written at a different point of the time step) and not possible for time means.

### `atmos.vas.tavg-h10m-hxy-u`

- **CMIP6 name:** vas
- **Long name:** Northward Near-Surface Wind
- **CAM fields:** `VAS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field VAS = U10*VBOT/sqrt(UBOT^2+VBOT^2) computed every time step in diag_surf (cam_diagnostics.F90; 0 if lowest-level wind < 1e-6 m/s). U10 is the coupler field Sx_u10, a speed from Monin-Obukhov similarity driven by the lowest-level wind speed, so the lowest-level direction is consistent (component code not verified). TEST (1 month, monthly means): no consistency violation (|mean vector| <= mean U10 everywhere); naive offline reconstruction from means would give rms error 2.6 m/s, up to 10 m/s in storm tracks. Instantaneous identity test still to be done. VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified). TEST (hourly instantaneous): |(UAS,VAS)| = U10 to 1e-7 relative. Angles up to 180 deg with respect to the output UBOT/VBOT: UAS/VAS use the state at the end of tphysbc (diag_surf, the state exported to the coupler that produced U10), while UBOT/VBOT are written later in tphysac (diag_phys_writeout), so at weak wind the two directions can differ; the UAS/VAS direction is the consistent one. U10/|Vbot| median 1.01, large at weak wind (0.5 m/s minimum in the flux scheme). Angle to output UBOT/VBOT decreases with wind speed (median 12 deg below 0.5 m/s, 1.5 deg above 5 m/s; p99 15 deg above 5 m/s), consistent with the different points of the time step (CLUBB applies momentum tendencies to the lowest level in tphysac before UBOT is written).

### `atmos.vas.tpt-h10m-hxy-u`

- **CMIP6 name:** vas
- **Long name:** Northward Near-Surface Wind
- **CAM fields:** `VAS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field VAS = U10*VBOT/sqrt(UBOT^2+VBOT^2) computed every time step in diag_surf (cam_diagnostics.F90; 0 if lowest-level wind < 1e-6 m/s). U10 is the coupler field Sx_u10, a speed from Monin-Obukhov similarity driven by the lowest-level wind speed, so the lowest-level direction is consistent (component code not verified). TEST (1 month, monthly means): no consistency violation (|mean vector| <= mean U10 everywhere); naive offline reconstruction from means would give rms error 2.6 m/s, up to 10 m/s in storm tracks. Instantaneous identity test still to be done. VERIFIED in med_phases_aofluxes_mod.F90 (CESMCOUPLED): over ocean flux_atmocn (shr_flux_mod) is called with seq_flux_atmocn_minwind=0.5 m/s and the ocean currents (us=So_u, vs=So_v), and So_u10 = sqrt(duu10n). Hence U10 over ocean is floored at low wind and relative to surface currents (zero in AMIP with data ocean), while the UAS/VAS direction comes from the absolute UBOT/VBOT. VERIFIED in shr_flux_mod.F90 (flux_atmOcn): with ocn_surface_flux_scheme=0 (default, Large-Yeager) duu10n = u10n**2, the NEUTRAL 10 m wind relative to the ocean current, from vmag floored at 0.5 m/s (optionally scaled by the cold-air-outbreak modification, default off: check coldair_outbreak_mod). With scheme 1 (COARE) and 2 (UA) the 10 m wind is the actual (stability-dependent) one. Check ocn_surface_flux_scheme in the mediator log and document in the CMOR comment. Land and sea-ice parts of Sx_u10 come from CLM/CICE (not verified).

### `atmos.wap.tavg-p19-hxy-air`

- **CMIP6 name:** wap
- **Long name:** Omega (=dp/dt)
- **CAM fields:** `OMEGA, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.wap.tavg-p19-hxy-u`

- **CMIP6 name:** wap
- **Long name:** Omega (=dp/dt)
- **CAM fields:** `OMEGA, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: treated as "where air" like the other plev variables (mask where plev > PS, no extrapolation), although DR cell_methods lack "where air" (kept CMIP6 "time: mean", possibly an oversight). Interpolate offline with PMID.

### `atmos.zg.tavg-500hPa-hxy-air`

- **CMIP6 name:** zg500
- **Long name:** Geopotential Height at 500hPa
- **CAM fields:** `Z500air`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air". DECISION: derived offline from the daily 3D field (needed anyway for plev19 daily), consistent with the plev19 product; online masked single-level field would only improve accuracy, not save 3D output. DECISION: new online 2D field Z500air (cam_diagnostics.F90: same as Z500, ln(p) interpolation, ECMWF extrapolation of Z, fillvalue where 500 hPa is below the surface) in the daily mean stream: exact "where air" time mean. CAM-style fallback: also save Z500 in the same stream (2D, ~0.07 GB/yr). TEST (hourly instantaneous, 6-hourly samples): Z500air identical to Z500 where defined (max |d| = 0); offline ln(p) interpolation of Z3 agrees within single-precision rounding (max |d| 7.6e-4 m, rms 2.4e-4 m); no column below ground at 500 hPa in the sample (PS > 500 hPa everywhere at the sampled times), so the mask is not exercised for Z500air, but it is the same code verified for T850air/U850air/V850air (4.4% missing, 0 mismatches). Field verified.

### `atmos.zg.tavg-p19-hxy-air`

- **CMIP6 name:** zg
- **Long name:** Geopotential Height
- **CAM fields:** `Z3, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: interpolate offline with PMID and mask where plev > PS (no extrapolation); for time means the mask from mean PS approximates "mean where air" (accepted). CAM online single-level fields (vertinterp) extrapolate T/Z with the ECMWF method and hold U/V/OMEGA/Q at the bottom value: not "where air".

### `atmos.zg.tpt-al-hxy-u`

- **CMIP6 name:** zg
- **Long name:** Geopotential height
- **CAM fields:** `Z3, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Model levels; PS for hybrid formula terms (with SE the true pressure is pfull = PMID).

### `atmos.aod550volso4.tavg-u-hxy-u`

- **CMIP6 name:** aod550volso4
- **Long name:** Monthly Aerosol Optical Depth at 550nm Due to Stratospheric Volcanic Aerosols
- **CAM fields:** `ODVdn_VOLC_MMR`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** ok
- **Notes:** DECISION: new day-night field ODVdn_VOLC_MMR (aer_rad_props.F90, written before night columns are set to fillvalue; bulk optics are computed on all columns): consistent with area: time: mean. Volcanic AOD in the RRTMG visible band 10 (442-625 nm), not exactly 550 nm: document in the CMOR comment. ODV_VOLC_MMR is day-only. DR units 1E-09 look inconsistent (dimensionless expected): to be checked with the DR team. TEST (amip 1970-01): ODVdn_VOLC_MMR has no missing values and equals ODV_VOLC_MMR where defined, but both are exactly 0 everywhere: TO BE INVESTIGATED (prescribed_strataero with the CMIP7 UOEXETER file: single VOLC_MMR or three-mode VOLC_MMR1-3 pbuf fields; rad_climate uses N:VOLC_MMR). ROOT CAUSE FOUND: in the CMIP7 input file volcanic_strataero_CMIP_UOEXETER-CMIP-2-2-1_..._c20260710.nc "altitude" is in km (5-39.5) but "altitude_int" (layer interfaces used by tracer_data rebin) is in m (4750-39750) although labelled km: all model layers fall below the first interface and VOLC_MMR is zero everywhere, i.e. no stratospheric volcanic aerosol in the runs (affects the radiative forcing, not only the diagnostic). The lowest 6 levels (5-7.5 km) are NaN. Fix the file (altitude_int/1000, NaN -> 0) and report it to the file provider; then repeat the test. TEST after fixing the input file (altitude_int in km, NaN -> 0): ODVdn_VOLC_MMR global mean 0.0077, max 0.017 (background 1970), no missing values, mean relative difference to the day-only ODV_VOLC_MMR 0.5% (night sampling). Remaining: report the file bug to the provider; clarify whether rmode is an effective radius (CAM uses it as geometric radius of a lognormal with sigma=1.6: factor 1.74). RADIUS (literature + code): the CMIP7 optical property dataset (Aubry et al., GMD 19, 3725-3756, 2026) is built on effective radius (EVA_H v2 Mie look-up tables vs effective radius; effective radius derived from the 525/1020 nm extinction ratio; size distribution unimodal lognormal sigma_g=1.8 for r_eff<0.4 um, bimodal 1.8/1.25 for larger); H2SO4 number density from volume density with 75% sulfate (consistent with CAM 4/3*98 conversion). CAM (aer_rad_props.F90) interprets VOLC_RAD_GEOM as the geometric mean radius of the volc_camRRTMG_byradius_sigma1.6 tables. Hence rmode in the CAM file is very likely an effective radius used as geometric radius: to preserve r_eff with the CAM sigma=1.6 tables, r_geom = r_eff/exp(2.5 ln^2 1.6) = r_eff/1.74. Residual inconsistency: distribution width 1.6 (CAM) vs 1.8 (dataset). To be confirmed with the CAM file producer. TEST vs CMIP7 dataset (UOEXETER-CMIP-2-2-1 ext at 550 nm, Jan 1970, global/90S-30S/tropics/30N-90N): CMIP7 SAOD 0.0086/0.0106/0.0059/0.0121; CAM with original rmode 0.0077/0.0091/0.0052/0.0113 (-11%); CAM with rmode/1.7372 0.0037/0.0043/0.0023/0.0057 (-57%). The original file reproduces the dataset AOD much better: keep the original rmode (only altitude_int and NaN fixes) until the file producer clarifies the radius definition and the CAM optics conventions; repeat the check in a post-Pinatubo month (e.g. 1992). TEST Jan 1992 (volcanic_vs_cmip7.py): CMIP7 SAOD 550 nm global 0.120; CAM original rmode 0.147 (+22%, RMSE 0.028), rmode/1.7372 0.180 (+50%, RMSE 0.066): original rmode closer again (both regimes). Input-only test: rmode/(3V/S) = 0.968 with w*rho = 1.275 g/cm3 (constant ratio: sad derived from rmode by the producer), i.e. rmode is an effective radius (geometric hypothesis would need w*rho = 0.76 g/cm3). OPTICS TABLE volc_camRRTMG_byradius_sigma1.6_c130724.nc: metadata say mu_samples = ln(geometric mean radius), weightpercent 75, density 1750 kg/m3, T 215 K, but the scalar sigma = 0.5878 = ln(1.8) (history: copied from rrtmg_Bi_sigma1.8/1.4 files). Mie recomputation of bext in band 10 (check_volc_table_mie.py, n = 1.43 assumed, uniform wavenumber average) does NOT match a lognormal with number-median radius = table radius (sigma 1.6 or 1.8: peak at ~0.15 um instead of ~0.26 um, values 2-3 times lower at Pinatubo sizes); it matches within ~5-15% if the table radius is the effective radius (sigma 1.6) or the volume-median radius (sigma 1.6). Hence the table radius behaves like an effective/volume radius, and passing the effective radius rmode unchanged is consistent with the table: DECISION (provisional): keep the original rmode, no /1.7372. Remaining differences vs CMIP7 (-11% 1970, +22% 1992) may come from the CAM tropopause cut (prescribed_strataero zeroes aerosol at and below the chemical tropopause; check with section D of volcanic_vs_cmip7.py and VOLC_MASS_C:A) and from different size distributions (CAM table single lognormal; dataset sigma 1.8, bimodal for large r_eff). TEST D Jan 1992 (VOLC_MASS_C snapshot from h0i): CAM/input column mass global 0.97 (tropics 0.88, i.e. ~12% cut at the tropopause; NH extratropics 1.18, probably timing of the end-of-month snapshot vs monthly input during poleward spreading); mass extinction k (AOD/mass, m2/g) CMIP7 2.49 global / 2.35 tropics, CAM original rmode 3.14 / 3.20 (+26% / +36%), rmode/1.7372 3.84 / 4.09 (+55% / +74%). The +22% AOD bias of the original rmode comes from the optics (CAM table gives a higher mass extinction than the dataset for the same radius), not from the mass. Possible causes: table width sigma 1.6 single lognormal vs dataset sigma 1.8 / bimodal (Mie estimate: about -7% at r_eff 0.47 um with sigma 1.8), refractive index and band weighting of the table. Options: accept the original rmode and document the residual bias, or build a new CAM volcanic optics table consistent with the dataset (needs H2SO4 refractive indices for all RRTMG bands). Repeat D for Jan 1970 and with VOLC_MASS_C:A. TEST D Jan 1970 (background, rmode ~0.155 um): CAM/input column mass global 0.78 (tropics 0.77, SH 0.73, NH 0.85: ~22% of the mass is below the CAM tropopause cut); k CMIP7 2.89 m2/g, CAM original 3.04 (+5%), rmode/1.7372 1.44 (-50%). AOD bias of the original rmode -18% = mass 0.78 x k 1.05. SUMMARY: with the original rmode the optics agree within ~5% in background conditions and are ~+26% too strong at Pinatubo sizes (r_eff ~0.47 um), consistent with the Mie check (table close to a sigma 1.6 lognormal in r_eff at small radii, higher at large radii; dataset sigma 1.8 / bimodal at large r_eff). Background AOD deficit comes from the tropopause cut in prescribed_strataero (design choice; whether CMIP7 recommends using the data only above the model tropopause is to be checked in the dataset documentation). DECISION: keep the original rmode. Caveat: the 1970 runs used the c20260710 input file (with altitude_int/NaN fixes), section D used c20261009.

### `atmos.bldep.tpt-u-hxy-u`

- **CMIP6 name:** bldep
- **Long name:** Boundary Layer Depth
- **CAM fields:** `PBLH`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** PBLH (m), instantaneous on the 3-hourly tape (avg flag I). Other DR bldep variants (1hr/mon means, daily max/min) are not in this list.

### `atmos.cldnvi.tavg-u-hxy-u`

- **CMIP6 name:** cldnvi
- **Long name:** Column Integrated Cloud Droplet Number
- **CAM fields:** `CDNUMC, CLDLIQTOT`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: cldnvi = mean(CDNUMC)/mean(CLDLIQTOT), missing where CLDLIQTOT = 0. DR: in-cloud column value (layers weighted by liquid cloud fraction), monthly mean weighted by liquid cloud cover seen from TOA: the weighting cancels the per-sample normalisation, so the ratio of time means is exact if both terms have the same sampling. CDNUMC = sum(nc_grid*pdel/g), grid-box mean, every microphysics step. New field CLDLIQTOT (micro_pumas_cam.F90, cam_dev), same step as CDNUMC: cldsav (max-random overlap) on liqcldf where in-cloud liquid icwmrst > 1e-7 kg/kg (liqcldf = AST is the total stratiform fraction, liquid and ice), with the overlap regions of the total cloud CLD (cldovrlap on cld_grid) as CLDTOT and radiation, so CLDLIQTOT <= CLDTOT at each step; cldsav made public in cloud_cover_diags.F90. TEST 1 (first version: liqcldf without liquid check, liquid-based regions): CLDTOT - CLDLIQTOT mean 0.009, min -0.022: CLDLIQTOT was in practice stratiform (liquid + ice) cover, negatives from different regions. Fixed; Note: CLDTOT is sampled on radiation steps, CLDLIQTOT every step. TEST 2 (after fix): CLDLIQTOT global mean 0.42 (CLDTOT 0.73; CLDLIQTOT/CLDTOT tropics 0.41, mid-latitudes 0.72, polar 0.66); 7 points with CLDLIQTOT > CLDTOT + 0.005 (max 0.008, around 30S, sampling difference: CLDTOT on radiation steps only); cldnvi median 1.9e10 m-2 (p05 3.2e9, p95 8.0e10), 191 points without liquid cloud in the month (missing). Resolved. TEST 3 (run with volcanic aerosol): 11 points with CLDLIQTOT > CLDTOT + 0.005, max 0.017, subtropical stratocumulus off Chile (sampling difference with CLDTOT, radiation steps only).

### `atmos.cltc.tavg-u-hxy-u`

- **CMIP6 name:** cltc
- **Long name:** Convective Cloud Cover Percentage
- **CAM fields:** `CLDTOTCONV`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online 2D field CLDTOTCONV (cloud_cover_diags.F90/cloud_diagnostics.F90): cldsav applied to CONCLD with the same maximum-random overlap and regions as CLDTOT, every radiation time step (CLDTOTCONV <= CLDTOT). CONCLD = deepcu in clubb_intr.F90: deep convective (ZM) cloud only, max 0.6; shallow convection is inside the CLUBB stratiform fraction and cannot be separated: document in CMOR comment. Fraction to %. TEST (amip 1970-01, monthly mean): code runs; global mean 0.058, max 0.28; pattern consistent with ZM deep convection (ITCZ, SPCZ, Maritime Continent, austral-summer continents) plus mid-latitude storm tracks and Southern Ocean (ZM active in cold-air outbreaks); visually CLDTOTCONV << CLDTOT. Pending: numerical checks CLDTOTCONV <= CLDTOT, nonzero only where FREQZM > 0. TEST 2 (numerical): CLDTOTCONV <= CLDTOT everywhere, zero where FREQZM = 0, spatial correlation with FREQZM 0.97, >= column max of mean CONCLD. Resolved.

### `atmos.co2.tavg-al-hxy-u`

- **CMIP6 name:** co2
- **Long name:** Mole Fraction of CO2
- **CAM fields:** `CO2, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** CO2 tracer (mol/mol), radiatively active (rad_climate A:CO2), transported; concentration-driven: forced by the CMIP7 flbc surface concentrations; emission-driven: emissions + land/ocean fluxes. Spatially nonuniform: report 3D (DR). Same mapping in both run types.

### `atmos.co2.tavg-p19-hxy-air`

- **CMIP6 name:** co2
- **Long name:** Mole Fraction of CO2
- **CAM fields:** `CO2, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** As co2 on model levels, interpolated offline with PMID and masked where plev > PS ("where air").

### `atmos.co2.tclm-p19-hxy-air`

- **CMIP6 name:** co2Clim
- **Long name:** Mole Fraction of CO2
- **CAM fields:** `CO2, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Climatology (12 monthly means) only for runs in which CO2 does not vary from year to year (DR), instead of co2; derived offline from the monthly means; in practice not applicable to the planned historical/scenario AMIP and emission-driven runs (possibly amip-piForcing). Experiment-dependent: to be handled when mapping per experiment.

### `atmos.co2.tclm-u-hm-u`

- **CMIP6 name:** co2massClim
- **Long name:** Total Atmospheric Mass of CO2
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** DECISION: DISCARD. DR processing note: if CO2 is spatially nonuniform, omit this field and report the mole fraction of CO2 (co2). The CAM CO2 tracer is nonuniform in both concentration-driven and emission-driven runs. (co2massClim follows co2mass.)

### `atmos.co23D.tavg-al-hxy-u`

- **CMIP6 name:** co23D
- **Long name:** 3D-Field of Transported CO2
- **CAM fields:** `CO2, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Transported CO2 tracer as mass fraction: co23D = CO2 * 44.0095/28.966 (kg/kg). In CAM it coincides with the CO2 used by radiation (A:CO2): document in the CMOR comment. DR comment says emission-driven runs, but the request list includes 50 experiments, also concentration-driven: provide wherever requested.

### `atmos.co2mass.tavg-u-hm-u`

- **CMIP6 name:** co2mass
- **Long name:** Total Atmospheric Mass of CO2
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** DECISION: DISCARD. DR processing note: if CO2 is spatially nonuniform, omit this field and report the mole fraction of CO2 (co2). The CAM CO2 tracer is nonuniform in both concentration-driven and emission-driven runs.

### `atmos.fco2all.tavg-u-hxy-u`

- **CMIP6 name:** fco2all
- **Long name:** Carbon Mass Flux into Atmosphere Due to All Emissions of CO2 from All Sources [kgC m-2 s-1]
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** discard
- **Notes:** EXPERIMENT DEPENDENCE: AMIP runs are concentration-driven (CO2 tracer forced by the flbc surface concentrations); coupled runs are emission-driven (CO2 from emissions and land/ocean fluxes). DISCARD only for the concentration-driven AMIP configuration (no CO2 surface fluxes in CAM). TO BE REVIEWED for the emission-driven coupled runs: total CO2 flux seen by the atmosphere (natural + anthropogenic). RESOLVED for AMIP (concentration-driven): DISCARD. To be revisited when the coupled emission-driven configuration is mapped.

### `atmos.fco2antt.tavg-u-hxy-u`

- **CMIP6 name:** fco2antt
- **Long name:** Carbon Mass Flux into Atmosphere Due to All Anthropogenic Emissions of CO2 [kgC m-2 s-1]
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** discard

### `atmos.fco2fos.tavg-u-hxy-u`

- **CMIP6 name:** fco2fos
- **Long name:** Carbon Mass Flux into Atmosphere Due to Fossil Fuel Emissions of CO2 [kgC m-2 s-1]
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** discard

### `atmos.fco2nat.tavg-u-hxy-u`

- **CMIP6 name:** fco2nat
- **Long name:** Surface Carbon Mass Flux into the Atmosphere Due to Natural Sources [kgC m-2 s-1]
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** discard
- **Notes:** EXPERIMENT DEPENDENCE: AMIP runs are concentration-driven (CO2 tracer forced by the flbc surface concentrations); coupled runs are emission-driven (CO2 from emissions and land/ocean fluxes). DISCARD only for the concentration-driven AMIP configuration. TO BE REVIEWED for the emission-driven coupled runs: natural land + ocean CO2 fluxes as seen by the atmosphere. RESOLVED for AMIP (concentration-driven): DISCARD. To be revisited when the coupled emission-driven configuration is mapped. RESOLVED for AMIP (concentration-driven): DISCARD. To be revisited when the coupled emission-driven configuration is mapped. RESOLVED for AMIP (concentration-driven): DISCARD. To be revisited when the coupled emission-driven configuration is mapped.

### `atmos.hfdsnb.tavg-u-hxy-lnd`

- **CMIP6 name:** hfdsnb
- **Long name:** Downward Heat Flux at Snow Base
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Land-model (CLM) variable, not in CAM MFT.

### `atmos.hus.tpt-p6-hxy-air`

- **CMIP6 name:** hus6
- **Long name:** Specific humidity
- **CAM fields:** `Q, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous, 950-700 hPa. Option: online 2D levels to avoid 3hr 3D. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.loadbc.tavg-u-hxy-u`

- **CMIP6 name:** loadbc
- **Long name:** Load of Black Carbon Aerosol
- **CAM fields:** `BURDENBCdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `atmos.loadoa.tavg-u-hxy-u`

- **CMIP6 name:** loadoa
- **Long name:** Load of Dry Aerosol Organic Matter
- **CAM fields:** `BURDENPOMdn, BURDENSOAdn`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `atmos.loadpoa.tavg-u-hxy-u`

- **CMIP6 name:** loadpoa
- **Long name:** Load of Dry Aerosol Primary Organic Matter
- **CAM fields:** `BURDENPOMdn`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Day-night (dn) variant: defined at all times, consistent with area: time: mean.

### `atmos.loadso4.tavg-u-hxy-u`

- **CMIP6 name:** loadso4
- **Long name:** Load of SO4
- **CAM fields:** `BURDENSO4dn`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: loadso4 = BURDENSO4dn * 96.06/115.11 (= 0.8345): in the ghg_mam4 mechanism so4_a* are ammonium bisulfate (chem_mech.in: so4_a1 -> NH4HSO4, adv_mass 115.107), DR asks for sulfate (SO4) dry mass. Day-night (dn) variant.

### `atmos.noaahi2m.tavg-h2m-hxy-u`

- **CMIP6 name:** noaahi2m
- **Long name:** mean 2m daily NOAA heat index
- **CAM fields:** `HEATIDX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field HEATIDX (cam_diagnostics.F90, diag_surf), every time step: DR NOAA formula with T = TREFHT in degF and RH in % = RHREFHT (q/qs, qs from qsat, w.r.t. liquid water at these temperatures), no extra constants; converted to degC; fillvalue (flag_xyfill) where TREFHT < 299.817 K, so the daily mean is over the samples where the index is defined and missing if never defined. TEST: instantaneous recomputation exact (max 5e-5 degC, no mask mismatch); daily: defined in 20% of points*days, median 29.7 degC, consistent masking. Resolved.

### `atmos.noaahi2m.tmax-h2m-hxy-u`

- **CMIP6 name:** noaahi2mmax
- **Long name:** max 2m daily NOAA heat index
- **CAM fields:** `HEATIDXMX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field HEATIDXMX (avg flag X): daily maximum of the time-step heat index (same computation as HEATIDX, fill values excluded). TEST: HEATIDXMX defined exactly where TREFHTMX >= 299.817 K, >= HEATIDX everywhere, max 42.4 degC (Australia). Resolved.

### `atmos.pr.tmax-u-hxy-u`

- **CMIP6 name:** prhmax
- **Long name:** Maximum Hourly Precipitation Rate
- **CAM fields:** `PRECT`
- **Reprocess:** True
- **Confidence:** medium
- **Status:** ok
- **Notes:** Max of hourly means; PRECTMX is time-step max.

### `atmos.prra.tavg-u-hxy-u`

- **CMIP6 name:** prra
- **Long name:** Rainfall Flux
- **CAM fields:** `PRECT, PRECSC, PRECSL`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** prra = (PRECT - PRECSC - PRECSL)*1000 kg/m3: liquid precipitation (convective + large-scale), m/s water equivalent to kg m-2 s-1; linear, exact from time means.

### `atmos.prrsn.tavg-u-hxy-lnd`

- **CMIP6 name:** prrsn
- **Long name:** Fraction of Rainfall on Snow
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Land-model (CLM) variable, not in CAM MFT.

### `atmos.prsnc.tavg-u-hxy-lnd`

- **CMIP6 name:** prsnc
- **Long name:** Convective Snowfall Flux
- **CAM fields:** `PRECSC, LANDFRAC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** prsnc = PRECSC*1000 kg/m3 (convective snowfall, m/s water equivalent to kg m-2 s-1); mean where land: value of the cell, missing where LANDFRAC = 0.

### `atmos.prsnsn.tavg-u-hxy-lnd`

- **CMIP6 name:** prsnsn
- **Long name:** Fraction of Snowfall (Including Hail and Graupel) on Snow
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Land-model (CLM) variable, not in CAM MFT.

### `atmos.reffsclwtop.tavg-u-hxy-scl`

- **CMIP6 name:** reffsclwtop
- **Long name:** Cloud-Top Effective Droplet Radius in Stratiform Cloud
- **CAM fields:** `ACTREL, FCTL`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** reffsclwtop = mean(ACTREL)/mean(FCTL), micron to m, missing where FCTL = 0. micro_pumas_cam.F90 (cam_dev): every microphysics step each column is scanned from the top; at the first layer with stratiform liquid (liqcldf > 0.01, in-cloud liquid > 1e-7 kg/kg) ACTREL accumulates REL*liqcldf and FCTL accumulates liqcldf; if an ice layer (icecldf > 0.01) is found first the column has no liquid top. Hence the ratio is the effective radius of the uppermost liquid layer seen from space, weighted by the liquid cloud-top fraction, as in DR. Same sampling for both terms: exact. Caveats for the CMOR comment: cloud-top fraction is the liquid fraction of that layer (no overlap correction); shallow convective clouds are part of the CLUBB stratiform fraction and cannot be reported separately as DR asks.

### `atmos.rluscs.tavg-u-hxy-u`

- **CMIP6 name:** rluscs
- **Long name:** Surface Upwelling Clear-Sky Longwave Radiation
- **CAM fields:** `FLNSC, FLDSC`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** FLNSC + FLDSC.

### `atmos.rtmt.tavg-u-hxy-u`

- **CMIP6 name:** rtmt
- **Long name:** Net Downward Radiative Flux at Top of Model
- **CAM fields:** `FSNT, FLNT`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** FSNT - FLNT, both at the top of the model: matches DR (differs from TOA because of the RRTMG extra layer).

### `atmos.snmsl.tavg-u-hxy-lnd`

- **CMIP6 name:** snmsl
- **Long name:** Water Flowing out of Snowpack
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Land-model (CLM) variable, not in CAM MFT.

### `atmos.snrefr.tavg-u-hxy-lnd`

- **CMIP6 name:** snrefr
- **Long name:** Refreezing of Water in the Snow
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Land-model (CLM) variable, not in CAM MFT.

### `atmos.snwc.tavg-u-hxy-lnd`

- **CMIP6 name:** snwc
- **Long name:** Snow Water Equivalent Intercepted by the Vegetation
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Land-model (CLM) variable, not in CAM MFT.

### `atmos.ta.tpt-p5u-hxy-u`

- **CMIP6 name:** taUTLS
- **Long name:** 6 hourly instantaneous temperature in the UTLS region
- **CAM fields:** `T, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** UTLS levels (150-250 hPa), never below ground; no "where air" in DR. Interpolate offline with PMID.

### `atmos.ta.tpt-p6-hxy-air`

- **CMIP6 name:** ta6
- **Long name:** Air temperature
- **CAM fields:** `T, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous, 950-700 hPa; masking exact. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.tntrs.tavg-al-hxy-u`

- **CMIP6 name:** tntrs
- **Long name:** Tendency of Air Temperature Due to Shortwave Radiative Heating
- **CAM fields:** `QRS, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** QRS (K/s), shortwave heating rate on model levels (all sky), computed on radiation time steps and applied at every step; PS for the hybrid formula terms.

### `atmos.ts.tavg-u-hxy-lnd`

- **CMIP6 name:** tsns
- **Long name:** Snow Surface Temperature
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** tsns (snow surface temperature): Land-model (CLM) variable, not in CAM MFT.

### `atmos.ua.tpt-p5u-hxy-air`

- **CMIP6 name:** uaUTLS
- **Long name:** 6 hourly instantaneous eastward wind in the UTLS region
- **CAM fields:** `U, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** UTLS levels. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.ua.tpt-p6-hxy-air`

- **CMIP6 name:** ua6
- **Long name:** Eastward wind
- **CAM fields:** `U, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous, 950-700 hPa. Option: online 2D levels. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.va.tpt-p5u-hxy-air`

- **CMIP6 name:** vaUTLS
- **Long name:** 6 hourly instantaneous northward wind in the UTLS region
- **CAM fields:** `V, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** UTLS levels. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.va.tpt-p6-hxy-air`

- **CMIP6 name:** va6
- **Long name:** Northward Wind
- **CAM fields:** `V, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous, 950-700 hPa. Option: online 2D levels. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.wap.tpt-p6-hxy-air`

- **CMIP6 name:** wap6
- **Long name:** Omega (=dp/dt)
- **CAM fields:** `OMEGA, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Instantaneous, 950-700 hPa. Option: online 2D levels. DECISION: keep 3D fields, interpolate offline with instantaneous PMID; masking with instantaneous PS is exact.

### `atmos.wbgt.tavg-h2m-hxy-u`

- **CMIP6 name:** wbgt2m
- **Long name:** mean 2m daily wet bulb globe temperature
- **CAM fields:** `WBGT`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field WBGT (diag_surf), every time step: DR formula 0.567*T_C + 0.393*e/100 + 3.94 with e = QREFHT*PS/epsilo (CAM physconst epsilo = mwh2o/mwdry instead of the DR molar masses, relative difference ~1e-4), T_C = TREFHT - tmelt; exact daily mean. TEST: instantaneous recomputation exact (max 1e-5 degC); daily mean vs formula from daily means: max 0.013 degC (product of means). Resolved.

### `atmos.wbgt.tmax-h2m-hxy-u`

- **CMIP6 name:** wbgt2mmax
- **Long name:** maximum 2m daily wet bulb globe temperature
- **CAM fields:** `WBGTMX`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** DECISION: new online field WBGTMX (avg flag X): daily maximum of the time-step WBGT (CAM constants). TEST: WBGTMX >= WBGT everywhere, max 34.7 degC. Resolved.

### `atmos.wsg.tmax-h100m-hxy-u`

- **CMIP6 name:** wsgmax100m
- **Long name:** Maximum Wind Speed of Gust at 100m
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmos.wsg.tmax-h10m-hxy-u`

- **CMIP6 name:** wsgmax10m
- **Long name:** Maximum Wind Speed of Gust at 10m
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** DECISION: DISCARD. DR asks for the maximum instantaneous wind gust at 10 m. In this CAM version U10WITHGUSTS/UGUST are never filled (outfld commented out, coupler field So_u10withGust not imported), and CAM gustiness (convective/subgrid enhancement of the mean wind for fluxes) is not a WMO gust.

## Realm: atmosChem

### `atmosChem.cfc11.tavg-u-hm-air`

- **CMIP6 name:** cfc11global
- **Long name:** Global Mean Mole Fraction of CFC11
- **CAM fields:** `TMCFC11, PS, AREA`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** Global mean mole fraction weighted by moles of air: (sum(TMCFC11*AREA)/M_CFC11)/(sum(PS/g*AREA)/M_air), units 1E-12. CFC11 is a prognostic tracer (flbc + loss); radiation uses N:CFC11STAR (prescribed CFC11-equivalent): document in the CMOR comment.

### `atmosChem.cfc113.tavg-u-hm-air`

- **CMIP6 name:** cfc113global
- **Long name:** Global Mean Mole Fraction of CFC113
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** Lumped into CFC11STAR.

### `atmosChem.cfc12.tavg-u-hm-air`

- **CMIP6 name:** cfc12global
- **Long name:** Global Mean Mole Fraction of CFC12
- **CAM fields:** `TMCFC12, PS, AREA`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** As cfc11 with TMCFC12 and M_CFC12; CFC12 is radiatively active (A:CFC12).

### `atmosChem.ch4.tavg-al-hxy-u`

- **CMIP6 name:** ch4
- **Long name:** Mole Fraction of CH4
- **CAM fields:** `CH4, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** CH4 tracer (mol/mol), radiatively active (A:CH4): flbc surface concentrations, transport and first-order loss with prescribed loss frequencies (mo_ghg_chem.F90). Nonuniform: 3D as DR asks.

### `atmosChem.drynh3.tavg-u-hxy-u`

- **CMIP6 name:** drynh3
- **Long name:** Dry Deposition Rate of NH3
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.drynh4.tavg-u-hxy-u`

- **CMIP6 name:** drynh4
- **Long name:** Dry Deposition Rate of NH4
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.drynoy.tavg-u-hxy-u`

- **CMIP6 name:** drynoy
- **Long name:** Dry Deposition Rate of NOy
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** discard
- **Notes:** Registered but no NOy species in mechanism.

### `atmosChem.emich4.tavg-u-hxy-u`

- **CMIP6 name:** emich4
- **Long name:** total emission rate of CH4
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** CH4 driven by lower boundary condition.

### `atmosChem.flashrate.tavg-u-hxy-u`

- **CMIP6 name:** flashrate
- **Long name:** Lightning Flash Rate
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard
- **Notes:** DECISION: DISCARD. FLASHFRQ (mo_lightning.F90) is the Price and Rind (1992) flash frequency per storm per minute from the convective cloud-top height, computed even without lightning NOx (needs CLDTOP/CLDBOT), flag I. DR asks for flash density (km-2 s-1): CAM does not compute it (the NOx production uses its own grid factor and tuning). Methods in the literature are empirical calibrations: Price and Rind (1994) resolution calibration factor (shown to scale poorly with resolution, Wong et al. 2013, GMD) or rescaling to the observed global flash rate (~45 s-1, LIS/OTD), i.e. tuning rather than a model prediction; one storm per ~1 deg cell is not realistic.

### `atmosChem.hcfc22.tavg-u-hm-air`

- **CMIP6 name:** hcfc22global
- **Long name:** Global Mean Mole Fraction of HCFC22
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.n2o.tavg-al-hxy-u`

- **CMIP6 name:** n2o
- **Long name:** Mole Fraction of N2O
- **CAM fields:** `N2O, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** N2O tracer (mol/mol), radiatively active (A:N2O): flbc surface concentrations, transport and first-order loss with prescribed loss frequencies. Nonuniform: 3D as DR asks.

### `atmosChem.o3.tavg-al-hxy-u`

- **CMIP6 name:** o3
- **Long name:** Mole Fraction of O3
- **CAM fields:** `ozone, PS`
- **Reprocess:** False
- **Confidence:** high
- **Status:** ok
- **Notes:** Prescribed ozone used by radiation (N:ozone, CMIP7 FZJ-CMIP-ozone-2-0, monthly, interpolated in time): documents the forcing seen by the model. Field registered with avg flag I: request ozone:A in fincl. If ozone only repeats an annual cycle, DR asks for the climatological variant.

### `atmosChem.o3.tavg-p19-hxy-air`

- **CMIP6 name:** o3
- **Long name:** Mole Fraction of O3
- **CAM fields:** `ozone, PMID, PS`
- **Reprocess:** True
- **Confidence:** high
- **Status:** ok
- **Notes:** As o3 on model levels (ozone:A), interpolated offline with PMID, masked where plev > PS. If ozone does not change except for the annual cycle, DR asks for tro3Clim instead (experiment-dependent).

### `atmosChem.o3ste.tavg-al-hxy-u`

- **CMIP6 name:** o3ste
- **Long name:** Stratospheric Ozone Tracer Volume Mixing Ratio
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.tropo3ste.tavg-al-hxy-u`

- **CMIP6 name:** tropo3ste
- **Long name:** Tropospheric ozone volume mixing ratio due to stratosphere-troposphere exchange (STE)
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.wetnh3.tavg-u-hxy-u`

- **CMIP6 name:** wetnh3
- **Long name:** Wet Deposition Rate of NH3
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.wetnh4.tavg-u-hxy-u`

- **CMIP6 name:** wetnh4
- **Long name:** Wet Deposition Rate of NH4
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** high
- **Status:** discard

### `atmosChem.wetnoy.tavg-u-hxy-u`

- **CMIP6 name:** wetnoy
- **Long name:** Wet Deposition Rate of NOy Including Aerosol Nitrate
- **CAM fields:** `DISCARD`
- **Reprocess:** False
- **Confidence:** medium
- **Status:** discard

