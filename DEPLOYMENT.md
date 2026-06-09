# Deployment Guide: GitHub Pages (Frontend) + Railway (Backend)

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

A workflow has been added at `.github/workflows/deploy.yml` to deploy the backend to Railway and the frontend to GitHub Pages on pushes to `main`.

Add these GitHub repository secrets before push:
- `RAILWAY_API_KEY`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT`
- `API_BASE_URL`

> **Note:** GitHub Pages deployment uses the built-in `GITHUB_TOKEN` (no additional credentials needed).
> **Note:** `nixpacks.toml` installs `tesseract` and `poppler` automatically for OCR/PDF support.

---

## 2. Deploy Frontend to GitHub Pages

**Automatic via CI/CD:** When you push to `main`, the GitHub Actions workflow automatically builds the Flutter web app and deploys it to GitHub Pages.

**Manual Setup (One-time):**

1. Go to your GitHub repo → **Settings** → **Pages**
2. Under "Build and deployment":
   - **Source:** Select "Deploy from a branch"
   - **Branch:** Select `gh-pages`
   - **Folder:** Leave as `/ (root)`
3. Click **Save**

Your frontend will be available at: `https://raghavmittal429-hash.github.io/medical-trend`

---

## 3. Connect Them

- The Flutter app reads `API_BASE_URL` at **build time** via `--dart-define`
- The backend reads `ALLOWED_ORIGINS` at **runtime** to restrict CORS
- After backend is deployed, update `ALLOWED_ORIGINS` in Railway to your GitHub Pages URL: `https://raghavmittal429-hash.github.io`

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
| `API_BASE_URL` | GitHub Actions (build-time) | `https://your-app.up.railway.app` |
| `ANTHROPIC_API_KEY` | Railway | your Anthropic key |
| `ALLOWED_ORIGINS` | Railway | `https://raghavmittal429-hash.github.io` |
| `LANGSMITH_API_KEY` | Railway | your LangSmith key (optional) |
