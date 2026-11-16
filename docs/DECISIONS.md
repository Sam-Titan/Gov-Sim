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
**Update 2026-11-15:** the calibration part is replaced by D-039 (GBM for the district level, fixed assumed β for slider changes).

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

## D-037 — Scheme slider values and sources (2026-11-15)
Approved by Sam. Cash, documents and bank rules come from official pages; "assumed" marks
a value no source gave. Burden and speed (1-5) are our scores, approved by Sam.
| Scheme | Benefit (₹) | Docs | Bank | Burden | Speed |
|---|---|---|---|---|---|
| PM-JAY | 5,00,000 cover per family per year, shown as **non-cash cover** (india.gov.in PM-JAY page) | 2: Aadhaar, ration card (`hem.nha.gov.in/BeneficiaryIdentification.pdf`) | no | 2 | 4 |
| PMUY | 1,600 per connection (`pmuy.gov.in/faq.html`; PIB Apr 2023) | 6 (`pmuy.gov.in/ujjwala2.html`, proof of address only if different) | yes (mandatory) | 3 | 4 |
| JSY | Mother's package, state rule below | LPS 1, HPS 2 (JSY/MCH card; BPL or SC/ST certificate needed in HPS states, JSY guidelines 4.3) | no (cash paid at the facility, 4.7) | 2 | 3 |
| SBM | 12,000 per household toilet (`swachhbharatmission.ddws.gov.in/faq`) | 1, **assumed**: guidelines name no documents; a beneficiary-list entry is the only step | yes, **assumed**: guidelines say DBT "may be ensured" for cash (6.4.10) | 3 | 2 |
- **JSY state rule** (JSY guidelines, `nhm.gov.in/showfile.php?lid=420` para 4.1/4.6; `nhm.gov.in` JSY page). Low-performing states (LPS, 10): Uttar Pradesh, Uttarakhand, Bihar, Jharkhand, Madhya Pradesh, Chhattisgarh, Assam, Rajasthan, Odisha, Jammu & Kashmir. LPS mother's package ₹1,400 rural / ₹1,000 urban; all other states (HPS) ₹700 / ₹600. ASHA package not counted. Ladakh counts as HPS (no income value, excluded from training anyway).
- **β2 form:** `log(1 + benefit / income)`, income = state per-capita NSDP 2021-22. PM-JAY is a yearly family cover and income is per person: a known mismatch, noted in the report.
- **Slider:** `cash_benefit_inr` max raised to ₹5,00,000; UI uses a log scale.
- Burden and speed reasons: PM-JAY card is made at a centre, cover is instant. PMUY has the longest paper list, connection comes fast. JSY is claimed at the facility, cash on the spot. SBM needs the household to build first, paid after.

## D-038 — Agent model design choices for Phase 2 (2026-11-15)
Approved by Sam (plan changes) plus the choices Claude made while building (flagged for review).
- **Covered share** = `b + (1 - b) x mean(eligible_i x p_i)` over the district's agents (expected value, not coin flips). Assumes "already covered without the scheme" is independent of agent traits.
- **Baseline `b`:** PM-JAY and PMUY: the district's NFHS-4 value (pre-scheme, 2015-16). If a district has no NFHS-4 value, the household-weighted state mean of NFHS-4 is used and the row is flagged `partial_data`; Telangana (no NFHS-4 anywhere) is excluded for these two schemes. JSY and SBM: `b = 0` (no pre-scheme number exists in our data; NFHS-4 is already mid-scheme). Private births and own toilets are therefore absorbed into β0 and the sign-up probability. **Limitation, to be shown in the report.**
- **NFHS-4 use:** PM-JAY, PMUY: baseline only, never a target. JSY, SBM: second target with one shared nuisance shift `era_shift` added to z for NFHS-4 rows (not a β, not a slider). Traits are the same for both time points.
- **β1** fixed at 1.0 on a district trust latent fixed at 0 (prior mean). Not fitted; labelled "assumed". No data on trust in V1.
- **Weak β (2, 3, 5, 6, 8) and β7:** ridge penalty to a prior mean of 0 (sd 1), so signs come from the data, not from bounds.
- **Common random numbers:** each district has fixed uniform draws (seed 42 + district id), reused in every evaluation.
- **Eligibility in V1 real schemes = all agents.** SPEC §3 "rural focus" for SBM is not applied (urban sanitation is in the NFHS target and b = 0 cannot explain it). Custom-policy target groups use the same eligibility function.
- **Exclusions:** 5 districts with no state income (Ladakh, Dadra & Nagar Haveli and Daman & Diu) are excluded from training and evaluation, not imputed (rule 4).
- **GBM:** district traits + scheme feature values + baseline `b` + era flag. No scheme ID. Same rows as the agent model.

## D-039 — Hybrid output: GBM for the district level, assumed β for slider changes (2026-11-15)
Decided by Sam after the Phase 2 results (agent model does not beat the GBM: LOSTO 14.1 vs 10.5 pp, LOSO 32.1 vs 30.8; β2 and β6 got the wrong sign from 4 schemes). Replaces the "calibrate all β" part of D-004.
- **District level ("from data"):** ~~the GBM prediction~~ changed by D-041: the actual NFHS-5 value for mapped districts. The GBM stays as the baseline in the report.
- **Slider changes ("model assumption"):** agent model run twice, at the scheme's real settings and at the user's settings; the difference is added to the GBM value.
- **β2, β3, β5, β6, β8 are fixed assumed values**, each with a low and a high value (table in SPEC 5.1 once Sam approves; proposal in PROGRESS.md). Cite research where it exists, otherwise label "assumed by team". **β0 and β7 stay fitted** (to the NFHS data, with the others fixed); **β1 stays fixed** (assumed). `era_shift` stays a nuisance term.
- **Headline test is LOSTO.** LOSO stays in the report with the note that 4 schemes are too few to test generalisation across schemes.
- **UI range** = GBM error band (from LOSTO errors) + spread of the slider change across the low and high β sets.
- **Custom policies always show the `new_policy` label.**
- Model report page states that the agent model does not beat the GBM.
- `backend/artifacts/*.json` are to be committed (Sam makes the commit).
**Status:** the decision is approved; the β values themselves are **not yet approved** and nothing uses them.

## D-040 — β values approved; β2 on monthly income; error band; range rule (2026-11-15)
- **β2 uses monthly income:** `log(1 + benefit / (state per-capita income / 12))` (changes D-037's formula; code updated, `MONTHS = 12`). So a cash change is visible in the result.
- **Fixed β values approved by Sam** (weak / central / strong): β2 0.2 / 0.5 / 1.0; β3 -0.3 / -0.8 / -1.5; β5 -0.2 / -0.6 / -1.2; β6 0.1 / 0.4 / 0.8; β8 -0.3 / -0.9 / -1.8. All "assumed by team" (no effect sizes found; Gupta 2017 supports direction only). Subject to the sanity table below; β0, β7 not yet refitted.
- **GBM error band:** 10th and 90th percentile of the GBM's LOSTO errors (actual - predicted), **per scheme**. First look (not final): PM-JAY -28.7 / +28.5 pp, PMUY -12.3 / +15.0, JSY -6.9 / +11.1, SBM -14.8 / +13.2.
- **UI range rule (proposal, Sam to confirm):** `low = GBM + change_min + e10`, `high = GBM + change_max + e90`, `point = GBM + change_central`, clipped to 0-100. `change_min` and `change_max` are the smallest and largest of the weak / central / strong slider changes (sign-agnostic). The two parts are **added end to end, not combined as a root of squares**. This assumes the worst case, where both errors point the same way, so the range is wider than a statistical interval. With no slider change the range is the GBM band alone. Custom policies: no real settings to compare to, so always the `new_policy` label and a wider range (set in Phase 3).
- **Sanity-table finding (see PROGRESS.md):** with monthly income, PM-JAY's ₹5 lakh makes the un-anchored model predict about 98% coverage for PM-JAY, so it barely reacts to sliders. **Proposal:** anchor the agent model to the GBM value for each district and scheme (add a per-district shift to z so the model equals the GBM at the real settings), then apply the slider change. Not adopted until Sam approves.

## D-041 — Anchor at the NFHS value, sampling band, low-confidence, PM-JAY cap (2026-11-15)
Approved by Sam. Updates D-039 and D-040.
- **Anchor in logit space.** For each district and scheme, the agent model's z is shifted (one number per district) so the model equals the starting level at the real settings. The slider change is then `model(user settings) - model(real settings)`. β0 and β7 cancel out of this change (the shift absorbs them), so they matter only for the report's unanchored fit.
- **Starting level = the actual NFHS-5 value** for real schemes in the 629 districts with data. **Custom policies:** the user picks a real scheme to "start from"; the change is applied to that scheme's level in that district. Always the `new_policy` label.
- **GBM** stays as the baseline in the report (LOSTO error bands per scheme in `report.json`). It is not in the UI range for mapped districts.
- **Sampling band (replaces the GBM band in the UI range):** `SE = sqrt(deff x p x (1-p) / n)`, band = ±1.2816 x SE (10th-90th percentile, like the GBM band). `n` = households interviewed, printed on each NFHS sheet ("information was gathered from 897 households, 942 women, and 143 men"; all 704 read, `nfhs_sample_sizes.parquet`), used for PM-JAY, PMUY, SBM. JSY uses women interviewed (births in the last 5 years are not printed), so the **JSY band is understated**. **Design effect 2.0 is assumed by team** (the NFHS sample is clustered, the value is not printed on the sheets).
- **Range** = end-to-end sum (D-040): `low = level + min(change) + sampling_low`, `high = level + max(change) + sampling_high`, `point = level + central change`, clipped to 0-100. **"Low confidence" label** when high - low > 30 pp.
- **PM-JAY benefit slider** capped at ₹2,50,000 to ₹10,00,000 (half to double the real cover), labelled "non-cash cover".
- **Optional documents effect for all agents: proposed, not used** (values in PROGRESS.md).

## D-042 — JSY sampling band uses estimated births; deff labelled "assumed" (2026-11-15)
Decided by Sam. Replaces the "JSY band is understated" part of D-041.
- **JSY n** = women interviewed x (Census 2011 children 0-6 x 5/7 / Census 2011 women 15-49), per district, labelled **estimated** in `report.json`. Women 15-49 come from Census C-13 (Females, ages 15-49; 311.7 million in India, `census_age.parquet` column `women_15_49`). Births per woman: median 0.38 (range 0.19 to 0.79). Limits: 2011 ratio applied to 2019-21; ignores child deaths and migration. JSY median half-width goes from ±1.49 to ±2.34 pp (max 3.38 to 6.0).
- **Design effect 2.0** stays, labelled "assumed by team" in `report.json` (`sampling_band.deff`).
- **Documents effect for all agents** (proposal in PROGRESS) is **not used**.

## D-043 — No LightGBM surrogate; the anchored agent model answers live (2026-11-15)
Decided by Sam. Updates D-004 (the "train a surrogate" part).
Measured: one `/simulate` core (1 district, 3 beta sets) 6 ms median, 17 ms worst; one state (Uttar Pradesh, 71 districts) 6 ms median, 12 ms worst; all 629 districts 25 ms; start-up 0.3 s. All far under the 200 ms target, so a surrogate would add build time and an extra error source for no speed gain. LightGBM stays only as the GBM baseline (never deleted). Reasons come from the model itself (one slider term switched on at a time).

## D-044 — Custom policies report uptake in the target group and people reached (2026-11-15)
Decided by Sam. Replaces the custom-policy output of D-014, D-038 and D-041 (a share of all households, which drops sharply for a narrow group).
- **Uptake in the group (%)** = mean sign-up probability over the group's sampled agents, anchored at the starting scheme's NFHS level (everyone eligible, real settings). **Range** = lowest and highest value over the weak / central / strong beta sets and the NFHS sampling band of the level.
- **Reached (count, estimated)** = Census 2011 base (households for PM-JAY and PMUY, estimated births for JSY, people for SBM) x group share of the 500 sampled agents x uptake. The group share is an agent-sample share applied to the base, so it is approximate (e.g. "female" households).
- `changes` = the new settings against the real settings for the same group. Reasons include `target_group` (how the group differs from everyone at the real settings).
- Groups under 10 of 500 agents: `group_too_small` (no number). `new_policy` stays on; `partial_data` is added when the group is "unbanked".
- Not comparable with a share of all: `/compare` returns `comparable: false` and no difference when A and B use different bases.
- SPEC 7.2 updated.

## D-045 — Districts show their current state; no-baseline rule (2026-11-15)
Decided by Sam.
- A district whose state changed after Census 2011 is listed and simulated under the **current** state; the 2011 link (`pc11_s_id`) is kept. Warangal is shown under Telangana (formed 2014; hand-reviewed override). Mapped Telangana and Ladakh districts already used the current state from the NFHS sheet. An unknown split with no override stops start-up with an error instead of guessing.
- PM-JAY and PMUY baseline (D-038): own NFHS-4 value, else the household-weighted state mean (flagged `partial_data`). Where a state has no NFHS-4 value at all (Telangana, 9 districts; NCT Delhi, 9 districts) the result is `no_data` with reason `no_baseline`.
- JSY cash slider replaces the rural value and keeps the urban:rural ratio; PM-JAY cash outside ₹2,50,000 to ₹10,00,000 returns 422 (approved).

## D-046 — NFHS-4 state value as PM-JAY / PMUY baseline for Delhi and Telangana (2026-11-15)
Decided by Sam. Extends the baseline rule of D-038 and D-045.
- Order: the district's NFHS-4 value; else the household-weighted state mean of NFHS-4 district values; else (only NCT Delhi and Telangana, which have no NFHS-4 district value at all) the **official NFHS-4 state value** read from the NFHS-5 state compendium (same two PDFs, MANIFEST rows 751 and 752). Values: health insurance Delhi 15.7, Telangana 66.4; clean fuel Delhi 97.9, Telangana 67.3. Always flagged `partial_data`.
- Stored in its own file (`nfhs4_state_baseline.parquet`), never as a trait (these are target indicators).
- Used by the live service only. Phase 2 training still excludes these 18 rows (D-038), so `report.json` is unchanged. The live service now has 629 rows for PM-JAY and PMUY (was 611); `no_baseline` stays as a safety reason but no real district uses it.
- **Known limit:** in 167 of 629 PM-JAY rows (8 of the 18 new Telangana ones) the NFHS-5 value is not above the NFHS-4 baseline (coverage fell, e.g. RSBY ended). The model cannot go below the baseline, so it anchors at baseline + 0.5 pp and the slider change is measured from there. The displayed level is still the actual NFHS-5 value. PMUY: 23 of 629 rows.

## D-047 — Simulator page choices (2026-11-16)
Decided by Sam (plan approval for Phase 4).
- **Packages:** `maplibre-gl`, `react-map-gl`, and the Radix primitives for the shadcn slider and switch (`@radix-ui/react-slider`, `@radix-ui/react-switch`). Nothing else.
- **Map:** no basemap tiles (districts only, no third-party service); GeoJSON served from `frontend/public/geo/`; India view with state outlines first, then zoom to the chosen state. Colourblind-safe sequential scale (ColorBrewer YlGnBu, 8 classes of 12.5 pp); `low_confidence` districts hatched; legend says "middle value, see the range in the panel". State outlines (`states.geojson`) merge districts by their **current** state (D-045), so Telangana and Ladakh are their own states (36 outlines).
- **Data fetching:** `/simulate`, `/simulate/state` and `/compare` are POST but generated as TanStack **query options** (Hey API `isQuery` hook in `openapi-ts.config.ts`), so requests are cached and cancelled when outdated. The previous result stays on screen while a new one loads.
- **URL:** state, district, scheme and moved sliders live in the search params, so a scenario can be shared by link. Zustand holds UI state only (theme).
- **Metric label** on every result (D-030). Range ends round outward (low down, high up).
- **Light/dark** follows the system by default, with a manual toggle. Dark colour tokens are the demo bulletin's, given by Sam and added to SPEC §9.
- **Hindi:** all new Hindi strings are **draft**; Sam reviews them in Phase 6 (list in PROGRESS).

## D-048 — Phase 4 changes before sign-off (2026-11-16)
Decided by Sam.
- State outlines merged by current state (D-045); dark tokens from the demo bulletin (SPEC §9); language choice saved in localStorage (`govsim.lang`) like the theme.
- Map note "District boundaries are approximate and not authoritative" (EN + HI draft).
- Approved as they are: Back button does not undo slider moves (URL uses `replace`), the MapLibre worker fix, local GeoJSON types.
- **Boundary check:** reported in PROGRESS. No geometry changed; Sam decides.

## D-049 — Map boundary: keep as is; polygon 000; light tokens (2026-11-16)
Decided by Sam.
- **Boundary:** keep the map as it is, with the note "District boundaries are approximate and not authoritative". No Survey of India overlay in V1. (Check results: PROGRESS "Phase 4 boundary check".)
- **Polygon `000`** (unnamed, Gilgit-Baltistan / Aksai Chin region) is always drawn in the "no data" grey, is not clickable, and has a state-edge outline, so India's outline has no gap.
- **Light tokens** from the demo bulletin added (surface-2 `#edece6`, ink-muted `#55575f`, ink-faint `#85868d`, line-strong `#c7c5b8`, accent-soft `#e4ecf6`, stamp-soft `#f7e3e0`); SPEC §9 updated.
