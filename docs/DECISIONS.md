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

## D-028 — Final V1 schemes: 4 NFHS proxies (2026-11-15) — replaces D-005
Schemes: **PM-JAY** (health insurance, NFHS #12), **PMUY** (clean cooking fuel, #10),
**JSY** (institutional births, #42), **SBM** (improved sanitation, #9). All are labelled
"proxy". Two time points (NFHS-4, NFHS-5) from the same NFHS-5 district sheets.
**Dropped:** NSAP old age / widow / disability pensions, Ujjwala admin counts, Jan Dhan,
and the MGNREGA idea.
**Why each was picked:** each has one main scheme behind it, is demand-driven (people
choose to apply), has a district value in every sheet, and comes from a public PDF that
a script may download (DHS `robots.txt` does not block `/pubs/pdf`).
**Why the others were dropped:** NSAP, Ujjwala and Jan Dhan district files are only on
data.gov.in (blocks bots) or Dataful/AIKosh (login or unclear terms). NSAP counts are also
capped per state. MGNREGA MIS reports use a captcha and checked URLs, so a script would
have to work around the site. Indicators with no district value (JSY payment, bank account
use, ICDS) are state-level only. 4+ ANC visits and the MCP card were dropped by Sam because
they are not tied to one scheme.
**Limits:** survey estimates, not admin counts; only 4 schemes from one survey, so scheme
effects are weakly identified (see SPEC §5.3, §5.4 `survey_estimate` warning). Telangana
has NFHS-5 only; Chandigarh is left out.
Also recorded: the district map is SHRUG v2.1 open district polygons, hosted on AIKosh,
CC BY-NC-SA 4.0.

## D-029 — pdftotext for data scripts only (2026-11-15)
The system tool `pdftotext` (poppler) is allowed in `backend/scripts/` to read the NFHS
district PDFs. The live API and the frontend must never call it; the app reads only the
Parquet output.
**Why:** approved by Sam. NFHS district data exists only as PDFs; no new Python package
is needed.

(Note: D-026 and D-027 are not used.)

## D-030 — Target is the NFHS % of all households / births / people (2026-11-15)
For the 4 NFHS schemes the model predicts the NFHS share of **all** households (PM-JAY,
PMUY), **all births** in the last 5 years (JSY) or **all people** (SBM). It is not the
share of the eligible group. The UI says so on every result ("share of all households",
etc., in English and Hindi). SPEC §1 and §3 updated.
**Why:** decided by Sam. NFHS gives the share of the whole group; we have no good count of
eligible households per district to turn it into an eligible share.

## D-031 — Drop `digital_only` and β4; keep bank-account β8 for now (2026-11-15)
Removed from SPEC §5.1 and §6: the `digital_only` slider and β4 (digital-only application
x no internet). The model now has 8 β values (β0–β3, β5–β8; numbers kept so notes still
match). Kept: `requires_bank_account` and β8, to be dropped in Phase 2 if they cannot be
estimated. β2 is renamed "benefit value relative to income"; in Phase 2 the PM-JAY value is
set from official scheme guidelines and cited. β3, β5, β6, β8 carry a "weakly estimated"
note (only 4 schemes, one survey; scheme features cannot be separated from which scheme it is).
**Why:** none of the four schemes is digital-only, so β4 cannot be learned from the data.
PM-JAY is a health cover, not cash, so "cash relative to income" needed a clearer name.

## D-032 — Census 2011 source: Primary Census Abstract from censusindia.gov.in (2026-11-15)
District population and households come from the official Census Digital Library table
PC11_PCA-SD (`DDW_PCA0000_2011_Indiastatedist.xlsx`, 640 districts, Total / Rural / Urban).
Checked first: the site has no `robots.txt` (404), the file downloads with no login, and I
found no terms page that forbids it. Licence is not stated on the page.
**Limits:** the PCA has no BPL, widow, disability, age-60+, LPG, bank or internet counts.
Bases for the 4 schemes: households (PM-JAY, PMUY), people (SBM) and an estimate of births
in 5 years (children aged 0-6 x 5/7, JSY; ignores child deaths and migration).
**Why:** chosen by Sam. District codes match the map's `pc11_d_id` (all 640 match).
The Local Government Directory (LGD) was **not** used: its download page has a captcha.

## D-033 — V1 uses the 634 mapped districts (2026-11-15)
Only NFHS districts that map to a Census 2011 district are in V1. The other 70 show as "no
data" on the map (`has_nfhs_data` false). Names kept in `data/interim/unmapped_districts.csv`
for later. **Why:** decided by Sam; no guessing of parent districts.

## D-034 — Vidisha and Lakshadweep accepted as missing (2026-11-15)
No NFHS-5 district sheet found for either. Listed in `docs/DATA_REPORT.md` and to be listed
on the About page. Chandigarh is skipped by an earlier decision. **Why:** decided by Sam.

## D-035 — Trait sources, leakage guard, partial_data (2026-11-15)
Traits come from three layers (NFHS-5 district sheets, Census 2011 PCA + C-20 disability,
NFHS-5 state compendium for bank/phone/internet). State-level values are copied to every
district and flagged `partial_data`. The 4 targets, their close relatives and the
health-service and outcome blocks are never traits (list in DATA_REPORT). Trait-target
correlations are checked in the report. BPL and income have no free source and are dropped;
"has LPG" is dropped (it is the PMUY target). Census C-20 (disability) used for district
disability; it has no exact 18+ cut, so 20+ and 60+ are used. Census C-13 (age) and C-02
(widows) are `.xls`: see D-036. **Why:** decided by Sam.

## D-036 — Trait follow-ups: xlrd, age 60+, no widows/BPL/LPG/electricity, beta2, beta7 (2026-11-15)
- **`xlrd` approved for data scripts only** (read old `.xls` Census tables). Not used by the live app.
- **Age 60+** comes from Census C-13 (35 state files, all 640 districts; sum of ages 60-99 and 100+ over all ages; 8.6% nationally, ranges 2.5% to 17.8% by district).
- **Widows dropped in V1** (C-02 has district tables for only 13 states). Removed "widow" from the custom-policy targets. "BPL" and "no LPG" removed from the custom-policy targets too (SPEC 7.2). BPL and income band dropped from traits. **Electricity trait dropped** (overlaps the PMUY target).
- **beta7 deprivation score:** mean of six sign-adjusted z-scores over the 704 NFHS-5 districts: women literate, women with 10+ years of schooling, female school attendance, birth registration (low = deprived); women married before 18, population below 15 (high = deprived). Only non-leaking traits. Correlation with targets in DATA_REPORT (largest: SBM -0.68).
- **beta2 income: state per-capita NSDP, not a national figure.** A free, scriptable source exists: Economic Survey 2023-24 statistical appendix table 1.11A on indiabudget.gov.in (source: state Directorates of Economics & Statistics via MoSPI; PDF downloads with no login, no `robots.txt` (404)). RBI's own site blocks scripts (HTTP 418 / returns the homepage), so it was not used. One common year, 2021-22 (2022-23 and 2023-24 have gaps), current prices. Missing for Ladakh and Dadra & Nagar Haveli and Daman & Diu (5 districts); no national figure was added, Phase 2 decides. Nominal, so it is not adjusted for prices across states.
**Why:** decided by Sam.
