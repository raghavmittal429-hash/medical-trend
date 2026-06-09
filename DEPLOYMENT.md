# Deployment Guide: GitHub Pages (Frontend) + PythonAnywhere (Backend)

## 1. Deploy Backend to PythonAnywhere

### Initial Setup (One-time)

1. **Create PythonAnywhere Account**
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Sign up for a free account (or paid if you need more resources)

2. **Set up Web App**
   - Dashboard → New Web App
   - Choose: Python 3.11 + FastAPI (or manually add FastAPI)
   - Accept default settings

3. **Clone Your Repository**
   - Dashboard → Bash Console
   - Run:
     ```bash
     git clone https://github.com/raghavmittal429-hash/medical-trend.git ~/medical-trend
     cd ~/medical-trend
     python3 -m venv venv
     source venv/bin/activate
     pip install -r backend/requirements.txt
     ```

4. **Configure WSGI File**
   - Web tab → WSGI configuration file
   - Edit the WSGI file (usually `/var/www/USERNAME_pythonanywhere_com_wsgi.py`)
   - Replace content with:
     ```python
     import sys
     sys.path.insert(0, '/home/USERNAME/medical-trend')
     from backend.main import app
     application = app
     ```

5. **Add Environment Variables**
   - Web tab → Environment variables
   - Add:
     - `ANTHROPIC_API_KEY` = your key
     - `LANGSMITH_API_KEY` = your key (if used)
     - `ALLOWED_ORIGINS` = `https://raghavmittal429-hash.github.io`

6. **Reload Web App**
   - Click the green **Reload** button on the Web tab

7. **Your backend URL will be:**
   ```
   https://USERNAME.pythonanywhere.com
   ```

### CI/CD via GitHub Actions

The workflow automatically deploys on push to `main`:
- Pulls latest code from GitHub
- Installs dependencies  
- Reloads the WSGI app

**Required GitHub Secrets:**
- `PYTHONANYWHERE_HOST` = `ssh.pythonanywhere.com`
- `PYTHONANYWHERE_USERNAME` = your PythonAnywhere username
- `PYTHONANYWHERE_SSH_KEY` = your private SSH key (see setup below)
- `PYTHONANYWHERE_APP_DIR` = `medical-trend` (or your directory)

#### Generate SSH Key for Deployment

1. On your local machine, generate SSH key:
   ```bash
   ssh-keygen -t rsa -b 4096 -f pythonanywhere_deploy_key
   ```
   - Press Enter when asked for passphrase (leave empty)

2. Go to PythonAnywhere → Account → SSH keys
   - Copy contents of `pythonanywhere_deploy_key.pub`
   - Add to "Authorized keys"

3. Add to GitHub Secrets:
   - Go to your repo → Settings → Secrets
   - Create `PYTHONANYWHERE_SSH_KEY`
   - Paste contents of `pythonanywhere_deploy_key` (private key)

## GitHub Actions Deployment

A workflow has been added at `.github/workflows/deploy.yml` to deploy the backend to PythonAnywhere and the frontend to GitHub Pages on pushes to `main`.

Add these GitHub repository secrets before push:
- `PYTHONANYWHERE_HOST`
- `PYTHONANYWHERE_USERNAME`
- `PYTHONANYWHERE_SSH_KEY`
- `PYTHONANYWHERE_APP_DIR`
- `API_BASE_URL` (your PythonAnywhere backend URL)

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
- `API_BASE_URL` should be: `https://USERNAME.pythonanywhere.com`
- `ALLOWED_ORIGINS` should be: `https://raghavmittal429-hash.github.io`

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
| `API_BASE_URL` | GitHub Actions (build-time) | `https://USERNAME.pythonanywhere.com` |
| `ANTHROPIC_API_KEY` | PythonAnywhere | your Anthropic key |
| `ALLOWED_ORIGINS` | PythonAnywhere | `https://raghavmittal429-hash.github.io` |
| `LANGSMITH_API_KEY` | PythonAnywhere | your LangSmith key (optional) |
