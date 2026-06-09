# Deployment Guide: GitHub Pages (Frontend) + Render (Backend)

## 1. Deploy Backend to Render

### Initial Setup (One-time)

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub account (recommended)

2. **Create New Web Service**
   - Dashboard → New → Web Service
   - Select your `medical-trend` repository
   - Accept defaults (Render will auto-detect Python)
   - Plan: Free tier (sufficient for testing)

3. **Configure Environment Variables**
   - Under Environment section, add:
     - `ANTHROPIC_API_KEY` = your key
     - `LANGSMITH_API_KEY` = your key (if used)
     - `ALLOWED_ORIGINS` = `https://raghavmittal429-hash.github.io`
   - Leave `PYTHON_VERSION` as default

4. **Deploy Configuration**
   - Build Command: (auto-detected from `render.yaml`)
   - Start Command: (auto-detected from `render.yaml`)
   - Click **Create Web Service**

5. **Your backend URL will be:**
   ```
   https://medical-trend-backend.onrender.com
   (or similar - check Render dashboard)
   ```

### CI/CD via GitHub Actions

The workflow automatically triggers Render deployment on push to `main` using a deploy hook.

**Required GitHub Secret:**
- `RENDER_DEPLOY_HOOK_URL` = Deploy hook URL from Render

#### Get Deploy Hook URL

1. Go to your Render service dashboard
2. Settings → Deploy Hook
3. Copy the webhook URL
4. Add to GitHub Secrets:
   - Repo → Settings → Secrets → New Secret
   - Name: `RENDER_DEPLOY_HOOK_URL`
   - Value: Paste the deploy hook URL

### Render Configuration File

The `render.yaml` file in the root directory tells Render:
- Build the Python backend with dependencies
- Start the Uvicorn server on port 8000
- Use Python 3.11.9
- Auto-reload on git push to main

## GitHub Actions Deployment

A workflow has been added at `.github/workflows/deploy.yml` to deploy the backend to Render and the frontend to GitHub Pages on pushes to `main`.

Add this GitHub repository secret:
- `RENDER_DEPLOY_HOOK_URL` - Deploy hook URL from your Render service
- `API_BASE_URL` - Your Render backend URL (e.g., `https://medical-trend-backend.onrender.com`)

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
- `API_BASE_URL` should be: `https://medical-trend-backend.onrender.com` (check your Render dashboard)
- `ALLOWED_ORIGINS` is set to: `https://raghavmittal429-hash.github.io` (already in render.yaml)

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
| `API_BASE_URL` | GitHub Actions (build-time) | `https://medical-trend-backend.onrender.com` |
| `ANTHROPIC_API_KEY` | Render | your Anthropic key |
| `ALLOWED_ORIGINS` | Render (via render.yaml) | `https://raghavmittal429-hash.github.io` |
| `LANGSMITH_API_KEY` | Render | your LangSmith key (optional) |
