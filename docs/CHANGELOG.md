# Changelog

## v1.0 — (date of Sam's tag)

First public release. Planning aid, not a guarantee.

### What V1 does
- **Simulator:** pick a state, a district and one of 4 schemes (PM-JAY, PMUY, JSY, SBM), move five sliders, and see the expected uptake as a **range** (low, middle, high) with the reasons that move it most.
- **Result = real data + model change:** the level is the district's NFHS-5 value; the sliders move it by the agent model's change from the scheme's real settings (D-052).
- **Custom policy:** start from a real scheme, choose a target group (age, gender, disability, area, bank account), see uptake within the group and the estimated number reached.
- **Compare:** two settings in one district, with B minus A as a range.
- **Map:** 629 districts with data; the other 81 say why they have none.
- **Model report** and **About and data** pages: accuracy against the GBM baseline, sensitivity, known weaknesses, sources and licences.
- **Downloads:** CSV for the Simulator result, the state table and Compare (UTF-8 with BOM, formula-safe), and a print / PDF view.
- **Languages:** English and Hindi (Hindi is a draft until a fluent speaker has reviewed it).
- **Honest by design:** always a range, warnings outside real-scheme settings or for far-away custom policies, "waking up the server" screen while the free backend starts.

### Known limits (also shown in the app)
- **The agent model is less accurate than the GBM baseline** out of sample (leave-one-state-out). The district level shown is NFHS-5 data; the model only supplies the change from the real settings. See the Model report page.
- The levels shown on the site are the actual NFHS-5 survey values; the agent model is used only to estimate the change when sliders move, and those changes are labelled as model assumptions.
- NFHS-5 is a household survey, not official sign-up counts; the schemes are survey proxies (D-028). JSY uses estimated births.
- 70 NFHS-5 districts created after Census 2011 have no 2011 parent and no result. Chandigarh, Lakshadweep and Vidisha have no NFHS-5 sheet.
- For PM-JAY, NFHS-5 is at or below NFHS-4 in 160 of 629 districts (cause unknown).
- District boundaries are approximate. State names and district names stay in English in Hindi.

### Tooling in this release
- Playwright end-to-end tests (`just e2e`) for the Simulator, custom policy, Compare, downloads, English/Hindi and the wake-up screen.
- Backend start-up and memory check (`backend/scripts/check_memory.py`): about 0.4 s and under 180 MB peak on a development machine; Render free plan limit is 512 MB.
- Wake-up screen treats 502, 503, 504, dropped connections and timeouts from `/api/health` as "still waking".
- Download buttons are disabled while a result is updating (no stale numbers under a new link).
- Sliders have accessible names.
- **No Sentry in V1** (D-055). Errors are checked in the Render logs and the browser console.
- Deploy steps: `docs/DEPLOY.md`.
