# PHASES — GovSim V1

Approved by Sam, 2026-11-16. Work on one phase at a time.

**End of every phase:**
1. `just check` and `just test` pass.
2. Claude Code updates `docs/PROGRESS.md` and suggests a commit message (no AI credit).
3. Sam reviews, commits, and pushes.
4. Sam signs off. Only then does the next phase start.

---

## Phase 0 — Setup
- Folder structure, `pyproject.toml` (uv), `package.json` (pnpm), `Justfile`.
- Ruff, ty, Biome configs. Lefthook (lint + type check + Gitleaks on commit).
- GitHub Actions CI (check + test) and Dependabot.
- `.env.example`, `.gitignore` (incl. `data/raw/`, `.env`).
- Empty FastAPI app with `/api/health`; empty Vite React app that calls it via the Vite proxy.
- Hey API wired up (`just gen-api`).
- `shared/mocks/` with one sample `/simulate` response.

**Done when:** `just setup`, `just dev`, `just check`, `just test` all work on the empty app.

## Phase 1 — Data
- Sam puts login-only files in `data/raw/` (Ujjwala, NSAP, map, data.gov.in Jan Dhan).
- Scripts download public files (Census 2011, NFHS-5, pmjdy.gov.in).
- Clean each source → Parquet in `data/processed/`.
- District join table (Census 2011 codes, LGD codes, split districts → 2011 parent).
- Estimate "eligible" counts per scheme per district.
- Jan Dhan: find the best free district data; record coverage in DECISIONS.md.
- Simplify the map → GeoJSON for the frontend (keep CC BY-NC-SA credit).
- Fill `data/MANIFEST.csv`.

**Done when:** one clean uptake table per scheme, one population/traits table, one map
file, and a data report (row counts, missing districts, coverage per state).

## Phase 2 — Model
- Agent sampler per district (seeded).
- Eligibility rules per scheme.
- Adoption model (9 β) + Nelder-Mead calibration.
- β recovery test on simulated data.
- LightGBM baseline.
- LOSO and LOSTO evaluation → `report.json`.

**Done when:** MAE numbers for agent model vs GBM are recorded in PROGRESS.md, and the
β values make sense (signs as expected).

## Phase 3 — Fast model + API
- Generate many agent-model runs (random sliders × districts).
- Train LightGBM quantile surrogate (p10 / p50 / p90). Check it against the agent model.
- Reasons (top 3 terms) and warnings (`out_of_range`, `new_policy`, `partial_data`).
- All routes in SPEC §8 with Pydantic models. Regenerate client with Hey API.

**Done when:** every route works, has tests, and `/simulate` answers in under 200 ms.

## Phase 4 — Simulator page
- App shell, demo style, light/dark mode, i18n set-up (EN + HI keys from the start).
- "Waking up the server…" screen.
- State/district picker + MapLibre map (click a district).
- Scheme picker, sliders, result range, top 3 reasons, warnings.
- State map coloured by uptake.

**Done when:** an official can run a full simulation for any district on one page.

## Phase 5 — Other pages
- Custom policy builder (inside Simulator).
- Compare page.
- Model report page.
- About / Data page (sources, licences, map credit, disclaimer).

**Done when:** all pages and the custom policy builder work with the real API.

## Phase 6 — Downloads + Hindi
- CSV download of results.
- Print-friendly results view ("Save as PDF").
- Full Hindi translation of every string. Check Devanagari font on all pages.

**Done when:** every page works in both languages, and both downloads open correctly.

## Phase 7 — Test + launch
- Playwright end-to-end tests for the main flows.
- Fix bugs. (Optional: Lighthouse CI, Locust.)
- Deploy: frontend to Netlify (forward `/api` to Render), backend to Render.
- Sentry on frontend + backend.
- `docs/CHANGELOG.md` entry. Sam tags `v1.0`.

**Done when:** the live site works end to end, including the wake-up screen.