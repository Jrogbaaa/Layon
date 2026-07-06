# You First Gersh — Platform

Password-gated internal dashboard: roster overview, per-influencer metrics + creative
recommendations, and trend reports. Reads from the same Supabase project the scraper
writes to.

## Setup

```bash
cd platform
npm install
cp .env.local.example .env.local   # fill in real values
```

`.env.local` variables:
- `SITE_PASSWORD` — shared password gate (e.g. `LAYCC`)
- `SESSION_SECRET` — random string (`openssl rand -base64 32`), signs the session cookie
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` — same Supabase project as `scraper/`

## Run locally

```bash
npm run dev
```

Visit http://localhost:3000 — you'll be redirected to `/login` until you enter the
site password.

## Deploy

Deploy to Vercel (same pattern as the team's Project-X) and set the four env vars above
in the Vercel project settings. `SUPABASE_SERVICE_KEY` is server-only — it's never sent
to the browser.

## Tests

```bash
npx playwright test
```
