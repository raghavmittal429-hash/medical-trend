# Deployment Guide: Netlify (Frontend) + Railway (Backend)

## 1. Deploy Backend to Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Set the **Root Directory** to `backend/`
3. Railway will auto-detect Python and use `nixpacks.toml` for setup
4. Add these **Environment Variables** in Railway dashboard:
   - `ANTHROPIC_API_KEY` = your key
   - `LANGSMITH_API_KEY` = your key (if used)
   - `ALLOWED_ORIGINS` = https://your-site.netlify.app *(add after Netlify deploy)*
5. After deploy, copy your Railway URL: `https://your-app.up.railway.app`

## GitHub Actions Deployment

A workflow has been added at `.github/workflows/deploy.yml` to deploy the backend to Railway and the frontend to Netlify on pushes to `main`.

Add these GitHub repository secrets before push:
- `RAILWAY_API_KEY`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT`
- `API_BASE_URL`
- `NETLIFY_AUTH_TOKEN`
- `NETLIFY_SITE_ID`

> **Note:** `nixpacks.toml` installs `tesseract` and `poppler` automatically for OCR/PDF support.

---

## 2. Deploy Frontend to Netlify

1. Go to [netlify.com](https://netlify.com) → Add New Site → Import from GitHub
2. Build settings are auto-read from `netlify.toml` (no changes needed)
3. Add this **Environment Variable** in Netlify dashboard → Site Settings → Env Vars:
   - `API_BASE_URL` = `https://your-app.up.railway.app` *(your Railway URL)*
4. Trigger a deploy

---

## 3. Connect Them

- The Flutter app reads `API_BASE_URL` at **build time** via `--dart-define`
- The backend reads `ALLOWED_ORIGINS` at **runtime** to restrict CORS
- After both are deployed, update `ALLOWED_ORIGINS` in Railway to your Netlify URL

---

## Local Development

Run backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Run Flutter web locally:
```bash
cd flutter_app
flutter run -d chrome
# or with explicit URL:
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

---

## Environment Variables Summary

| Variable | Where | Value |
|----------|-------|-------|
| `API_BASE_URL` | Netlify | `https://your-app.up.railway.app` |
| `ANTHROPIC_API_KEY` | Railway | your Anthropic key |
| `ALLOWED_ORIGINS` | Railway | `https://your-site.netlify.app` |
| `LANGSMITH_API_KEY` | Railway | your LangSmith key (optional) |
