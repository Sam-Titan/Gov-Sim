# SPEC — GovSim V1

Status: approved by Sam, 2026-11-16; schemes and data changed 2026-11-15 (D-028). Change only with Sam's approval (log it in DECISIONS.md).

## 1. Goal
Help **government officials** see how the public will react to a welfare scheme **before**
they launch it.

For a scheme **S** and a district **D**, GovSim predicts:
> the share of **all households / births / people** in D that are covered by S, as
> measured by the NFHS survey (D-030).

(Earlier drafts said "share of eligible people". With NFHS-based schemes the target is the
NFHS percentage. The agent model still uses the eligible group inside, to decide who can
sign up. The UI must always say "share of all households" (or "of all births" / "of all
people"), never "uptake among eligible".)

Metric: MAE (mean absolute error) in percentage points, on held-out data.

## 2. Users
- Main: government officials (policy and planning staff).
- They are not data scientists. Use plain words, clear labels, and honest uncertainty.

## 3. Schemes in V1 (4)
All four are **proxy** schemes: the sign-up number is an NFHS survey indicator that is
mostly, but not only, caused by the named scheme. None is a "clear" single-scheme count.
(Changed 2026-11-15, D-028: the earlier admin-count schemes had no public, scriptable
district data.)

| Code | Scheme | NFHS indicator (district sheet no.) | Label | Eligible group (estimate) | Why it is only a proxy |
|---|---|---|---|---|---|
| `pmjay` | PM-JAY (Ayushman Bharat health cover) | Households with any usual member covered under a health insurance/financing scheme (#12) | proxy | All households (Census 2011); no BPL data in V1 | Also counts RSBY, state schemes, ESIS, private cover. PM-JAY was not fully rolled out when NFHS-5 was surveyed |
| `pmuy` | PM Ujjwala Yojana (LPG) | Households using clean fuel for cooking (#10) | proxy | All households (Census 2011); no BPL or LPG data in V1 | "Clean fuel" = electricity, LPG/natural gas or biogas, bought with or without PMUY |
| `jsy` | Janani Suraksha Yojana (cash for institutional delivery) | Institutional births, births in the 5 years before the survey (#42) | proxy | Mothers giving birth (births estimate from Census 2011) | Includes births in private facilities and births that did not receive JSY cash |
| `sbm` | Swachh Bharat Mission (toilets) | Population in households using an improved, not shared, sanitation facility (#9) | proxy | Households without a toilet (rural focus) | Includes toilets built by the household itself and before the Mission |

Time points: NFHS-5 (2019-21) and NFHS-4 (2015-16), both read from the same NFHS-5 district
sheet. Telangana sheets have NFHS-5 only (districts were re-drawn, no NFHS-4 column).
Chandigarh is not included.

**Survey estimates, not admin counts.** NFHS values come from a sample survey (about
700-1,000 households per district) and carry sampling error. Every result for these
schemes is shown with the `survey_estimate` warning (§5.4).

**Metric (D-030):** for these four schemes the number we predict is the NFHS share of **all**
households (PM-JAY, PMUY), **all births** in the last 5 years (JSY) or **all people** (SBM),
not the share of the eligible group. The agent model still uses the eligible group to
decide who can sign up; calibration compares the model's overall covered share to the NFHS
value. Every result in the UI carries this label (EN + HI), e.g. "Share of all households
covered".

Not in V1: NSAP pensions, Ujjwala admin counts, Jan Dhan, PM-KISAN, Ayushman Bharat admin
data, MGNREGA (MIS reports need a captcha and checked URLs, so they cannot be scripted).

## 4. Data
All free, public, and downloadable by script. No paid ("Exclusive") Dataful files. No
data.gov.in (blocks bots) and no API key.

| Data | Source | Downloaded by |
|---|---|---|
| Scheme sign-up proxies (4 indicators x 2 time points) | NFHS-5 district fact sheets (PDF), DHS Program `dhsprogram.com/pubs/pdf/OF43/`; read with `pdftotext` in the data scripts only (D-029) | Claude Code (`backend/scripts/download_public.py`, `parse_nfhs.py`) |
| District list for the PDFs | `rohitdwivedula/nfhs5` `districtwise_links.csv`; Telangana names from `pratapvardhan/NFHS-5` (CC BY 4.0, also a cross-check) | Claude Code |
| District map | SHRUG v2.1 open district polygons, hosted on AIKosh (CC BY-NC-SA 4.0): `aikosh.indiaai.gov.in/home/datasets/details/2011_population_census_district_polygon_geometries.html` | Sam |
| Population and households | Census 2011 Primary Census Abstract, state and district level (`DDW_PCA0000_2011_Indiastatedist.xlsx`, ORGI Census Digital Library, table PC11_PCA-SD, `censusindia.gov.in/nada/index.php/catalog/6191`). District codes match the map's `pc11_d_id`. Licence not stated on the page; Govt of India public data | Claude Code |
| Household traits | NFHS-5 district fact sheets (same PDFs) | Claude Code |

**NFHS caveat:** values are survey estimates (sample size per district is printed on each
sheet). Values marked `*` (fewer than 25 cases) are missing; values in brackets are based
on 25-49 cases and are flagged.

Rules:
- Every file gets a row in `data/MANIFEST.csv`: `file, source_url, downloaded_on, licence, downloaded_by, notes`.
- `data/raw/` is git-ignored. Processed Parquet files needed by the live API go in
  `data/processed/` (committed only if small and the licence allows).
- Districts are joined by Census 2011 code (and LGD code where available). Districts split
  after 2011 are mapped back to their 2011 parent. Keep the mapping table in
  `data/processed/district_map.parquet`.
- The map is CC BY-NC-SA 4.0: credit it on the About page. Any derived map file keeps the
  same licence.

## 5. Model
### 5.1 Agent model (explainable core)
- Each district gets N synthetic agents (default 500, seed 42) sampled from district traits
  (`data/processed/district_traits.parquet`, D-035, D-036). Traits and their source level:
  - **District, NFHS-5:** female school attendance, population below 15, sex ratio, birth
    registration, women literate, women with 10+ years of schooling, women married before
    18. (Survey estimates.)
  - **District, Census 2011:** rural share, female share, children 0-6, age 60+, SC, ST,
    literacy 7+, worker share, disabled share (all ages, 20+, 60+). Uses the mapped 2011
    district.
  - **State only, flagged `partial_data`:** women with a bank account, mobile phone,
    internet use (NFHS-5), and per-capita income (NSDP 2021-22, Economic Survey table
    1.11A). The same value for every district of a state. The UI says so when these drive a
    result. Income is null for Ladakh and Dadra & Nagar Haveli and Daman & Diu.
  - **Dropped, no free source:** BPL, household income band. **Dropped, leakage:** "has
    LPG" (the PMUY target) and electricity (overlaps the PMUY target). **Dropped, only 13
    states:** widows (Census C-02, D-036).
  - **Never used as traits (leakage):** the 4 target indicators and their close relatives;
    full list in the data report (kept locally, not in the repo). Checked: no trait has |r| above 0.7 with a target.
- An agent is eligible if it matches the scheme's target group.
- An eligible agent signs up with probability `sigmoid(z)`, where z uses 8 β values (β4 was removed, D-031):

| β | Meaning |
|---|---|
| β0 | Baseline (intercept) |
| β1 | Trust in government (no direct data in V1 — district-level latent value with a fixed prior; documented assumption) |
| β2 | Benefit value relative to income (cash or cash-equivalent value, e.g. insurance cover). Income = the state per-capita NSDP trait (2021-22, nominal), same for all districts of a state, divided by 12 (monthly income, D-040); a national figure was not needed (D-036). Weakly estimated; PM-JAY value set from official guidelines in Phase 2 and cited |
| β3 | Documents needed × illiterate. Weakly estimated |
| β5 | Application burden (steps/visits, 1–5). Weakly estimated |
| β6 | Benefit speed (1–5). Weakly estimated |
| β7 | District deprivation. Score = mean of six sign-adjusted z-scores over the 704 NFHS districts (women literate, women 10+ years schooling, female school attendance, birth registration: low is deprived; women married before 18, population below 15: high is deprived). Non-leaking NFHS-5 traits only (D-036) |
| β8 | Bank account needed × unbanked. Weakly estimated; dropped in Phase 2 if it cannot be estimated (D-031) |

- **β handling (D-039):** β2, β3, β5, β6, β8 are fixed assumed values, each with a low and a high value (shown on the report page, labelled "assumed by team" or with a citation). β1 is fixed (assumed). Only β0 and β7 (and the nuisance `era_shift`) are fitted, with scipy Nelder-Mead to NFHS district values, common random numbers.
- The agent model is used for **slider changes only** (D-052). The change is applied to the **whole level** in logit space: `new level = sigmoid(logit(NFHS-5 level) + mean Δz)`, where Δz is the change in z from the scheme's real settings to the user's settings, averaged over the eligible agent types. There is no baseline term in a slider change. The baseline b (D-038) is only used when fitting β0 and β7.
- Check: β recovery test on simulated data (as in the demo bulletin), now for the fitted terms.

### 5.2 Baseline (also the district-level predictor, D-039)
- The GBM is the baseline in the model report (D-041). The "from data" level shown to users is the actual NFHS-5 value of the district.
- LightGBM (GBM) trained directly on district features → uptake. **Never deleted.**

### 5.3 Evaluation
- **LOSTO: leave-one-state-out (headline, D-039).**
- LOSO: leave-one-scheme-out. Kept in the report with the note that 4 schemes are too few: held-out schemes have slider values never seen in training, so no model predicts them well.
- Report MAE (pp) for agent model vs GBM. **The agent model does not beat the GBM** (Phase 2: LOSTO 14.1 vs 10.5 pp; LOSO 32.1 vs 30.8 pp); the report page says so. Known weaknesses:
  - Only 4 schemes, all survey proxies from one survey (NFHS), so scheme-feature effects
    (β2, β3, β5, β6, β8) are weakly identified and LOSO is noisy. Differences between schemes are
    partly differences between survey questions.
  - Some sliders barely vary across the 4 schemes (see PROGRESS.md); their β cannot be
    learned from the data and rest on priors.
  - Time: two points (NFHS-4, NFHS-5) only; no Telangana NFHS-4.

### 5.4 Fast answers (instant sliders, live model)
- **Output (D-039, D-041):** result = actual NFHS-5 value of the district ("from data") + agent-model change from the scheme's real settings to the user's settings ("model assumption"), the whole level moved in logit space by the average Δz of the eligible agents (D-052). Custom policies: the user picks a real scheme to start from; always the `new_policy` label.
- **Range (D-040, D-041)** = NFHS sampling band (SE = sqrt(deff x p(1-p)/n), n = households from the sheet, or estimated births for JSY (D-042), deff 2 assumed, 10th-90th pct) + the spread of the slider change across the weak / central / strong β sets, added end to end. `low_confidence` label when wider than 30 pp.
- **No surrogate (D-043).** The anchored agent model runs live for every request at the three β sets (weak / central / strong): about 6 ms for one district, 25 ms for all 629 districts.
- **Reasons:** top 3 slider terms that change the result most for that district (each term switched on alone, same logit rule, central β set).
- **Custom policy (D-052):** the shift of z is found so everyone eligible, at the real settings, has the start scheme's NFHS level; the target group's own level at the real settings follows from it, and the new settings move that level by the group's mean Δz.
- **Small changes:** a slider change under 0.5 pp is expected only where the level is 90% or more or 10% or less (ceiling / floor).
- **Warnings:**
  - `out_of_range`: a slider is outside the values seen in training.
  - `new_policy`: a custom policy is far from all real schemes → wider range + label.
  - `partial_data` (D-053): the result uses a state-level figure that is the same for every district of the state (bank accounts, per-capita income): when the benefit slider or the bank-requirement switch is moved, or a custom policy filters on "unbanked" or requires a bank account. Not shown for an imputed baseline. Text: "This result uses state-level figures (bank accounts, income) that are the same for every district in the state."
  - `low_confidence`: the range is wider than 30 pp.
  - `survey_estimate`: shown on every result for the 4 NFHS schemes. Text: "Based on a
    household survey (NFHS), not official sign-up counts. District values carry sampling
    error and cover more than this scheme alone." Both languages.

## 6. Scheme inputs (sliders)
| Field | Type | Range |
|---|---|---|
| `cash_benefit_inr` | number | 0 – 5,00,000 (PM-JAY: ₹2,50,000 – ₹10,00,000, half to double the real cover), log-scale slider (benefit value; β2 uses `log(1 + benefit / income)`; PM-JAY is labelled "non-cash cover"; D-037) |
| `document_count` | int | 0 – 8 |
| `requires_bank_account` | bool | — |
| `application_burden` | int | 1 – 5 |
| `benefit_immediacy` | int | 1 – 5 |
| `target_group` | object | custom policies only (see §7.2) |

Real schemes load with their real default values (D-037; JSY by state group and rural/urban). Ranges are final once Phase 2 shows the data.
Removed: `digital_only` (D-031). `requires_bank_account` stays until Phase 2 shows whether it can be estimated.

## 7. Pages
### 7.1 Simulator (`/`)
- Pick state → district (dropdown or click on the MapLibre map).
- Pick scheme, or "+ Custom policy".
- Sliders (§6).
- Result: uptake range (e.g. 28–35%), mid value, top 3 reasons, warnings.
- Map: the chosen state's districts coloured by predicted uptake.
- Download: CSV, and "Print / Save as PDF". CSV (Simulator result, state table, Compare result): UTF-8 with BOM, language follows the page, text cells starting with `=`, `+`, `-`, `@` get a `'` prefix (numbers stay numbers), every row carries the scenario link, the date and the model/data version (`generated` date of `report.json`). Print view adds the settings used, the same link, date and version, the sources line and the disclaimer; map, menu and controls are hidden, light colours (D-054).

### 7.2 Custom policy (inside Simulator)
- Name the policy.
- Target group from traits we have: age band (incl. 60+), gender, disability, rural/urban,
  unbanked (state-level, `partial_data`). Not offered: widow, BPL, no LPG (D-036).
- The same sliders, and a real scheme to start from (its NFHS level anchors the model).
- **Result (D-044):** the **uptake within the target group** (% of the group, with a range) and
  the **estimated number reached** (households for PM-JAY and PMUY, births for JSY, people for
  SBM; Census 2011 base x group share x uptake; "estimated"). It is **not** the share of all
  households, and the UI must say so ("of the target group", "estimated, Census 2011 base").
  Not comparable with a real scheme's share of all; Compare shows no difference between the two.
- Always shows the `new_policy` label. Groups under 10 of the 500 sampled agents are too small
  to model (`group_too_small`).

### 7.3 Compare (`/compare`)
- Two settings (A and B) for the same district, side by side, with the difference.

### 7.4 Model report (`/report`)
- Like the demo bulletin: data overview, scheme features, LOSO/LOSTO agent vs GBM,
  β recovery, known weaknesses.

### 7.5 About / Data (`/about`)
- Sources, licences (map credit), limits, disclaimer: "A planning aid, not a guarantee."

### 7.6 All pages
- English / Hindi switch (react-i18next). Light / dark mode.
- "Waking up the server…" message while the Render backend starts (polls `/api/health`).

## 8. API (FastAPI, prefix `/api`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Wake-up check |
| GET | `/states` | States list |
| GET | `/districts?state=` | Districts in a state (codes, names in EN/HI) |
| GET | `/schemes` | 4 schemes with default slider values and allowed ranges |
| POST | `/simulate` | One district + scheme input → range, reasons, warnings (custom policy: group uptake + reach) |
| POST | `/simulate/state` | One state + scheme input → uptake per district (for the map) |
| POST | `/compare` | One district + inputs A and B → both results + difference |
| GET | `/report` | Model report data |

All request/response bodies are Pydantic models. The frontend client is generated with
Hey API — never hand-written.

## 9. Design
- Fonts: IBM Plex Serif (headings), IBM Plex Sans (body), IBM Plex Mono (numbers),
  IBM Plex Sans Devanagari (Hindi).
- Colour tokens (light): bg `#f5f5f2`, surface `#ffffff`, ink `#15161a`, line `#dedcd2`,
  accent `#204a7d`, agent series `#2a78d6`, GBM series `#eb6834`, stamp/alert `#b7342f`,
  good `#0ca30c`, warn `#b9820a`; plus (from the demo bulletin, Sam 2026-11-16) surface-2 `#edece6`,
  ink-muted `#55575f`, ink-faint `#85868d`, line-strong `#c7c5b8`, accent-soft `#e4ecf6`,
  stamp-soft `#f7e3e0`.
- Colour tokens (dark, from the demo bulletin, given by Sam 2026-11-16): bg `#131311`,
  surface `#1c1c19`, surface-2 `#232320`, ink `#f2f1ea`, ink-muted `#c3c1b5`, ink-faint
  `#8f8d81`, line `#35342e`, line-strong `#46453d`, accent `#7fa9db`, accent-soft `#1e2c3d`,
  agent series `#3987e5`, GBM series `#d97a4e`, stamp/alert `#e2726d`, stamp-soft `#3a201f`,
  good `#3fbf3f`, warn `#d9a53a`.
- Map: the unnamed polygon `000` is always "no data" grey, not clickable, and outlined like a state edge (no gap in India's outline). States are outlined by merging districts by their current state (D-045); the map shows
  the note "District boundaries are approximate and not authoritative" (EN + HI).
- Report-style panels, thin borders, 4px radius. Tables with right-aligned mono numbers.

## 10. Toolkit (locked — new tools need Sam's approval)
- **Setup:** WSL2 (Ubuntu), uv, pnpm (corepack), Node 24, just, Git + GitHub, Lefthook + Gitleaks, Claude Code
- **Backend:** FastAPI + Uvicorn, Pydantic + pydantic-settings, httpx
- **Data/model:** polars, DuckDB, pyarrow, openpyxl, xlrd (data scripts only, old `.xls` Census tables),  numpy, scipy, scikit-learn, LightGBM, joblib, geopandas, shapely
- **Frontend:** Vite, React + TypeScript, Tailwind CSS v4 + shadcn/ui + lucide-react, TanStack Query, Zustand, React Router, react-hook-form + zod, Motion + sonner, MapLibre GL (react-map-gl), Recharts, react-i18next
- **Glue:** Hey API (`@hey-api/openapi-ts`), `shared/mocks/`, `.env`
- **Quality:** Ruff + ty, Biome, pytest, vitest, Playwright + `@playwright/mcp`, GitHub Actions + Dependabot
- **Hosting:** Netlify (frontend), Render free plan (backend)
- **Optional (approved, only if time allows):** Lighthouse CI, Locust, PostHog, SlowAPI, Docker + Compose
- **Not used:** LLM/agent libraries, databases, Redis/queues, auth, 3D tools, Caddy, Orval, PDF libraries

## 11. Out of scope for V1
Logins, saving policies on the server, live data refresh, PM-KISAN/Ayushman, sub-district results.

## 12. Repo and git
- Repo: `Gov-Sim`, public, no licence (all rights reserved).
- Sam makes every commit and push. Claude Code never commits, pushes, or adds AI credit.
- Releases: git tags `v1.0`, `v1.1`… with a CHANGELOG entry.