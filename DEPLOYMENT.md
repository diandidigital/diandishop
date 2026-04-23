# DiandiShop Deployment Guide (Vercel)

## 1) Prerequisites

- Vercel account + linked GitHub repository
- Python 3.9+ runtime
- Node.js 20+

## 2) Project structure

- `frontend` builds to static assets (`frontend/dist`)
- `api/app.py` is deployed as a Vercel Python serverless function
- `vercel.json` handles frontend build + API rewrites

## 3) Vercel configuration

`vercel.json` already includes:

- frontend build command: `cd frontend && npm ci && npm run build`
- output directory: `frontend/dist`
- function runtime: `api/app.py` on Python 3.9
- rewrites:
  - `/api/*` -> `/api/app.py`
  - all other routes -> SPA `index.html`

## 4) Environment variables

Set these in Vercel Project Settings > Environment Variables:

- `SECRET_KEY` (required)
- `SETUP_CODE` (optional, for first admin creation flow)
- `DATABASE_PATH` **or** `DATABASE_URL`
- `FRONTEND_ORIGIN` (set to your production frontend URL)
- `APP_RUNTIME_DIR` (optional)

### Database modes

- **Local SQLite**: set `DATABASE_PATH=/tmp/diandishop.db` on Vercel
- **URL-based SQLite**: set `DATABASE_URL=sqlite:////tmp/diandishop.db`

> The backend automatically runs schema setup and SQL migrations from `api/migrations`.

## 5) GitHub Actions CI/CD

Workflow: `.github/workflows/ci-cd.yml`

- Installs backend dependencies
- Runs backend syntax checks (`compileall`)
- Installs frontend dependencies
- Runs frontend production build
- Optionally triggers Vercel deploy hook if `VERCEL_DEPLOY_HOOK_URL` is configured

## 6) Local verification checklist

```bash
python -m pip install -r requirements.txt
python -m compileall api/app.py app.py
cd frontend && npm ci && npm run build
```

## 7) Future schema updates

Add a new SQL file in `api/migrations/` with an incremental name, for example:

- `0003_add_customer_table.sql`

It will be applied once automatically at backend startup.
