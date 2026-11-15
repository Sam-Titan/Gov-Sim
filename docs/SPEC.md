# SPEC — GovSim V1

Status: approved by Sam, 2026-11-16. Change only with Sam's approval (log it in DECISIONS.md).

## 1. Goal
Help **government officials** see how the public will react to a welfare scheme **before**
they launch it.

For a scheme **S** and a district **D**, GovSim predicts:
> the share of **eligible** people/households in D who sign up for S.

Metric: MAE (mean absolute error) in percentage points, on held-out data.

## 2. Users
- Main: government officials (policy and planning staff).
- They are not data scientists. Use plain words, clear labels, and honest uncertainty.

## 3. Schemes in V1 (5)
| Code | Scheme | Eligible group (estimate) | Sign-up data |
|---|---|---|---|
| `pmuy` | Pradhan Mantri Ujjwala Yojana (LPG) | Poor households without LPG | Dataful (free), district, 2017–2026 |
| `pmjdy` | Pradhan Mantri Jan Dhan Yojana (bank accounts) | Adults/households without a bank account | data.gov.in (2019) + pmjdy.gov.in — see note |
| `nsap_oap` | NSAP Old Age Pension (IGNOAPS) | BPL people aged 60+ | AIKosh NSAP district file |
| `nsap_wp` | NSAP Widow Pension (IGNWPS) | BPL widows aged 40+ | AIKosh NSAP district file |
| `nsap_dp` | NSAP Disability Pension (IGNDPS) | BPL people 18+ with severe disability | AIKosh NSAP district file |

**Jan Dhan note:** Jan Dhan is in V1. The known free district file may cover only some
states. In Phase 1, find the best free district data (data.gov.in, pmjdy.gov.in reports,
Parliament answers). If only some states are covered, train Jan Dhan on those states and
mark the other states "less certain" in the UI. Log what was found in DECISIONS.md.

Not in V1: PM-KISAN, Ayushman Bharat, MoSJE schemes.

## 4. Data
All free. No paid ("Exclusive") Dataful files. No data.gov.in API key.

| Data | Source | Downloaded by |
|---|---|---|
| Ujjwala sign-ups | Dataful "Year, State and District wise PMUY Connections" | Sam |
| Jan Dhan sign-ups | data.gov.in district file (2019); pmjdy.gov.in Excel reports | Sam (data.gov.in), Claude Code (pmjdy.gov.in) |
| NSAP pensions | AIKosh "District-wise Pension data under NSAP" | Sam |
| District map | AIKosh "2011 population census district polygon geometries" (CC BY-NC-SA 4.0) | Sam |
| Population | Census 2011 district tables | Claude Code |
| Household traits | NFHS-5 district fact sheets | Claude Code |

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
- Each district gets N synthetic agents (default 500, seed 42) sampled from Census 2011 +
  NFHS-5 shares: age band, gender, widow, disability, rural/urban, BPL, literate,
  has bank account, has internet/phone, has LPG, household income band.
- An agent is eligible if it matches the scheme's target group.
- An eligible agent signs up with probability `sigmoid(z)`, where z uses 9 β values:

| β | Meaning |
|---|---|
| β0 | Baseline (intercept) |
| β1 | Trust in government (no direct data in V1 — district-level latent value with a fixed prior; documented assumption) |
| β2 | Cash benefit relative to household income |
| β3 | Documents needed × illiterate |
| β4 | Digital-only application × no internet |
| β5 | Application burden (steps/visits, 1–5) |
| β6 | Benefit speed (1–5) |
| β7 | District deprivation |
| β8 | Bank account needed × unbanked |

- Calibrate β with scipy (Nelder-Mead) to match real district uptake.
- Check: β recovery test on simulated data (as in the demo bulletin).

### 5.2 Baseline
- LightGBM (GBM) trained directly on district features → uptake. **Never deleted.**

### 5.3 Evaluation
- LOSO: leave-one-scheme-out (headline).
- LOSTO: leave-one-state-out (geographic test).
- Report MAE (pp) for agent model vs GBM. Known weakness: few schemes → noisy LOSO.

### 5.4 Fast surrogate (instant sliders)
- Run the calibrated agent model on many random slider settings × all districts.
- Train LightGBM quantile models (10th / 50th / 90th percentile) on those runs → range.
- Save with joblib to `backend/artifacts/`.
- **Reasons:** top 3 β terms that change uptake most for that district (from the agent
  model's terms, averaged over the district's agents).
- **Warnings:**
  - `out_of_range`: a slider is outside the values seen in training.
  - `new_policy`: a custom policy is far from all real schemes → wider range + label.
  - `partial_data`: the scheme has no real data for this state (e.g. Jan Dhan).

## 6. Scheme inputs (sliders)
| Field | Type | Range |
|---|---|---|
| `cash_benefit_inr` | number | 0 – 50,000 |
| `document_count` | int | 0 – 8 |
| `digital_only` | bool | — |
| `requires_bank_account` | bool | — |
| `application_burden` | int | 1 – 5 |
| `benefit_immediacy` | int | 1 – 5 |
| `target_group` | object | custom policies only (see §7.2) |

Real schemes load with their real default values. Ranges are final once Phase 2 shows the data.

## 7. Pages
### 7.1 Simulator (`/`)
- Pick state → district (dropdown or click on the MapLibre map).
- Pick scheme, or "+ Custom policy".
- Sliders (§6).
- Result: uptake range (e.g. 28–35%), mid value, top 3 reasons, warnings.
- Map: the chosen state's districts coloured by predicted uptake.
- Download: CSV, and "Print / Save as PDF".

### 7.2 Custom policy (inside Simulator)
- Name the policy.
- Target group from traits we have: age band, gender, widow, disability, rural/urban, BPL,
  no LPG, unbanked.
- The same sliders. Always shows the `new_policy` label when far from real schemes.

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
| GET | `/schemes` | 5 schemes with default slider values and allowed ranges |
| POST | `/simulate` | One district + scheme input → range, reasons, warnings |
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
  good `#0ca30c`, warn `#b9820a`. Dark tokens as in the demo bulletin.
- Report-style panels, thin borders, 4px radius. Tables with right-aligned mono numbers.

## 10. Toolkit (locked — new tools need Sam's approval)
- **Setup:** WSL2 (Ubuntu), uv, pnpm (corepack), Node 24, just, Git + GitHub, Lefthook + Gitleaks, Claude Code
- **Backend:** FastAPI + Uvicorn, Pydantic + pydantic-settings, httpx
- **Data/model:** polars, DuckDB, pyarrow, openpyxl, numpy, scipy, scikit-learn, LightGBM, joblib, geopandas, shapely
- **Frontend:** Vite, React + TypeScript, Tailwind CSS v4 + shadcn/ui + lucide-react, TanStack Query, Zustand, React Router, react-hook-form + zod, Motion + sonner, MapLibre GL (react-map-gl), Recharts, react-i18next
- **Glue:** Hey API (`@hey-api/openapi-ts`), `shared/mocks/`, `.env`
- **Quality:** Ruff + ty, Biome, pytest, vitest, Playwright + `@playwright/mcp`, GitHub Actions + Dependabot
- **Hosting:** Netlify (frontend), Render free plan (backend), Sentry
- **Optional (approved, only if time allows):** Lighthouse CI, Locust, PostHog, SlowAPI, Docker + Compose
- **Not used:** LLM/agent libraries, databases, Redis/queues, auth, 3D tools, Caddy, Orval, PDF libraries

## 11. Out of scope for V1
Logins, saving policies on the server, live data refresh, PM-KISAN/Ayushman, sub-district results.

## 12. Repo and git
- Repo: `Gov-Sim`, public, no licence (all rights reserved).
- Sam makes every commit and push. Claude Code never commits, pushes, or adds AI credit.
- Releases: git tags `v1.0`, `v1.1`… with a CHANGELOG entry.