# ClaimForge — Production Deployment Guide

This guide explains how to access ClaimForge locally and how to deploy the **entire project folder** to any cloud hosting provider or server.

---

## 1. Localhost Links (Currently Running)

Your local development servers are running and active:

| Service | Localhost URL | Description |
| :--- | :--- | :--- |
| **ClaimForge Web App** | [http://localhost:3000](http://localhost:3000) | Main interactive Next.js user interface |
| **Demo Scenarios & Seeder** | [http://localhost:3000/demo](http://localhost:3000/demo) | 4 pre-packaged synthetic medical cases |
| **Executive Claims Dashboard** | [http://localhost:3000/dashboard](http://localhost:3000/dashboard) | Live metrics, claims list, status filters |
| **New Claim Intake** | [http://localhost:3000/claims/new](http://localhost:3000/claims/new) | File intake, auto-extraction, analysis |
| **Interactive API Docs (Swagger)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive FastAPI OpenAPI documentation |
| **Alternative API Docs (ReDoc)** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Clean API schema reference |
| **API Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Live system status & database connectivity |

> **Pro Tip:** Thanks to Next.js API proxy rewrites, API endpoints are also reachable directly through port 3000:
> - [http://localhost:3000/health](http://localhost:3000/health)
> - [http://localhost:3000/docs](http://localhost:3000/docs)
> - [http://localhost:3000/api/dashboard/stats](http://localhost:3000/api/dashboard/stats)

---

## 2. Deploying the Total Folder

The repository is now pre-configured so that **uploading or pushing the entire folder** deploys both frontend and backend seamlessly.

### How it Works
1. **Next.js API Rewrites**: Next.js automatically proxies `/api/*` to the FastAPI backend. This eliminates CORS issues and means you only need to expose **one public web port**.
2. **Unified Root `Dockerfile`**: Packages the Next.js frontend and FastAPI backend into a single production container using a lightweight startup orchestrator (`entrypoint.sh`).
3. **Multi-Container `docker-compose.yml`**: Configured with named volumes and internal private networking for microservice hosting.
4. **Automated Clean Packaging**: Windows virtual environments (`venv/`) and `node_modules/` are automatically excluded by `.gitignore`, `.dockerignore`, and `package_project.py`.

---

## 3. Deployment Options

### Option A: Render (Recommended — 100% Free Tier)
Render supports automatic full-stack deployment using the included [render.yaml](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/render.yaml) blueprint:
1. Push your folder to a GitHub or GitLab repository.
2. Sign in to [Render.com](https://render.com).
3. Click **New +** -> **Blueprint**.
4. Select your repository. Render will automatically detect `render.yaml`, build the Docker container, and give you a live HTTPS URL (e.g. `https://claimforge.onrender.com`).

Alternatively, as a manual **Web Service**:
- Click **New +** -> **Web Service**.
- Select your repository.
- Choose **Docker** as the environment.
- Health Check Path: `/health`.
- Click **Create Web Service**.

---

### Option B: Railway
Railway automatically detects the root [Dockerfile](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/Dockerfile) and [railway.json](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/railway.json):
1. Sign in to [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Railway will automatically build and expose your full-stack app on a public Railway domain.

---

### Option C: Docker Compose (VPS / DigitalOcean / AWS EC2 / Coolify)
If you are deploying to an Ubuntu or Linux cloud server:
```bash
# 1. Clone or copy your folder to the server
git clone <your-repo-url> claimforge
cd claimforge

# 2. Launch full-stack services
docker compose up -d --build

# 3. View running services
docker compose ps
```
The frontend is available at `http://your-server-ip:3000` and backend at `http://your-server-ip:8000`.

---

### Option D: Single-Container Docker (Google Cloud Run / Fly.io / Heroku)
Build and run the unified container locally or on any container platform:
```bash
# Build unified image
docker build -t claimforge:latest .

# Run image on port 3000
docker run -p 3000:3000 claimforge:latest
```

For **Fly.io**:
```bash
fly launch
fly deploy
```

---

### Option E: Uploading as a ZIP Archive
If you are uploading to an online submission portal or a host that accepts a ZIP file:
1. Run the included packaging script:
   ```bash
   python package_project.py
   # or on Windows PowerShell:
   .\package_project.ps1
   ```
2. This creates `claimforge_deployment.zip` (~400 KB), which includes:
   - All backend Python code, models, schemas, and tests
   - All frontend Next.js code, components, and styling
   - Database migrations and fixtures
   - Dockerfile, docker-compose.yml, and platform configs
   - Fully excluding local Windows `venv`, `node_modules`, and temporary cache files.
3. Upload `claimforge_deployment.zip` directly.

---

## 4. Environment Variables Reference

All defaults work out-of-the-box in local and production mode. To customize, set the following environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Environment mode (`development` or `production`) |
| `AI_PROVIDER` | `rule_based` | `rule_based`, `gemini`, `openai`, or `anthropic` |
| `STORAGE_MODE` | `local` | `local` (SQLite + disk) or `supabase` (PostgreSQL + S3) |
| `DATABASE_URL` | `sqlite+aiosqlite:////app/backend/data/claimforge.db` | Async SQLAlchemy database URI |
| `UPLOAD_DIR` | `/app/backend/uploads` | Document upload directory |
| `GEMINI_API_KEY` | *(optional)* | Google Gemini API key if AI_PROVIDER=gemini |
| `OPENAI_API_KEY` | *(optional)* | OpenAI API key if AI_PROVIDER=openai |
| `ANTHROPIC_API_KEY` | *(optional)* | Anthropic Claude API key if AI_PROVIDER=anthropic |
