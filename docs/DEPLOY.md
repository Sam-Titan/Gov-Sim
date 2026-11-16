# Deploy GovSim V1 (steps for Sam, done by hand)

Frontend on **Netlify**, backend on **Render** (free plan). No Sentry (D-055).
Claude Code does not deploy anything.

## Accounts you need
| Account | Why | Plan |
|---|---|---|
| GitHub | Render and Netlify read the repo from here (it is already public) | free |
| Render (render.com) | runs the Python backend | Free |
| Netlify (netlify.com) | serves the website and forwards `/api` to Render | Free |

Sign up to Render and Netlify with "Continue with GitHub" so they can see the repo.

## How the pieces connect
Browser -> Netlify (`https://<site>.netlify.app`) -> `/api/*` is forwarded by Netlify to Render
(`https://<service>.onrender.com/api/*`). The browser only talks to Netlify, so CORS is not used in
normal browsing. `CORS_ORIGINS` is still set on Render as a safety net.

## Env values
| Where | Name | Value |
|---|---|---|
| Render | `PYTHON_VERSION` | `3.12.11` (any 3.12.x that Render lists) |
| Render | `CORS_ORIGINS` | your Netlify URL, for example `https://govsim.netlify.app` (no trailing slash) |
| Render | `PORT` | set by Render, do not add |
| Netlify | `NODE_VERSION` | `24` (already in `frontend/netlify.toml`) |
| Netlify | `PNPM_VERSION` | `12.11.2` (already in `frontend/netlify.toml`) |
No secrets are needed. Nothing else goes in either dashboard.

## Step 1 — Render (backend)
1. Render dashboard -> **New +** -> **Web Service** -> connect the GitHub repo `Gov-Sim`.
   (Or **New +** -> **Blueprint** and pick `render.yaml`; then skip to the env step.)
2. Settings:
   - **Name:** `govsim-api` (the URL becomes `https://govsim-api.onrender.com`; if the name is taken, use another and remember it)
   - **Language:** Python 3. **Branch:** `main`.
   - **Root Directory:** leave **empty**.
   - **Build Command:** `pip install uv && cd backend && uv sync --frozen --no-dev`
   - **Start Command:** `cd backend && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** **Free**.
   - **Health Check Path** (Advanced): `/api/health`
3. **Environment** -> add `PYTHON_VERSION` = `3.12.11` and `CORS_ORIGINS` = `http://localhost:5173` for now.
4. **Create Web Service.** Wait for "Live" (first build takes a few minutes).
5. Open `https://<service>.onrender.com/api/health`. You should see `{"status":"ok"}`.
6. In **Logs**, find "Application startup complete" and note the time since "Started server process". Write it in PROGRESS. Locally it is about 0.4 s and 180 MB; the free plan has 512 MB and a slow CPU, so the time on Render will be longer.
   If the log says "Out of memory", tell Claude: the model has to be made smaller (needs your decision).

## Step 2 — Netlify (frontend)
1. Open `frontend/netlify.toml` and replace `GOVSIM-API` with your Render service name
   (the line `to = "https://GOVSIM-API.onrender.com/api/:splat"`). Commit and push (your commit).
2. Netlify dashboard -> **Add new site** -> **Import an existing project** -> **GitHub** -> pick `Gov-Sim`.
3. Settings:
   - **Base directory:** `frontend`
   - **Build command:** `pnpm build` (netlify.toml sets it)
   - **Publish directory:** `dist` (relative to the base directory; netlify.toml sets it)
   - Environment variables: none needed (`NODE_VERSION` and `PNPM_VERSION` are in netlify.toml).
4. **Deploy.** When it is live, note the URL (for example `https://govsim.netlify.app`).
   Optional: **Site configuration** -> **Change site name** for a nicer address.

## Step 3 — Tell Render the Netlify address
Render -> your service -> **Environment** -> set `CORS_ORIGINS` to the Netlify URL
(no trailing slash; several values can be separated by commas). Save; Render redeploys.

## Step 4 — Check the live site
1. Open the Netlify URL. If Render was asleep you see **"Waking up the server…"** for up to a minute,
   then the Simulator opens by itself. No error screen should appear at any time.
2. Pick Bihar -> Araria -> PM-JAY. A range appears; move "Application burden"; the result changes.
3. Open `https://<netlify-site>/compare` directly, and reload it (must not give a 404).
4. Open `https://<netlify-site>/api/health` in the browser: `{"status":"ok"}` (this proves the forwarding).
5. Switch to हिन्दी and back. Download a CSV; open it in Excel (Hindi should show correctly).
6. Cold test: wait about 20 minutes (Render sleeps after about 15 minutes idle), open the site again,
   and check the wake-up screen shows and then the site loads.
7. Optional: Claude can run the e2e suite against the live site:
   `cd frontend && E2E_BASE_URL=https://<netlify-site> pnpm exec playwright test`
   (a cold start can make the first test slow; run it twice if needed).
8. Errors: Render -> **Logs**, and the browser console (F12). No Sentry.

## Free plan notes
- Render free web services sleep after about 15 minutes without traffic; the first request wakes them (30 to 60 seconds). That is what the wake-up screen is for.
- Free instance hours are limited per month; a demo is well inside it.

## Before you announce it
- **Hindi review by a fluent speaker** is still open (D-054): `docs/HINDI_STRINGS.md` -> mark changes -> Claude applies them and removes the "draft" note.
- Tag the release yourself after the live check: `git tag v1.0 && git push origin v1.0`
  (CHANGELOG entry is in `docs/CHANGELOG.md`; put the date in its heading).
