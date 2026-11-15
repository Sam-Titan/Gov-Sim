# PROGRESS — GovSim V1

Update after every task. Newest log entries at the top.

## Current phase
**Phase 1 — Data** (started 2026-11-15)

## Phase status
| Phase | Status | Sam signed off |
|---|---|---|
| 0 Setup | ✅ Done | ✅ Sam, 2026-11-15 |
| 1 Data | 🔧 In progress | — |
| 2 Model | ⏳ Not started | — |
| 3 Fast model + API | ⏳ Not started | — |
| 4 Simulator page | ⏳ Not started | — |
| 5 Other pages | ⏳ Not started | — |
| 6 Downloads + Hindi | ⏳ Not started | — |
| 7 Test + launch | ⏳ Not started | — |

## Current phase tasks
- [ ] Download public files (Census 2011, NFHS-5, pmjdy.gov.in) via `backend/scripts/download_public.py`
- [ ] Fill `data/MANIFEST.csv` for each file
- [ ] Clean each source to Parquet in `data/processed/`
- [ ] District join table (`district_map.parquet`)
- [ ] Eligible counts per scheme per district
- [ ] Jan Dhan: best free district data; log coverage in DECISIONS.md
- [ ] Simplified GeoJSON for the frontend
- [ ] Data report (row counts, missing districts, coverage per state)

## Waiting on Sam
- Download into `data/raw/` (needed by Phase 1): Ujjwala (Dataful), NSAP pensions (AIKosh),
  district map (AIKosh), Jan Dhan district file (data.gov.in).

## Blockers
- `data/raw/` is empty. Sam's four login-only files are not there yet (see above). Public downloads can go ahead; cleaning the four Sam files cannot.
- Open decision: `@testing-library/jest-dom` (removed in Phase 0) — approval not stated; it stays uninstalled.

## Key results (fill in as phases finish)
- Agent model LOSO MAE: —
- GBM LOSO MAE: —
- Agent model LOSTO MAE: —
- GBM LOSTO MAE: —
- `/simulate` speed: —

## Log
- 2026-11-15 — Phase 0 signed off by Sam. D-025 logged (TypeScript 5.x pin). `@hookform/resolvers` approved (not yet installed; add when forms are built). Phase 1 started.
- 2026-11-15 — Phase 0 built. `just setup/check/test` pass; `just dev` + Vite proxy to `/api/health` verified with curl; `just gen-api` works. Notes: TypeScript pinned to 5.x (Hey API does not work with TS 7). shadcn CLI not run; `components.json` and `lib/utils.ts` added by hand. Playwright, MapLibre, Recharts not installed yet (later phases). Not a git repo yet, so Lefthook hooks install after `git init` + `just setup`. D-023, D-024 logged.
- 2026-11-16 — Planning done. SPEC, PHASES, DECISIONS, CLAUDE.md written and approved.