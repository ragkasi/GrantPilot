# GrantPilot Deployment Guide

## Architecture Overview

```
Browser
  |
  v
Next.js Frontend  (port 3000)
  |
  v (REST API calls with Bearer token)
FastAPI Backend   (port 8000)
  |
  |-- PostgreSQL (port 5432)
  |-- Local file storage (uploads/)
  |-- AI Provider API (Anthropic / OpenAI)
```

All three services can be run locally via Docker Compose, or deployed
independently to any cloud platform that supports containers.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.x | Multi-service orchestration |
| Python | 3.11+ | Backend (local dev only) |
| Node.js | 20+ | Frontend (local dev only) |
| PostgreSQL | 16+ | Production database (Docker provides this) |

---

## Quick Start — Local Stack via Docker Compose

### 1. Clone and prepare environment

```bash
git clone https://github.com/ragkasi/GrantPilot.git
cd GrantPilot

# Copy the root env template
cp .env.example .env
```

### 2. Fill in required secrets

Edit `.env`:

```bash
# Required: generate with python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=your-strong-random-secret-here

# Optional: needed for real AI analysis
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Build and start

```bash
docker-compose up --build
```

The first boot:
- Builds both images (~3-5 minutes)
- Starts Postgres and waits for it to be healthy
- Runs `alembic upgrade head` (all 3 migrations)
- Seeds the demo user and BrightPath project
- Starts FastAPI on port 8000 and Next.js on port 3000

### 4. Access the app

- Frontend: **http://localhost:3000**
- API docs: **http://localhost:8000/docs**
- Demo login: `demo@grantpilot.local` / `DemoGrantPilot123!`

---

## Environment Variables

### Root `.env` (docker-compose)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | **Yes** | — | Random secret for JWT signing |
| `POSTGRES_PASSWORD` | No | `devpassword` | Postgres password |
| `ANTHROPIC_API_KEY` | No | — | Enables real AI analysis |
| `OPENAI_API_KEY` | No | — | Enables OpenAI embeddings |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated frontend origins |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Public backend URL (baked at build time) |
| `DEBUG` | No | `false` | Enable debug logging |

### Backend `.env` (local dev)

Copy `backend/.env.example` to `backend/.env` for local development without Docker.

---

## Database Migrations

GrantPilot uses Alembic for schema migrations.

### How it works

| Mode | How schema is created |
|------|----------------------|
| Local dev (SQLite) | `create_all_tables()` runs on startup via SQLAlchemy metadata |
| Docker / Postgres | `alembic upgrade head` runs in `entrypoint.sh` before the app starts |

### Running migrations manually

```bash
# From the backend directory
cd backend

# Apply all pending migrations
PYTHONPATH=. alembic upgrade head

# Check current revision
PYTHONPATH=. alembic current

# View migration history
PYTHONPATH=. alembic history
```

### Creating a new migration

```bash
cd backend
PYTHONPATH=. alembic revision --autogenerate -m "description of change"
# Review the generated file in alembic/versions/
PYTHONPATH=. alembic upgrade head
```

---

## CORS Configuration

Set `ALLOWED_ORIGINS` to a comma-separated list of allowed frontend origins:

```bash
# Single origin
ALLOWED_ORIGINS=https://app.yourdomain.com

# Multiple origins
ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
```

The backend rejects cross-origin requests from any origin not in this list.

---

## Rate Limiting

Auth endpoints are rate-limited to prevent brute-force attacks:

| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 10 requests / 60 seconds per IP |
| `POST /auth/register` | 5 requests / 1 hour per IP |

The current implementation uses an in-memory store. For multi-instance deployments,
replace `app/core/rate_limit.py` with a Redis-backed implementation.

---

## Health Checks

| Service | Endpoint | Expected response |
|---------|----------|-------------------|
| Backend | `GET /health` | `{"status": "ok"}` |
| Frontend | `GET /api/health` | `{"status": "ok"}` |

Both are used by Docker health checks and suitable for load balancer probes.

---

## Production Deployment

### Recommended stack

```
Internet → HTTPS Reverse Proxy (Nginx / Caddy) → Frontend :3000
                                               → Backend :8000
                                  Postgres :5432 (internal only)
```

### Nginx example (minimal)

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
}
```

### Critical production settings

1. **JWT_SECRET** — must be a cryptographically strong random value:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **ALLOWED_ORIGINS** — set to your actual frontend domain

3. **DATABASE_URL** — use Postgres in production, not SQLite

4. **UPLOAD_DIR** — should be a persistent volume, not a container-local path

5. **ANTHROPIC_API_KEY** — required for real AI grant analysis

---

## File Storage

Uploaded documents are stored in `UPLOAD_DIR` (default: `uploads/`).

In Docker Compose this is a named volume (`uploads`) that persists across restarts.
In production, mount this to a persistent volume or swap `storage_service.py` for
an S3/cloud storage implementation.

---

## CI / GitHub Actions

The `.github/workflows/ci.yml` workflow runs automatically on every push to `main`:

| Job | Trigger | What it does |
|-----|---------|--------------|
| `backend-tests` | Every push/PR | Runs pytest (152 tests) |
| `frontend-checks` | Every push/PR | Typecheck + production build |
| `e2e-tests` | `main` branch only | Playwright happy-path tests (19 tests) |

### Required GitHub Secrets

No secrets are strictly required for the backend tests or frontend build.

For the E2E job to pass, no secrets are needed (it uses the demo in-memory DB
with the default dev JWT secret).

If you want to test real AI analysis in CI, add:
- `ANTHROPIC_API_KEY` as a GitHub Actions secret

### Running CI locally

```bash
# Backend tests
cd backend && PYTHONPATH=. python -m pytest tests/ -v

# Frontend typecheck
cd frontend && npm run typecheck

# Frontend build
cd frontend && npm run build

# E2E tests (requires both servers running)
# Terminal 1: cd backend && PYTHONPATH=. python -m uvicorn app.main:app --port 8000
# Terminal 2: cd frontend && npm run dev
# Terminal 3: cd frontend && npx playwright test
```

---

## Upgrading

1. Pull the latest code
2. Run `alembic upgrade head` if there are new migrations
3. Rebuild Docker images: `docker-compose up --build`

---

## Troubleshooting

**Backend fails to start with "relation does not exist"**
→ Run `alembic upgrade head` manually before starting the backend.

**Frontend shows "Failed to load project data"**
→ Verify `NEXT_PUBLIC_API_URL` points to the correct backend URL and CORS is configured.

**`ALLOWED_ORIGINS` not accepting my domain**
→ Check there are no trailing slashes in the origin value.

**Rate limit 429 on login**
→ Wait 60 seconds between login attempts, or restart the backend to reset in-memory counters.
