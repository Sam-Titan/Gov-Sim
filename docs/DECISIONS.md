# DECISIONS — GovSim V1

Every decision has a date and a reason. Add new ones at the bottom. Never delete old ones;
if a decision changes, add a new entry that replaces it.

## D-001 — Product is a simulator (2026-11-15)
Interactive "what-if" simulator, not a read-only report. The report is a separate page.
**Why:** officials need to test a policy before launch.

## D-002 — Audience is government officials (2026-11-15)
**Why:** stated by Sam. Means plain language, honest uncertainty, no overclaiming.

## D-003 — Real data in V1 (2026-11-15)
**Why:** a demo for officials needs real districts.

## D-004 — Hybrid model with fast surrogate (2026-11-15)
Calibrate the agent model (9 β) on real data → run it many times → train a LightGBM
surrogate for instant slider results. Keep the GBM baseline. Show a range and warnings.
**Why:** instant answers that can still be explained; too few real schemes to train ML
directly on real uptake.

## D-005 — V1 schemes (2026-11-16, replaces 2026-11-15 versions)
5 schemes: Ujjwala (PMUY), Jan Dhan (PMJDY), NSAP old age, widow and disability pensions.
Jan Dhan is fully in V1. If free district data covers only some states, train on those and
mark other states "less certain".
**Why:** Sam's decision. These schemes have district-level data. PM-KISAN and Ayushman
only have district data for some states, so they are out.

## D-006 — Free data only (2026-11-15)
No "Exclusive" (paid) Dataful files.
**Why:** stated by Sam.

## D-007 — Population data (2026-11-15)
Census 2011 district tables + NFHS-5 district fact sheets.
**Why:** free, district-level, and cover the agent traits.

## D-008 — Toolkit (2026-11-15)
As in SPEC §10. Added data, model, map, chart and i18n tools. No LLM, database, Redis,
auth or 3D tools in V1.
**Why:** keep V1 simple; data is pre-computed and the surrogate is fast.

## D-009 — MapLibre for maps (2026-11-15)
**Why:** chosen by Sam; zoomable and richer than d3-geo.

## D-010 — Hey API, not Orval (2026-11-15)
**Why:** one tool only.

## D-011 — Pages (2026-11-15)
Simulator, Compare, Model report, About/Data.
**Why:** agreed by Sam.

## D-012 — Downloads (2026-11-15)
CSV from the frontend; PDF via a print-friendly page. No PDF library.
**Why:** meets the need with no new tool.

## D-013 — English + Hindi (2026-11-15)
react-i18next; IBM Plex Sans Devanagari font.
**Why:** officials across India; matches the demo look.

## D-014 — Custom policies (2026-11-15)
Users build a policy from target-group traits we have + the scheme sliders. Wider range
and a "new policy" label when far from real schemes.
**Why:** proposed by Sam; the model uses scheme features, not names.

## D-015 — Demo style (2026-11-15)
IBM Plex fonts, light/dark mode, report panels, demo colour tokens.
**Why:** chosen by Sam.

## D-016 — Name "GovSim" (2026-11-15)
No new logo in V1. **Why:** chosen by Sam.

## D-017 — Render free plan + "waking up" screen (2026-11-15)
**Why:** free hosting with honest feedback during the 30–60 s cold start.

## D-018 — No data.gov.in API key (2026-11-16)
Sam downloads data.gov.in files by hand. **Why:** only one or two files are needed.

## D-019 — Phases (2026-11-16)
8 phases (0–7), data and model before frontend, each gated by Sam's sign-off.
**Why:** find data/model problems early.

## D-020 — Repo (2026-11-16)
Name `Gov-Sim`, public, no licence (all rights reserved).
**Why:** chosen by Sam.

## D-021 — Sam makes all commits and pushes (2026-11-16)
Claude Code never commits, pushes, tags or adds AI credit. Enforced in CLAUDE.md and
`.claude/settings.json` (deny rules).
**Why:** all work is pushed under Sam's GitHub name only.

## D-022 — Process rules (2026-11-15)
Git tags per release with a CHANGELOG entry. Every decision logged here with a date and a
reason. PROGRESS.md updated at every phase end. No V1 → V2 plan for now.
**Why:** agreed in the ground rules.
## D-023 — Fonts via @fontsource (2026-11-15)
IBM Plex fonts are installed from `@fontsource/*` npm packages (small addition to the
SPEC §10 toolkit).
**Why:** approved by Sam. Self-hosted fonts, no runtime call to Google.

## D-024 — Frontend test helpers (2026-11-15)
`@testing-library/react` and `jsdom` are added for vitest. shadcn's own helper packages
(clsx, tailwind-merge, class-variance-authority, etc.) are also allowed.
**Why:** approved by Sam. Needed to test React components.

## D-025 — TypeScript pinned to 5.x (2026-11-15)
`typescript@5` in the frontend, not 7.
**Why:** Hey API (`@hey-api/openapi-ts` 0.99) crashes on TypeScript 7 (`ts.SyntaxKind` is
missing). Revisit when Hey API supports TS 7.
