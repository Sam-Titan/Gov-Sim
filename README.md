# GovSim

Test a welfare scheme on a district before launch. A planning aid, not a guarantee.

Government officials pick a district and a scheme (or build a custom one), move sliders for benefit size, documents, bank-account rule, application burden and speed of payment, and see the expected uptake as a **range**, with the top reasons and clear warnings. English and Hindi.

## What V1 covers
- **4 schemes**, each measured through an NFHS indicator (survey proxies, not official sign-up counts): PM-JAY (health cover), PMUY (cooking gas), JSY (institutional births), SBM (toilets).
- **629 districts** with live results on an interactive map. The other 81 say why they have no result.
- **Pages:** Simulator (with custom policy builder), Compare, Model report, About and data.
- **Downloads:** CSV (result, state table, Compare) and a print / PDF view.

## How it works
1. **Real data for the level.** The level shown is the district's NFHS-5 value (2019-21).
2. **Agent model for the change.** 500 synthetic citizens per district, sampled from NFHS-5 and Census 2011 traits, each signing up with a logistic probability. When a slider moves, the average change moves the level (in logit space).
3. **Honest range.** The range combines NFHS sampling error with weak, central and strong assumptions about how people respond.

The agent model is compared with a LightGBM baseline, which is never removed. On held-out states the baseline is more accurate (MAE 10.5 pp against 26.1 pp). This is why the agent model supplies only the change, not the level. Details are on the Model report page.

## Stack
- **Backend:** Python 3.12 (uv), FastAPI, Pydantic, polars, DuckDB, NumPy, SciPy, scikit-learn, LightGBM.
- **Frontend:** Vite, React, TypeScript (strict), Tailwind CSS, TanStack Query, Zustand, MapLibre GL, Recharts, react-i18next. The API client is generated with Hey API.
- **Hosting (planned):** Netlify (frontend) and Render (backend).

## Getting started
Needs `uv`, `pnpm`, `just`.

```
just setup     # install backend and frontend dependencies
just dev       # run backend (port 8000) and frontend (port 5173)
```

| Command | What it does |
|---|---|
| `just check` | Ruff, ty, Biome, TypeScript |
| `just test` | pytest and vitest |
| `just e2e` | Playwright end-to-end tests |
| `just gen-api` | regenerate the TypeScript client from the FastAPI schema |
| `just data` | data pipeline (downloads and parses public data) |
| `just train` | calibrate the agent model, train the baseline, write the report |

Secrets, if ever needed, go in `.env` (git-ignored). Add new keys to `.env.example` with a blank value. V1 needs none.

## Folders
- `backend/` FastAPI app, model code (`govsim/`), data scripts, `artifacts/` (report and fitted values)
- `frontend/` React app
- `data/` processed tables and GeoJSON (`data/raw/` is git-ignored); every file is listed in `data/MANIFEST.csv`
- `shared/` mocks for frontend work and tests
- `docs/` spec, phases, progress, decisions, data report, deploy guide, changelog

## Limits
- Levels are survey estimates and carry sampling error.
- With only four schemes, most design effects rest on assumed values.
- Census 2011 populations are old. 70 newer districts have no 2011 parent and no result.
- District boundaries are approximate and not authoritative.
- The Hindi text is a draft until a fluent speaker reviews it.

## Docs
- Spec: `docs/SPEC.md`
- Deploy steps: `docs/DEPLOY.md`
- Release notes: `docs/CHANGELOG.md`

## Data and licences
Sources and licences for every file are in `data/MANIFEST.csv` and `data/processed/README.md`. NFHS-5 is from IIPS and ICF via the DHS Program. The district map is SHRUG v2.1 (Development Data Lab), CC BY-NC-SA 4.0, and must keep that licence and credit. The repository itself has no licence (all rights reserved).
