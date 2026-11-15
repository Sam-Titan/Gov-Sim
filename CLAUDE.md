# CLAUDE.md — Gov-Sim

Read this file first, every session. Then read `docs/PROGRESS.md` to see where we are.

## What this project is
GovSim V1: a website where government officials test a welfare scheme **before** launch.
They pick a district and a scheme (or build a custom one), move sliders, and see the
expected uptake as a range. Full details: `docs/SPEC.md`.

## Docs you must keep in sync
| File | What it holds | When to update |
|---|---|---|
| `docs/SPEC.md` | What we build | Only after Sam approves a change |
| `docs/PHASES.md` | The 8 phases and their "done when" checks | Only after Sam approves a change |
| `docs/PROGRESS.md` | Current phase, done/next tasks, blockers | After every task |
| `docs/DECISIONS.md` | Every decision, with date and reason | When Sam approves a decision |
| `docs/CHANGELOG.md` | Release notes | At each release tag |
| `data/MANIFEST.csv` | Every data file: source, date, licence, who downloaded | When a data file is added |

## Non-negotiable rules
1. **Git: never commit, push, tag, or amend.** Sam makes every commit and push under his
   own name. You may run read-only git commands (`git status`, `git diff`, `git log`).
   At the end of a task, suggest a short commit message. Never add `Co-Authored-By`,
   "Generated with Claude", or any Claude/Anthropic credit anywhere — not in commit
   messages, PR text, code comments, or docs.
2. **Toolkit is locked.** Only use tools listed in `docs/SPEC.md` § Toolkit. If you think
   a new package is needed, stop and ask Sam. Do not install it first.
3. **Phases are gated.** Work only on the current phase in `docs/PROGRESS.md`. At the end
   of a phase: run `just check` and `just test`, update PROGRESS.md, then stop and wait
   for Sam's sign-off.
4. **No made-up data.** Real data only (except `shared/mocks/` for frontend work and
   tests). Never invent numbers, district names, or sources. If data is missing, say so in
   PROGRESS.md under Blockers.
5. **Raw data is never committed.** `data/raw/` is git-ignored. Sam downloads login-only
   files by hand. You download public files with scripts in `backend/scripts/`.
6. **The GBM baseline is never deleted.** The agent model must always be compared to it.
7. **Be honest in the UI.** Always show a range, not one number. Show warnings when inputs
   go outside the training data or a custom policy is far from real schemes.
8. **Both languages.** Every user-facing string goes through react-i18next
   (`frontend/src/i18n/en.json` and `hi.json`). No hard-coded UI text.
9. **Secrets** live only in `.env` (git-ignored). Add new keys to `.env.example` with a
   blank value.

## Commands (Justfile)
- `just setup` — install backend (uv) and frontend (pnpm) dependencies
- `just dev` — run backend + frontend together
- `just check` — Ruff, ty, Biome, TypeScript
- `just test` — pytest + vitest
- `just e2e` — Playwright tests
- `just gen-api` — regenerate TypeScript client from FastAPI `openapi.json` (Hey API)
- `just data` — run the data pipeline (Phase 1)
- `just train` — calibrate the agent model, train baseline + surrogate (Phases 2–3)

## Code style
- Python 3.12, managed by uv. Type hints everywhere. Pydantic models for all API input/output.
- Data work in polars / DuckDB. Store tables as Parquet in `data/processed/`.
- Frontend: React + TypeScript strict mode. Server data via TanStack Query hooks from
  `frontend/src/api/` (generated — never edit by hand). UI state in Zustand.
- Keep functions small. Write a test for every new module or route.
- Answers to Sam: short, simple language.

## Look and feel
Copy the demo bulletin style: IBM Plex Serif / Sans / Mono (+ IBM Plex Sans Devanagari for
Hindi), light and dark mode, report-style panels, colour tokens in `docs/SPEC.md` § Design.