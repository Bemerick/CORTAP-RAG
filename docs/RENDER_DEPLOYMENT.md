# Render Deployment Guide - CORTAP RAG v2.2.0

Complete guide for deploying CORTAP RAG with PostgreSQL database and Alembic migrations to Render.

## 🎯 Prerequisites

- Render account (https://render.com)
- GitHub repository with latest code
- OpenAI API key
- Git installed locally

## 📋 Deployment Architecture

```
┌─────────────────────────────────────────────┐
│           Render Services                    │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │  PostgreSQL DB   │  │  Backend API    │ │
│  │  (cortap-rag-db) │◄─┤  (Python/Fast   │ │
│  │                  │  │   API)          │ │
│  │  • Structured    │  │  • Alembic      │ │
│  │    Data          │  │    Migrations   │ │
│  │  • Query         │  │  • ChromaDB     │ │
│  │    Processing    │  │    (Vector)     │ │
│  └──────────────────┘  └─────────────────┘ │
│                              ▲               │
│                              │               │
│                        ┌─────┴─────────────┐ │
│                        │  Frontend (React) │ │
│                        │  Static Site      │ │
│                        └───────────────────┘ │
└─────────────────────────────────────────────┘
```

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Ensure all changes are committed:**
   ```bash
   git status
   git add .
   git commit -m "Prepare for Render deployment with PostgreSQL"
   git push origin main
   ```

2. **Verify required files exist:**
   - ✅ `render.yaml` (updated with PostgreSQL)
   - ✅ `backend/requirements.txt` (includes alembic, sqlalchemy, psycopg2-binary)
   - ✅ `backend/alembic.ini` (Alembic configuration)
   - ✅ `backend/alembic/` (migration files)
   - ✅ `backend/scripts/deploy.sh` (deployment script)

### Step 2: Create New Render Services

#### Option A: Using render.yaml (Recommended)

1. **Go to Render Dashboard:** https://dashboard.render.com/

2. **Click "New" → "Blueprint"**

3. **Connect your GitHub repository**

4. **Render will automatically detect `render.yaml`**
   - Creates 3 services:
     - `cortap-rag-db` (PostgreSQL)
     - `cortap-rag-backend` (Web Service)
     - `cortap-rag-frontend` (Static Site)

5. **Configure environment variables:**
   - Click on `cortap-rag-backend` service
   - Go to "Environment"
   - Set `OPENAI_API_KEY` (from your OpenAI account)
   - Verify `DATABASE_URL` is auto-linked from database

6. **Deploy!**

#### Option B: Manual Service Creation

If you prefer manual setup:

##### 2.1 Create PostgreSQL Database

1. Click "New" → "PostgreSQL"
2. Settings:
   - **Name:** `cortap-rag-db`
   - **Database:** `cortap_rag`
   - **User:** `cortap_user` (auto-generated)
   - **Region:** Oregon (or your preference)
   - **Plan:** Starter ($7/month)
3. Click "Create Database"
4. Wait for database to be created (~2 minutes)
5. **Save the Internal Database URL** (you'll need this)

##### 2.2 Create Backend Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Settings:
   - **Name:** `cortap-rag-backend`
   - **Region:** Oregon (same as database)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && alembic upgrade head && python ingest_full_guide.py
     ```
   - **Start Command:**
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan:** Starter ($7/month)

4. **Add Environment Variables:**
   ```
   OPENAI_API_KEY=<your-openai-api-key>
   DATABASE_URL=<internal-database-url-from-step-2.1>
   CHROMA_DB_PATH=/opt/render/project/src/chroma_db
   ENVIRONMENT=production
   ```

5. **Add Disk:**
   - Name: `chroma-data`
   - Mount Path: `/opt/render/project/src/chroma_db`
   - Size: 1 GB

6. Click "Create Web Service"

##### 2.3 Create Frontend Service

1. Click "New" → "Static Site"
2. Connect your GitHub repository
3. Settings:
   - **Name:** `cortap-rag-frontend`
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `./dist`

4. **Add Environment Variable:**
   ```
   VITE_API_URL=<backend-service-url>
   ```
   (Get this from backend service after it's created)

5. **Add Redirect Rule:**
   - Type: Rewrite
   - Source: `/*`
   - Destination: `/index.html`

6. Click "Create Static Site"

### Step 3: Verify Deployment

1. **Check Database Service:**
   ```
   Status: Available ✅
   Connection String: postgres://...
   ```

2. **Check Backend Service:**
   - View Logs:
     ```
     📊 Running database migrations...
     ✅ Database migrations completed successfully
     🎉 CORTAP RAG is ready to serve requests
     ```
   - Test API endpoint: `https://cortap-rag-backend.onrender.com/health`

3. **Check Frontend:**
   - Open frontend URL
   - Verify it loads
   - Test a query

## 🔄 Database Migration Management

### Automatic Migrations on Deploy

The build command includes `alembic upgrade head`, which:
- Runs automatically on every deployment
- Applies any pending migrations
- Ensures database schema is up-to-date

### Manual Migration Commands

To run migrations manually via Render Shell:

1. **Access Backend Service Shell:**
   - Go to backend service dashboard
   - Click "Shell" tab
   - Or use Render CLI: `render shell cortap-rag-backend`

2. **Check current migration status:**
   ```bash
   cd backend
   alembic current
   ```

3. **View migration history:**
   ```bash
   alembic history
   ```

4. **Apply migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Rollback one migration:**
   ```bash
   alembic downgrade -1
   ```

### Creating New Migrations

1. **Make schema changes locally** in `backend/database/schemas.py`

2. **Generate migration:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add new feature"
   ```

3. **Review generated migration** in `backend/alembic/versions/`

4. **Test locally:**
   ```bash
   alembic upgrade head
   ```

5. **Commit and push:**
   ```bash
   git add backend/alembic/versions/
   git commit -m "Add migration: Add new feature"
   git push origin main
   ```

6. **Render will auto-deploy and apply migration**

## 🔧 Environment Variables Reference

### Backend Service

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key for embeddings |
| `DATABASE_URL` | ✅ Yes | - | PostgreSQL connection string (auto-linked) |
| `CHROMA_DB_PATH` | ✅ Yes | `/opt/render/project/src/chroma_db` | ChromaDB storage path |
| `ENVIRONMENT` | ✅ Yes | `production` | Application environment |

### Frontend Service

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | ✅ Yes | - | Backend API URL (auto-linked) |

## 🐛 Troubleshooting

### Database Connection Issues

**Problem:** Backend can't connect to database

**Solutions:**
1. Verify `DATABASE_URL` is set correctly:
   ```bash
   echo $DATABASE_URL
   ```

2. Check database service status (must be "Available")

3. Verify internal database URL format:
   ```
   postgresql://user:password@hostname:5432/database
   ```

4. Check backend logs for connection errors

### Migration Failures

**Problem:** `alembic upgrade head` fails during build

**Solutions:**
1. Check migration files for errors:
   ```bash
   cd backend
   alembic history
   ```

2. Manually run migration in Shell:
   ```bash
   cd backend
   alembic upgrade head --sql  # Show SQL without applying
   ```

3. If migration is broken, rollback:
   ```bash
   alembic downgrade -1
   ```

4. Fix migration locally, test, and redeploy

### Build Command Failures

**Problem:** Build fails during `pip install` or `alembic upgrade`

**Solutions:**
1. **Check Python version:** Render uses Python 3.11 by default
   - Add `runtime.txt` with: `python-3.11.0`

2. **Check requirements.txt:**
   - Ensure all dependencies have versions
   - Test locally: `pip install -r requirements.txt`

3. **Check migration dependencies:**
   - Database must be running before migration
   - Verify `DATABASE_URL` is set

4. **View full build logs:**
   - Go to "Events" tab in service dashboard
   - Click on failed build

### ChromaDB Disk Issues

**Problem:** ChromaDB data not persisting

**Solutions:**
1. Verify disk is attached:
   - Go to backend service → "Disk" tab
   - Check mount path matches `CHROMA_DB_PATH`

2. Check disk usage:
   ```bash
   df -h /opt/render/project/src/chroma_db
   ```

3. Increase disk size if needed (Settings → Disk)

## 📊 Monitoring & Logs

### Viewing Logs

1. **Real-time logs:**
   - Go to service dashboard
   - Click "Logs" tab

2. **Filter logs:**
   - Use search: `ERROR`, `database`, `migration`

3. **Download logs:**
   - Click "Download" button

### Health Checks

1. **Backend health endpoint:**
   ```bash
   curl https://cortap-rag-backend.onrender.com/health
   ```

2. **Database health:**
   ```bash
   # In Render Shell
   cd backend
   python -c "from database.connection import get_db; next(get_db()); print('OK')"
   ```

## 🔄 Updating Deployment

### Rolling Updates

Render performs zero-downtime deployments:
1. Push changes to GitHub
2. Render auto-detects changes
3. Builds new version
4. Runs migrations
5. Switches traffic to new version

### Manual Redeploy

1. Go to service dashboard
2. Click "Manual Deploy" → "Deploy latest commit"

### Rollback

1. Go to "Events" tab
2. Find previous successful deploy
3. Click "Redeploy"

## 🔐 Security Best Practices

1. **Never commit secrets:**
   - Use Render environment variables
   - Keep `.env` files local only

2. **Use internal URLs:**
   - Database uses internal connection (faster, free)
   - Backend → Database: internal URL
   - Frontend → Backend: external URL

3. **Restrict database access:**
   - IP allow list (if needed)
   - Use strong passwords

4. **Enable auto-updates:**
   - Render can auto-deploy on push
   - Review changes before merging

## 💰 Cost Estimation

### Free Tier
- PostgreSQL: **Not available** (requires paid plan)
- Backend: $0 (first 750 hours/month)
- Frontend: $0 (100 GB bandwidth)

### Starter Plan (Recommended)
- PostgreSQL: **$7/month**
- Backend: **$7/month**
- Frontend: **$0** (static site)
- Disk (1GB): **Included**
- **Total: ~$14/month**

### Professional Plan
- PostgreSQL: $20/month (larger storage)
- Backend: $25/month (more CPU/memory)
- Frontend: $0
- **Total: ~$45/month**

## 🎉 Success Checklist

After deployment, verify:

- [ ] Database service is "Available"
- [ ] Backend service is "Live"
- [ ] Frontend service is "Live"
- [ ] Migrations completed successfully
- [ ] Health endpoint returns 200 OK
- [ ] Frontend loads and connects to backend
- [ ] Can query structured data
- [ ] Can query RAG knowledge base
- [ ] Logs show no errors

## 📚 Additional Resources

- [Render Docs](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md)
- [HYBRID_ARCHITECTURE.md](./HYBRID_ARCHITECTURE.md)

## 🆘 Support

If you encounter issues:
1. Check logs first
2. Review this guide
3. Check Render status page: https://status.render.com
4. Open issue in project repository

---

**Version:** 2.2.0
**Last Updated:** December 8, 2025
**Deployment Platform:** Render
**Database:** PostgreSQL 14+
