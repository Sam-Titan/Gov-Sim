# PROGRESS — GovSim V1

Update after every task. Newest log entries at the top.

## Current phase
**Phase 0 — Setup** (done, waiting for Sam's sign-off)

## Phase status
| Phase | Status | Sam signed off |
|---|---|---|
| 0 Setup | ✅ Done, awaiting review | — |
| 1 Data | ⏳ Not started | — |
| 2 Model | ⏳ Not started | — |
| 3 Fast model + API | ⏳ Not started | — |
| 4 Simulator page | ⏳ Not started | — |
| 5 Other pages | ⏳ Not started | — |
| 6 Downloads + Hindi | ⏳ Not started | — |
| 7 Test + launch | ⏳ Not started | — |

## Current phase tasks
- [x] Folder structure
- [x] uv project + backend deps
- [x] pnpm project + frontend deps
- [x] Justfile
- [x] Ruff / ty / Biome configs
- [x] Lefthook + Gitleaks
- [x] GitHub Actions CI + Dependabot
- [x] `.env.example`, `.gitignore`
- [x] FastAPI `/api/health`
- [x] Vite app calls `/api/health`
- [x] Hey API (`just gen-api`)
- [x] `shared/mocks/` sample

## Waiting on Sam
- Download into `data/raw/` (needed by Phase 1): Ujjwala (Dataful), NSAP pensions (AIKosh),
  district map (AIKosh), Jan Dhan district file (data.gov.in).

## Blockers
- None yet.

## Key results (fill in as phases finish)
- Agent model LOSO MAE: —
- GBM LOSO MAE: —
- Agent model LOSTO MAE: —
- GBM LOSTO MAE: —
- `/simulate` speed: —

## Log
- 2026-11-15 — Phase 0 built. `just setup/check/test` pass; `just dev` + Vite proxy to `/api/health` verified with curl; `just gen-api` works. Notes: TypeScript pinned to 5.x (Hey API does not work with TS 7). shadcn CLI not run; `components.json` and `lib/utils.ts` added by hand. Playwright, MapLibre, Recharts not installed yet (later phases). Not a git repo yet, so Lefthook hooks install after `git init` + `just setup`. D-023, D-024 logged.
- 2026-11-16 — Planning done. SPEC, PHASES, DECISIONS, CLAUDE.md written and approved.