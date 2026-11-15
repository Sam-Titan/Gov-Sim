# PROGRESS — GovSim V1

Update after every task. Newest log entries at the top.

## Current phase
**Phase 3 — Fast model + API** (signed off 2026-11-15). Next: Phase 4, not started.

## Phase status
| Phase | Status | Sam signed off |
|---|---|---|
| 0 Setup | ✅ Done | ✅ Sam, 2026-11-15 |
| 1 Data | ✅ Done | ✅ Sam, 2026-11-15 |
| 2 Model | ✅ Done | ✅ Sam, 2026-11-15 |
| 3 Fast model + API | ✅ Done | ✅ Sam, 2026-11-15 |
| 4 Simulator page | ⏳ Not started | — |
| 5 Other pages | ⏳ Not started | — |
| 6 Downloads + Hindi | ⏳ Not started | — |
| 7 Test + launch | ⏳ Not started | — |

## Current phase tasks
- [x] Scheme search; final V1 schemes = 4 NFHS proxies (D-028)
- [x] Download all NFHS-5 district fact sheets by script: 704 PDFs
- [x] Fill `data/MANIFEST.csv` for each file (714 rows)
- [x] Parse the PDFs to `data/processed/nfhs_districts.parquet`
- [x] Download Census 2011 PCA (district) from censusindia.gov.in (D-032)
- [x] District join table `data/processed/district_map.parquet` (634 of 704 mapped; 70 unmapped, listed)
- [x] Eligible counts per scheme per district (`eligible_counts.parquet`, Census 2011 bases)
- [x] Simplified GeoJSON for the frontend (`districts.geojson`, 1.16 MB)
- [x] Data report (`docs/DATA_REPORT.md`)
- [x] Census C-20 disability (35 state files, 640 districts) + NFHS trait indicators + NFHS-5 state bank/phone/internet (`partial_data`) -> `district_traits.parquet` (D-035)
- [x] `data/processed/README.md` (source and licence per file); map has `has_nfhs_data`; DD state name fixed
- [x] Follow-ups (D-036): `xlrd`, Census C-13 age 60+ (35 xls, 640 districts), drop widows/electricity, beta7 deprivation score, beta2 state income (Economic Survey table 1.11A)
- [x] **Phase 1 done.** `just check` and `just test` pass. Waiting for Sam's sign-off.

## Phase 3 tasks
- [x] JSY sampling band: n = women interviewed x (Census children 0-6 x 5/7 / Census women 15-49), labelled "estimated" (D-042). New column `women_15_49` in `census_age.parquet`. JSY median half-width ±1.49 -> ±2.34 pp (max 3.38 -> 6.0)
- [x] deff 2.0 kept, labelled "assumed by team" in `report.json` (`sampling_band.deff`)
- [x] Documents effect for all agents: left out (Sam)
- [x] Speed check, then **no surrogate** (D-043, Sam approved). SPEC 5.4 and PHASES updated
- [x] `govsim/service.py`: live anchored model at weak / central / strong beta sets, reasons (top 3), warnings
- [x] Routes: `/states`, `/districts`, `/schemes`, `/simulate`, `/simulate/state`, `/compare`, `/report` (Pydantic, `operation_id` set). Client regenerated (`just gen-api`); mock updated to the real shape
- [x] No-data districts: `/districts` lists all 710 with `has_data` + `reason`; `/simulate` returns 404 `{code: "no_data", reason}`; `/simulate/state` marks them `has_data: false`
- [x] Sam's changes before sign-off: custom policies report group uptake + people reached (D-044, SPEC 7.2); current state shown (Warangal -> Telangana, D-045); no-baseline rule checked (D-045)
- [x] NFHS-4 state value for NCT Delhi and Telangana as PM-JAY / PMUY baseline, flagged `partial_data` (D-046); `parse_state.py`, `nfhs4_state_baseline.parquet`, DATA_REPORT, tests
- [x] 78 backend tests, `just check` and `just test` pass
- [x] Phase 3 signed off by Sam, 2026-11-15 (once D-046 was in).

## Phase 3 results (2026-11-15)
**Speed, through the HTTP routes (TestClient, median / worst of 30, ms).** Model only: one district 6 / 17, state of 71 districts 6 / 12, all 629 districts 25.
| Route | Median | Worst |
|---|---|---|
| `POST /simulate` | 15 | 20 |
| `POST /simulate` (custom policy) | 13 | 23 |
| `POST /simulate/state` (Uttar Pradesh, 75 rows) | 14 | 25 |
| `POST /compare` (two results) | 21 | 31 |
Under 200 ms. Start-up 0.3 s for the model plus a few seconds of imports. The strict 200 ms test runs locally only (skipped when `CI` is set); CI uses a 1 s bound.

**Warnings.** `survey_estimate` always; `low_confidence` over 30 pp; `new_policy` for every custom policy; `out_of_range` ("Beyond what real schemes do") when a slider is outside the real-scheme envelope (cash 600 to 5,00,000; documents 1 to 6; burden 2 to 3; speed 2 to 4); `partial_data` when the PM-JAY/PMUY baseline came from a state mean, or a custom policy targets "unbanked".
**Districts.** 710 listed (704 NFHS sheets + 6 Census districts with no sheet). 629 have data; 81 do not: 70 `unmapped`, 5 `no_state_income`, 6 `no_nfhs_sheet` (Chandigarh, Lakshadweep, Vidisha, and the split parents Jaintia Hills, Barddhaman, Warangal). `name_hi` is null (no Hindi district names in our data).
**Sam's changes, done (D-044, D-045).**
- **Custom policies:** `result.basis = "target_group"`: uptake within the group (%, range = weak/central/strong betas x NFHS sampling band) and `result.reach` (estimated count: Census 2011 base x group share x uptake; households for PM-JAY/PMUY, births for JSY, people for SBM). `new_policy` stays. Example (Araria, PMUY, rural unbanked women): group 8.8% of 5.7 lakh households (about 50,000), uptake 5.7% (2.1 to 10.6), about 2,850 reached (1,070 to 5,300). `/compare` returns `comparable: false` between a custom policy and a real scheme. Groups under 10 of 500 agents return `group_too_small`.
- **Current state:** Warangal is listed under Telangana; `pc11_s_id` kept. It was the only census-only district with a changed state (Ladakh and Telangana districts with NFHS sheets already use the current state). Start-up fails loudly on an unreviewed split.
- **No baseline:** D-038 already used the household-weighted state mean (flagged `partial_data`) for non-Telangana districts, so nothing changed there. **Not all of them can be filled:** NCT Delhi has no NFHS-4 value for any of its 9 mapped districts (re-drawn after 2015-16), so it has no state mean either. **Done (D-046):** Delhi and Telangana now use the official NFHS-4 state value (insurance 15.7 / 66.4, clean fuel 97.9 / 67.3), flagged `partial_data`. PM-JAY and PMUY have 629 rows each. Known limit: in 167 of 629 PM-JAY rows (8 of the 18 new) the NFHS-5 value is not above the baseline, so the anchor is baseline + 0.5 pp (23 of 629 for PMUY).

**Choices made while building (approved by Sam).** JSY cash slider replaces the rural value (urban keeps the real ratio). PM-JAY cash outside ₹2,50,000 to ₹10,00,000 returns 422. `name_hi` is null. Chandigarh and Lakshadweep use their own name as the state.
**Speed with the custom policy (HTTP, median / worst ms):** `/simulate` 21 / 39; `/simulate/state` (Uttar Pradesh) 31 / 64. Still under 200 ms.

## Phase 2 tasks
- [x] Plan, slider values (D-037), model design (D-038), hybrid decision (D-039), β values and range rule (D-040), anchor and bands (D-041)
- [x] Sampler, eligibility, adoption model (monthly-income β2), logit anchor, slider change, range rule (`govsim/hybrid.py`), PM-JAY benefit cap
- [x] NFHS sample sizes parsed for all 704 sheets (`scripts/parse_sample_sizes.py`, `nfhs_sample_sizes.parquet`)
- [x] β0, β7 refitted (β2, 3, 5, 6, 8 fixed); LOSTO headline + LOSO; GBM bands; sampling bands; sanity table; recovery -> `backend/artifacts/report.json`, `betas.json`
- [x] `just check` and `just test` pass (47 backend tests)
- [x] Phase 2 signed off by Sam, 2026-11-15 (committed and pushed by Sam).

## Phase 2 results (2026-11-15, `just train`, 21 s)
Data: 629 districts, 3,614 rows (see D-038 for exclusions and baselines).

**Accuracy, MAE pp on held-out NFHS-5 rows (headline = LOSTO).**
| Test | Agent model (fixed central β, unanchored) | GBM | Naive (training mean) |
|---|---|---|---|
| LOSTO (leave one state out), headline | 26.1 | 10.5 | 23.0 |
| LOSO (leave one scheme out) | 29.7 | 30.8 | 26.2 |

- **The agent model does not beat the GBM** and is no longer used to predict a level. With β2, 3, 5, 6, 8 fixed, its unanchored in-sample MAE is 23 pp (GBM 4.2). Its job is the slider change, so this is expected; the report page must say so (D-039).
- **LOSO:** 4 schemes are too few; a held-out scheme has slider values never seen in training. Per scheme (agent / GBM / naive): JSY 23.0 / 39.1 / 36.2; PM-JAY 58.5 / 42.8 / 32.7; PMUY 29.1 / 23.9 / 22.5; SBM 8.8 / 17.3 / 13.6.
- Agent beats GBM in 3 of 32 states.

**Fitted terms (central set; weak and strong in `report.json`).** β0 = 1.09 (weak 0.90, strong 1.19), β7 = -0.75 (-0.74, -0.81), era shift = -0.47 (-0.26, -0.70). β7 has the expected sign. Recovery (simulate, refit from zero, other β fixed): at 1 pp and 3 pp noise β0, β7 and the era shift come back within 0.02, as long as the model is right. β0 and β7 do not change the anchored slider changes (D-041).
**Fixed β (assumed by team, approved):** β2 0.2 / 0.5 / 1.0; β3 -0.3 / -0.8 / -1.5; β5 -0.2 / -0.6 / -1.2; β6 0.1 / 0.4 / 0.8; β8 -0.3 / -0.9 / -1.8 (weak / central / strong). β1 = 1.0 on trust 0 (assumed).

**Bands (pp).**
| Scheme | GBM LOSTO band (10th / 90th pct, in report only) | NFHS sampling band, median half-width (max) |
|---|---|---|
| PM-JAY | -28.68 / +28.53 | ±2.7 (6.05) |
| PMUY | -12.28 / +15.03 | ±2.79 (5.61) |
| JSY | -6.85 / +11.1 | ±1.49 (3.38), understated |
| SBM | -14.84 / +13.2 | ±2.68 (6.03) |
Sampling band method: `SE = sqrt(deff × p × (1-p) / n)`, band ±1.2816 × SE (10th-90th percentile). `n` = households interviewed (read from each sheet; 704 of 704 found, 213 to 990, median 908) for PM-JAY, PMUY, SBM; women interviewed for JSY (no births count is printed, so the JSY band is **understated**). **Design effect 2.0 is assumed by team.** At the real settings no district is wider than 30 pp, so "low confidence" only appears when sliders move a lot (e.g. SBM, strong set, +1 burden: change -11.3 pp, range about 11 pp + band).

**Sanity table (anchored at the actual NFHS value, median district, weak / central / strong, pp).**
| Scheme | +1 document | +1 burden | +1 speed | Double benefit | Add bank requirement |
|---|---|---|---|---|---|
| PM-JAY | -0.1 / -0.2 / -0.3 | -0.7 / -1.9 / -3.3 | +0.4 / +1.5 / +3.2 | +1.0 / +2.7 / +5.8 | -0.3 / -0.9 / -1.3 |
| PMUY | -0.2 / -0.3 / -0.3 | -1.0 / -2.8 / -4.8 | +0.5 / +2.0 / +3.8 | +0.2 / +0.5 / +0.9 | already required |
| JSY | -0.2 / -0.5 / -1.0 | -0.8 / -2.4 / -5.5 | +0.4 / +1.3 / +2.4 | +0.1 / +0.2 / +0.5 | -0.5 / -2.0 / -5.5 |
| SBM | -0.4 / -1.1 / -1.9 | -2.0 / -6.0 / -11.3 | +1.0 / +3.6 / +6.3 | +1.5 / +3.5 / +6.2 | already required |
One oddity: PMUY +1 document is -0.30 (central) and -0.25 (strong): the sets are refitted separately and the effect is tiny, so the order flips slightly. Not an error in the model.

**Optional: documents effect for all agents (proposal, NOT used).** Add `β3a × docs/4` for every agent, besides the illiterate-only β3. Values (weak / central / strong): -0.05 / -0.15 / -0.30. Effect of +1 document on z is -0.01 / -0.04 / -0.08 for a literate agent (vs -0.08 / -0.20 / -0.38 for an illiterate one). Tiny; say if you want it in.

**Files:** `backend/govsim/hybrid.py` (anchor, change, sampling band, range, low-confidence), `govsim/evaluate/sanity.py`, `scripts/parse_sample_sizes.py`, `backend/artifacts/{report,betas}.json` (not git-ignored; Sam commits).
Suggested commit message: `Phase 2 model: hybrid output (NFHS level + anchored agent-model change), fixed assumed betas, sampling bands, LOSTO/LOSO report`

## Waiting on Sam
- Nothing. Phase 4 (simulator page) has not started; say "start Phase 4" to begin.
- Notes carried forward: deff 2.0 is an assumption; JSY n is an estimate (2011 ratio); documents effect not used.

## Blockers
- 70 NFHS-5 districts (mostly new since 2011, 22 of 31 in Telangana) have no 2011 parent. An official source is needed (LGD has a captcha, so not scriptable). See decision 1 below.
- Open decision: `@testing-library/jest-dom` (removed in Phase 0): not approved, stays uninstalled.

## Key results (fill in as phases finish)
- Agent model LOSO MAE: 29.7 pp (naive 26.2; fixed central β, D-039)
- GBM LOSO MAE: 30.8 pp
- Agent model LOSTO MAE: 26.1 pp (naive 23.0); GBM LOSTO (headline): 10.5 pp
- GBM LOSTO MAE: 10.5 pp
- `/simulate` speed: 15 ms median, 20 ms worst (HTTP, no surrogate, D-043)

## Findings: NFHS-5 district data (2026-11-15)
Source: DHS Program, `dhsprogram.com/pubs/pdf/OF43/<ST>_<District>.pdf`. `robots.txt` does not block `/pubs/pdf`. Licence: Govt of India (MoHFW/IIPS) public report; no licence text on the page.
I opened the files: 704 PDFs read with `pdftotext`, one row per district, 34 state/UT codes. Chandigarh skipped. Telangana: 31 districts, read from the DHS district sheets (they exist at `TG_<District>.pdf`; the state compendium only has the state sheet).

| Scheme (label) | NFHS indicator | NFHS-5 values | NFHS-5 range | NFHS-4 values | Few-case flags |
|---|---|---|---|---|---|
| PM-JAY (proxy) | Households with a member covered by health insurance/financing scheme | 704 of 704 | 1.2 – 97.8 % | 572 of 704 | 0 |
| PMUY (proxy) | Households using clean cooking fuel | 704 of 704 | 8.6 – 99.8 % | 572 of 704 | 0 |
| JSY (proxy) | Institutional births (last 5 years) | 704 of 704 | 21.4 – 100 % | 572 of 704 | 0 |
| SBM (proxy) | Population using improved sanitation facility | 704 of 704 | 29.2 – 99.9 % | 572 of 704 | 0 |

- **No missing NFHS-5 values.** NFHS-4 is missing for 132 districts: all 31 Telangana districts and 101 districts created or re-drawn after 2015-16 (largest: Gujarat 17, Chhattisgarh 15, Assam 12, Delhi 11). The sheets print `na` for these.
- **Check against a second copy:** the GitHub CSV (`pratapvardhan/NFHS-5`, CC BY 4.0, 341 districts) matches my parsed values exactly for 340 districts x 4 indicators x 2 time points (0 differences). 1 district did not match by name.
- **Sheet differences found and handled:** Mahisagar (GJ) and Wardha (MH) use an older template: indicators are numbered differently and insurance reads "covered by a health scheme or health insurance". The parser reads by label, not number. 5 file names differ from the district names (e.g. Bulandshahr, Bandipore, Papumpare, Toubal, "North Tripura"); the script uses the spelling from the link list first.
- **Map join:** the map has 641 polygons (Census 2011 districts, 35 state ids, columns `pc11_s_id`, `pc11_d_id`, `d_name`). 618 of the 704 NFHS names match a map name exactly. The rest (new/split districts, spelling) need the join table.
- **Timing caution:** NFHS-4 was surveyed in 2015-16, before PMUY (May 2016) and PM-JAY (2018). For those two, NFHS-4 is a baseline, not scheme uptake.
- **Survey estimates:** about 700-1,000 households per district, so sampling error. The `survey_estimate` warning is in SPEC §5.4.
- **Download etiquette:** 1.5 s wait between requests per worker. The first run was one worker; I then used 3 workers in parallel to finish faster (about 3 requests at once).

### Why the others failed (short)
NSAP, Ujjwala, Jan Dhan: district files only on data.gov.in (`robots.txt` blocks all bots), Dataful, or AIKosh (terms unclear). MGNREGA: MIS pages use a captcha and checked report URLs. India Data Portal: 403. NFHS district sheets have no JSY payment, bank account or ICDS indicator (state-level only). Details are in DECISIONS D-028.

### Sliders and β terms (decided 2026-11-15, D-031)
`digital_only` and β4 dropped from SPEC. `requires_bank_account` and β8 kept; dropped in Phase 2 if not estimable. β2 renamed "benefit value relative to income" (PM-JAY value from official guidelines in Phase 2, cited). β3, β5, β6, β8 marked "weakly estimated". Metric label: D-030.

## Findings: Census 2011, join, map (2026-11-15)
- **Census source (D-032):** `censusindia.gov.in` Census Digital Library, table PC11_PCA-SD. The site has no `robots.txt` (404). The Excel file downloaded with no login. I found no terms page; licence is not stated. The file has 640 districts x (Total, Rural, Urban), 94 columns. Saved to `data/raw/census2011/`.
- **Keys match the map:** all 640 Census district ids equal the map's `pc11_d_id`. The map has 641 polygons: one extra (`pc11_d_id` 000, J&K) with no name or Census row. I kept it in the GeoJSON (marked `has_census_data: false`) so the outline of India is not changed. Say if you want it removed.
- **All-India check:** 249,501,663 households and 1,210,854,977 people, equal to the official India row.
- **Join NFHS to 2011:** 634 of 704 mapped (617 exact name, 17 reviewed spelling/rename: e.g. Ahmedabad, Prayagraj = Allahabad, Dantewada). Each maps to a different 2011 district (no clashes). **70 unmapped**, by state: Telangana 22, Chhattisgarh 9, Gujarat 7, Assam 6, Meghalaya 5, Arunachal 4, Tripura 4, UP 4, and a few in 6 other states (Delhi 2, West Bengal 2, Punjab 2, Madhya Pradesh 1, Haryana 1, Maharashtra 1). List: `data/interim/unmapped_districts.csv`.
- **Fuzzy matching rejected:** a trial matched "South East" Delhi to "South West" and "North Garo Hills" to "South Garo Hills". I used exact names plus a short hand-reviewed list only, and did not guess parents.
- **Boundary risk:** an exact name match does not prove the same boundary. A 2011 district that later lost land keeps its name. Treat states with unmapped districts as "boundary changed".
- **2011 districts with no NFHS district:** Chandigarh (skipped), Lakshadweep, Vidisha (MP), Jaintia Hills, Barddhaman, Warangal. The last three were split, so their new districts are among the 70 unmapped.
- **Two NFHS sheets not found:** Vidisha (MP) and Lakshadweep. Vidisha is missing from the third-party district list, and `MP_Vidisha.pdf` and `LD_Lakshadweep.pdf` are 404 at DHS. NFHS-5 reports 707 districts, and 704 + Chandigarh + Vidisha + Lakshadweep = 707.
- **Eligible counts (bases for the NFHS %):** PM-JAY, PMUY = households; SBM = people; JSY = births in the last 5 years, **estimated** as children 0-6 x 5/7 (ignores child deaths and migration). All Census 2011, so populations are 10+ years old by NFHS-5 time.
- **Map:** simplified to about 1 km (1.16 MB, valid geometry, 641 polygons). It carries the CC BY-NC-SA 4.0 credit in the file (`attribution`). If you commit it, note the repo has no licence (all rights reserved) while the map must stay CC BY-NC-SA.

### Gap for Phase 2: agent traits
SPEC §5.1 samples agents by age band, gender, widow, disability, rural/urban, BPL, literate, bank account, internet/phone, LPG, income band. The Census PCA gives only rural/urban, gender, children 0-6, SC/ST, literacy and workers. NFHS district sheets give some shares (e.g. women literate, electricity, clean fuel, improved water) but I only parsed the 4 scheme indicators. **No district source for BPL, widow, disability, age 60+, bank account, internet, income.** I did not invent any. Options in decision 3 below.

### Decisions done (Sam, 2026-11-15)
D-033 V1 uses 634 mapped districts; D-034 Vidisha and Lakshadweep missing; D-035 trait sources and leakage guard; D-036 `xlrd` approved, age 60+ added, widows/BPL/LPG/electricity dropped (also from custom-policy targets), beta7 score, beta2 state income. Processed data and GeoJSON committable (README added); DD name fixed.

### Decisions needed from Sam
- Phase 1 sign-off only. Open note for Phase 2: Ladakh and Dadra & Nagar Haveli and Daman & Diu (5 districts) have no state income value.

## Log
- 2026-11-15 — Phase 3 signed off by Sam after D-046 (NFHS-4 state value for Delhi and Telangana). 78 tests, `just check` and `just test` pass. Stopped; Phase 4 not started. Suggested commit message: `Phase 3: JSY births band, live anchored model (no surrogate), API routes, group uptake for custom policies, NFHS-4 state baseline`
- 2026-11-15 — Phase 3 built. JSY births band (D-042), deff labelled assumed, no surrogate (D-043). Live service + 7 routes + warnings + reasons; no-data districts handled; client regenerated; 68 tests, `just check` clean. Stopped for Phase 3 sign-off.
- 2026-11-15 — Phase 3 changes from Sam: custom-policy group uptake + reach (D-044), current state for Warangal (D-045), no-baseline check (Delhi has no state mean). 76 tests, `just check` and `just test` pass. Stopped for Phase 3 sign-off. Suggested commit message: `Phase 3: JSY births band, live anchored model (no surrogate), API routes, tests`
- 2026-11-15 — Phase 2 signed off by Sam; code committed and pushed by Sam. Stopped; Phase 3 not started.
- 2026-11-15 — Phase 2 final (D-039 to D-041). NFHS sample sizes parsed; hybrid module (logit anchor, slider change, sampling band, end-to-end range, low-confidence); PM-JAY cap; β0, β7 refitted with β2, 3, 5, 6, 8 fixed; report.json written; 47 tests, `just check` clean. Stopped for Phase 2 sign-off.
- 2026-11-15 — Phase 2 built (D-037, D-038). Sampler, eligibility, adoption model, Nelder-Mead calibration, recovery test, GBM, LOSO/LOSTO, `just train`. 40 backend tests, `just check` clean. Agent model does not beat the GBM; β2 and β6 have the wrong sign (details above). Stopped for Sam.
- 2026-11-15 — Phase 1 follow-ups (D-036). Installed `xlrd` (approved). Downloaded C-13 (35 xls) and Economic Survey table 1.11A (MANIFEST 787 rows). Added age 60+ share, beta7 `deprivation_score`, `state_per_capita_nsdp_2021_22`; removed electricity trait; widows dropped. SPEC 5.1, 7.2, 10 and DATA_REPORT updated. 28 backend tests, `just check` clean. Phase 1 marked done; stopped for sign-off.
- 2026-11-15 — Traits and Phase 1 close-out. Downloaded Census C-20 (35 xlsx) and the two NFHS-5 state compendia (MANIFEST 751 rows). Added `parse_state.py`, `traits.py`, C-20 parsing, trait parsing in `parse_nfhs.py`, `has_nfhs_data` on map, DD name fix, `data/processed/README.md`. 8 NFHS district traits (max |r| with a target 0.67), 9 Census shares, 3 state-level traits (`partial_data`, matches GitHub CSV 37/37). SPEC 5.1 updated; D-033 to D-035. `just check` and `just test` pass. Stopped for Phase 1 sign-off.
- 2026-11-15 — Phase 1 data tasks finished. Census 2011 PCA downloaded (D-032), join table built (634/704), eligible counts, simplified GeoJSON, `docs/DATA_REPORT.md`. SPEC: metric label (D-030), β4/`digital_only` dropped, β2 renamed, "weakly estimated" notes (D-031). New scripts: `census.py`, `join_districts.py`, `geo.py`, `build_data.py`; 21 backend tests. Stopped for Sam's sign-off. Suggested commit message: `Phase 1 data: Census 2011, district join, eligible counts, map, data report`
- 2026-11-15 — Schemes switched to 4 NFHS proxies (D-028, D-029). Downloaded 704 NFHS-5 district PDFs, parsed to `data/processed/nfhs_districts.parquet`, cross-checked (0 differences vs GitHub CSV on 340 districts). New: `download_public.py`, `parse_nfhs.py`, tests. SPEC §3, §4, §5.3, §5.4, DECISIONS, PHASES updated. Old PMJDY page and row deleted; map rows fixed. `just check` and `just test` pass (10 backend, 1 frontend). Stopped for Sam. Suggested commit message: `Switch V1 to 4 NFHS-based schemes; add NFHS download and parse scripts`
- 2026-11-15 — Scheme switch: probed NFHS-5, NFHS-4, MGNREGA, India Data Portal, HMIS. No download, no SPEC/DECISIONS/PHASES change. Deleted PMJDY HTML + row; fixed map rows. Stopped for Sam. Suggested commit message: `Update manifest and log scheme data-source check`
- 2026-11-15 — Phase 1 data search done (see report above). Downloaded 1 page (pmjdy.gov.in HTML). `data/MANIFEST.csv` created with 8 rows (map files by Sam, PMJDY page by Claude Code). Stopped for Sam's review. No commit made. Suggested commit message: `Add data source search report and manifest`
- 2026-11-15 — Phase 0 signed off by Sam. D-025 logged (TypeScript 5.x pin). `@hookform/resolvers` approved (not yet installed; add when forms are built). Phase 1 started.
- 2026-11-15 — Phase 0 built. `just setup/check/test` pass; `just dev` + Vite proxy to `/api/health` verified with curl; `just gen-api` works. Notes: TypeScript pinned to 5.x (Hey API does not work with TS 7). shadcn CLI not run; `components.json` and `lib/utils.ts` added by hand. Playwright, MapLibre, Recharts not installed yet (later phases). Not a git repo yet, so Lefthook hooks install after `git init` + `just setup`. D-023, D-024 logged.
- 2026-11-16 — Planning done. SPEC, PHASES, DECISIONS, CLAUDE.md written and approved.