# DiandiShop Web

DiandiShop is now structured as a modern web application:

- **Frontend**: Vue 3 + Vite + Tailwind CSS + Pinia + Axios (`/frontend`)
- **Backend**: Flask API with role-based sessions (`/api/app.py`)
- **Deployment**: Vercel (static frontend + serverless Flask function)
- **Database**: SQLite by default, configurable via environment variables

## Architecture

- `frontend/`: responsive SPA (Login/Register, POS, Dashboard, Product management, Stock management)
- `api/app.py`: Flask API, CORS-enabled, serverless-ready
- `api/migrations/*.sql`: SQL migrations applied automatically at startup
- `vercel.json`: deployment and rewrite configuration
- `.github/workflows/ci-cd.yml`: quality/build checks and optional deploy hook

## Local development

### Backend

```bash
python -m pip install -r requirements.txt
python app.py
```

Backend runs at `http://localhost:5000`.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Frontend runs at `http://localhost:5173`.

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:5000
```

## Environment variables

Backend:

- `SECRET_KEY` - Flask secret key
- `SETUP_CODE` - first-admin activation code
- `DATABASE_PATH` - SQLite file path (default: `<repo>/diandishop.db`)
- `DATABASE_URL` - optional sqlite URL (`sqlite:///absolute/path.db`)
- `FRONTEND_ORIGIN` - allowed CORS origin(s)
- `APP_RUNTIME_DIR` - override templates/static runtime path

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full deployment and production setup.
