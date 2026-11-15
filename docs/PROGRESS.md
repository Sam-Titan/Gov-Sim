# PROGRESS — GovSim V1

Update after every task. Newest log entries at the top.

## Current phase
**Phase 1 — Data** (started 2026-11-15)

## Phase status
| Phase | Status | Sam signed off |
|---|---|---|
| 0 Setup | ✅ Done | ✅ Sam, 2026-11-15 |
| 1 Data | ✅ Done, waiting for sign-off | — |
| 2 Model | ⏳ Not started | — |
| 3 Fast model + API | ⏳ Not started | — |
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

## Waiting on Sam
- Phase 1 sign-off, and the decisions listed under "Decisions needed from Sam".

## Blockers
- 70 NFHS-5 districts (mostly new since 2011, 22 of 31 in Telangana) have no 2011 parent. An official source is needed (LGD has a captcha, so not scriptable). See decision 1 below.
- Open decision: `@testing-library/jest-dom` (removed in Phase 0): not approved, stays uninstalled.

## Key results (fill in as phases finish)
- Agent model LOSO MAE: —
- GBM LOSO MAE: —
- Agent model LOSTO MAE: —
- GBM LOSTO MAE: —
- `/simulate` speed: —

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
- 2026-11-15 — Phase 1 follow-ups (D-036). Installed `xlrd` (approved). Downloaded C-13 (35 xls) and Economic Survey table 1.11A (MANIFEST 787 rows). Added age 60+ share, beta7 `deprivation_score`, `state_per_capita_nsdp_2021_22`; removed electricity trait; widows dropped. SPEC 5.1, 7.2, 10 and DATA_REPORT updated. 28 backend tests, `just check` clean. Phase 1 marked done; stopped for sign-off.
- 2026-11-15 — Traits and Phase 1 close-out. Downloaded Census C-20 (35 xlsx) and the two NFHS-5 state compendia (MANIFEST 751 rows). Added `parse_state.py`, `traits.py`, C-20 parsing, trait parsing in `parse_nfhs.py`, `has_nfhs_data` on map, DD name fix, `data/processed/README.md`. 8 NFHS district traits (max |r| with a target 0.67), 9 Census shares, 3 state-level traits (`partial_data`, matches GitHub CSV 37/37). SPEC 5.1 updated; D-033 to D-035. `just check` and `just test` pass. Stopped for Phase 1 sign-off.
- 2026-11-15 — Phase 1 data tasks finished. Census 2011 PCA downloaded (D-032), join table built (634/704), eligible counts, simplified GeoJSON, `docs/DATA_REPORT.md`. SPEC: metric label (D-030), β4/`digital_only` dropped, β2 renamed, "weakly estimated" notes (D-031). New scripts: `census.py`, `join_districts.py`, `geo.py`, `build_data.py`; 21 backend tests. Stopped for Sam's sign-off. Suggested commit message: `Phase 1 data: Census 2011, district join, eligible counts, map, data report`
- 2026-11-15 — Schemes switched to 4 NFHS proxies (D-028, D-029). Downloaded 704 NFHS-5 district PDFs, parsed to `data/processed/nfhs_districts.parquet`, cross-checked (0 differences vs GitHub CSV on 340 districts). New: `download_public.py`, `parse_nfhs.py`, tests. SPEC §3, §4, §5.3, §5.4, DECISIONS, PHASES updated. Old PMJDY page and row deleted; map rows fixed. `just check` and `just test` pass (10 backend, 1 frontend). Stopped for Sam. Suggested commit message: `Switch V1 to 4 NFHS-based schemes; add NFHS download and parse scripts`
- 2026-11-15 — Scheme switch: probed NFHS-5, NFHS-4, MGNREGA, India Data Portal, HMIS. No download, no SPEC/DECISIONS/PHASES change. Deleted PMJDY HTML + row; fixed map rows. Stopped for Sam. Suggested commit message: `Update manifest and log scheme data-source check`
- 2026-11-15 — Phase 1 data search done (see report above). Downloaded 1 page (pmjdy.gov.in HTML). `data/MANIFEST.csv` created with 8 rows (map files by Sam, PMJDY page by Claude Code). Stopped for Sam's review. No commit made. Suggested commit message: `Add data source search report and manifest`
- 2026-11-15 — Phase 0 signed off by Sam. D-025 logged (TypeScript 5.x pin). `@hookform/resolvers` approved (not yet installed; add when forms are built). Phase 1 started.
- 2026-11-15 — Phase 0 built. `just setup/check/test` pass; `just dev` + Vite proxy to `/api/health` verified with curl; `just gen-api` works. Notes: TypeScript pinned to 5.x (Hey API does not work with TS 7). shadcn CLI not run; `components.json` and `lib/utils.ts` added by hand. Playwright, MapLibre, Recharts not installed yet (later phases). Not a git repo yet, so Lefthook hooks install after `git init` + `just setup`. D-023, D-024 logged.
- 2026-11-16 — Planning done. SPEC, PHASES, DECISIONS, CLAUDE.md written and approved.