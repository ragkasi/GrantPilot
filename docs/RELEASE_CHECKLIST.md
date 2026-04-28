# GrantPilot Release Checklist

Use this before sharing publicly, tagging a release, or demoing live.

---

## Pre-deploy

- [ ] All backend tests pass: `cd backend && python -m pytest tests/ -v`
- [ ] Frontend TypeScript clean: `cd frontend && npm run typecheck`
- [ ] Frontend production build succeeds: `cd frontend && npm run build`
- [ ] MCP tests pass: `cd mcp/grant-context-mcp && python -m pytest tests/ -v`
- [ ] Railway Postgres is at the latest migration revision (`alembic upgrade head`)
- [ ] Railway backend has `ANTHROPIC_API_KEY` set for real analysis
- [ ] Railway backend has `ALLOWED_ORIGINS` set to the live frontend URL
- [ ] Railway frontend has `NEXT_PUBLIC_API_URL` set to the live backend URL
- [ ] Railway backend has a Volume mounted at `/app/uploads` (persistent PDFs)
- [ ] `JWT_SECRET` is a strong random value (not the dev default)

---

## Smoke test (hosted)

Run the readiness check script against the live deployment:

```bash
python scripts/demo_check.py --api-url https://your-backend.up.railway.app
```

Expected: all 5 checks pass and `analysis_source` is reported.

Manual spot-checks:

- [ ] Landing page loads at root URL `/`
- [ ] Login with `demo@grantpilot.local` / `DemoGrantPilot123!` succeeds
- [ ] Dashboard shows BrightPath project with scores (82 / 74)
- [ ] Project detail shows indigo "Demo project" provenance banner
- [ ] Requirements tab loads with 10 rows
- [ ] Draft Answers tab shows 3 answers
- [ ] Download Report generates and saves a PDF
- [ ] Account page shows "Password changes are disabled for the demo account"
- [ ] API docs accessible at `https://your-backend.up.railway.app/docs`

---

## Real pipeline validation

- [ ] Create a new project (any name)
- [ ] Upload `demo-assets/sample-grant-opportunity.txt` as Grant Opportunity Document
- [ ] Upload `demo-assets/sample-mission-statement.txt` as Mission Statement
- [ ] Click **Run Analysis**
- [ ] Confirm emerald "AI analysis grounded in your uploaded documents" banner appears
- [ ] Confirm requirements list contains items from the sample grant (501c3, Ohio, IRS letter, etc.)
- [ ] Confirm requirements are NOT the BrightPath mock data (different requirement text)

---

## Screenshots to capture

For GitHub README, portfolio pages, or LinkedIn post:

| # | What to capture | Page / State |
|---|---|---|
| 1 | Landing page hero (above the fold) | `/` |
| 2 | Dashboard with BrightPath project card (scores visible) | `/dashboard` |
| 3 | Project detail — indigo provenance banner + score rings | `/projects/proj_stem_2026` |
| 4 | Requirements tab — table with one row expanded showing evidence | Same page, Requirements tab |
| 5 | Draft Answers tab — one answer expanded with citations | Same page, Draft Answers tab |
| 6 | Missing Docs & Risks tab — risk flags visible | Same page, Risks tab |
| 7 | PDF report first page (cover with scores and org name) | Downloaded PDF |
| 8 | Emerald "real_pipeline" banner after uploading demo-assets | New project after real analysis |
| 9 | API docs (Swagger UI) | `/docs` on the backend |
| 10 | Account page — demo account with disabled password change notice | `/account` |

**Recommended resolution:** 1440×900 or 1280×800, light theme, browser chrome visible.

---

## Git release

After all checks pass:

```bash
# Stage everything
git add -A

# Commit
git commit -m "feat: Phase 19 — org delete, demo password lock, retrospective, release prep"

# Tag the release
git tag v1.0.0-demo

# Push
git push origin main --tags
```

---

## Demo reset (if needed before a live demo)

```bash
# Local
cd backend && python scripts/reset_demo.py

# Hosted (Railway — run via CLI or exec into container)
railway run python scripts/reset_demo.py
```

---

## Sharing publicly

- [ ] GitHub repo is public (or visibility set correctly)
- [ ] `backend/.env` is in `.gitignore` and NOT committed
- [ ] No real API keys or JWT secrets in committed files
- [ ] README live demo URL points to the correct hosted URL
- [ ] `demo-assets/` files are clearly labeled as fictional sample data
