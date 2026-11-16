# data/processed/

Made by `just data` (`backend/scripts/build_data.py`) from `data/raw/`. Safe to commit.
Source URLs and download dates are in `data/MANIFEST.csv`. Row counts and checks are in
the data report (kept locally, not in the repo).

| File | What it holds | Source | Licence |
|---|---|---|---|
| `nfhs_districts.parquet` | 704 districts: the 4 target indicators, NFHS-5 and NFHS-4 | NFHS-5 district fact sheets (IIPS/MoHFW) via dhsprogram.com | Govt of India public report; no licence text on the page |
| `nfhs_traits.parquet` | Same 704 districts: trait indicators (never the 4 targets) | NFHS-5 district fact sheets | as above |
| `nfhs_state_traits.parquet` | State/UT values: women bank account, phone, internet | NFHS-5 state fact sheet compendium (Phase I, II) | as above |
| `census2011_districts.parquet` | 640 districts: households, population, children 0-6, SC, ST, literate, workers | Census 2011 Primary Census Abstract, censusindia.gov.in | ORGI public data; no licence stated |
| `census_disability.parquet` | 640 districts: disabled persons (all, 20+, 60+) | Census 2011 table C-20 | as above |
| `census_age.parquet` | 640 districts: all-ages persons, persons aged 60+ and women aged 15-49 (JSY births estimate, D-042) | Census 2011 table C-13 (single-year age) | as above |
| `state_income.parquet` | State/UT per-capita NSDP, current prices, 2021-22 | Economic Survey 2023-24 table 1.11A (state DES via MoSPI), indiabudget.gov.in | Govt of India public report; no licence text |
| `nfhs_sample_sizes.parquet` | 704 districts: households, women and men interviewed (printed on each sheet) | NFHS-5 district fact sheets (`parse_sample_sizes.py`) | as above |
| `nfhs4_state_baseline.parquet` | 37 states/UTs: NFHS-4 state value of health insurance and clean fuel (PM-JAY / PMUY baseline where districts have none, D-046) | NFHS-5 state compendium, NFHS-4 column (`parse_state.py`) | as above |
| `eligible_counts.parquet` | Bases per scheme (households, people, births estimate) | Derived from the Census PCA | as above |
| `district_map.parquet` | NFHS district to Census 2011 district (634 of 704 mapped) | Our join (exact names + reviewed spellings) | Derived; inputs as above |
| `district_traits.parquet` | One row per NFHS district with all traits, `deprivation_score` (beta7), state income (beta2) and flags (`in_v1`, `state_traits_partial_data`) | Derived from the files above | Derived |
| `districts.geojson` | 641 simplified district polygons with `has_census_data`, `has_nfhs_data` | SHRUG v2.1 open district polygons (AIKosh) | **CC BY-NC-SA 4.0**: credit on the About page; non-commercial; share-alike |
| `states.geojson` | 36 state outlines: districts merged by their **current** state (D-045: Telangana and Ladakh are their own), same simplification as the districts, so edges match. Polygon `000` (no name, no state) is left out | Made from the same SHRUG polygons by `scripts/geo.py` | **CC BY-NC-SA 4.0** (same as `districts.geojson`) |

Third-party cross-checks (not used as data): `rohitdwivedula/nfhs5` district list and
`pratapvardhan/NFHS-5` (CC BY 4.0) CSVs.
sheets listed in the district link file.

Notes: NFHS values are survey estimates. Census values are 2011 counts. Trait columns from
the state compendium are the same for every district of a state (`partial_data`).
