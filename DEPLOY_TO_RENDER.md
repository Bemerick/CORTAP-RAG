# 🚀 Quick Deploy to Render

Fast-track guide to deploy CORTAP RAG v2.2.0 to Render with PostgreSQL.

## ⚡ Quick Start (5 Minutes)

### 1. Pre-Flight Check
```bash
bash backend/scripts/pre_deploy_check.sh
```

All checks should pass! ✅

### 2. Commit & Push
```bash
git add .
git commit -m "Deploy CORTAP RAG v2.2.0 to Render"
git push origin main
```

### 3. Deploy on Render

**Go to:** https://dashboard.render.com/

**Click:** "New" → "Blueprint"

**Select:** Your GitHub repository

**That's it!** Render will:
- ✅ Create PostgreSQL database
- ✅ Create backend API service
- ✅ Create frontend static site
- ✅ Run database migrations automatically
- ✅ Deploy your application

### 4. Configure Secrets

After services are created:

1. Go to `cortap-rag-backend` service
2. Click "Environment" tab
3. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-...your-key...
   ```
4. Save changes (service will redeploy)

### 5. Test It! 🎉

Visit your frontend URL (e.g., `https://cortap-rag-frontend.onrender.com`)

Try a query:
- "How many indicators are in section 1?"
- "What are the requirements for assessments?"

## 📊 What Gets Deployed

```
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│  • Structured query data            │
│  • Automatic migrations             │
│  Cost: $7/month                     │
└─────────────────────────────────────┘
           ▲
           │
┌─────────────────────────────────────┐
│  Backend API (Python/FastAPI)       │
│  • Hybrid RAG+DB queries            │
│  • ChromaDB vector store            │
│  • Auto-migration on deploy         │
│  Cost: $7/month                     │
└─────────────────────────────────────┘
           ▲
           │
┌─────────────────────────────────────┐
│  Frontend (React/Vite)              │
│  • Static site                      │
│  Cost: FREE                         │
└─────────────────────────────────────┘

Total: ~$14/month
```

## 🔄 Updating Your Deployment

Just push to GitHub:
```bash
git add .
git commit -m "Update feature X"
git push origin main
```

Render auto-deploys! 🚀

## 📋 Environment Variables

### Backend (Required)
| Variable | Where to Get |
|----------|--------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `DATABASE_URL` | Auto-linked by Render |
| `CHROMA_DB_PATH` | Auto-set (default) |
| `ENVIRONMENT` | Auto-set to "production" |

### Frontend (Auto-configured)
| Variable | Source |
|----------|--------|
| `VITE_API_URL` | Auto-linked to backend |

## 🐛 Troubleshooting

### Build Fails
```bash
# Check logs in Render dashboard
# Common issues:
# 1. Missing OPENAI_API_KEY → Add in Environment tab
# 2. Migration error → Check database is running
# 3. Python deps → Check requirements.txt
```

### Database Connection Error
```bash
# Verify DATABASE_URL is set
# Check database service status (must be "Available")
# Ensure backend and database are in same region
```

### Frontend Can't Connect
```bash
# Check VITE_API_URL is set correctly
# Verify backend service is "Live"
# Check CORS settings in backend
```

## 📚 Detailed Documentation

For in-depth guides, see:
- [Complete Render Deployment Guide](./docs/RENDER_DEPLOYMENT.md)
- [Database Migrations](./docs/DATABASE_MIGRATIONS.md)
- [Hybrid Architecture](./docs/HYBRID_ARCHITECTURE.md)

## ✅ Success Checklist

After deployment:
- [ ] Database service shows "Available"
- [ ] Backend service shows "Live"
- [ ] Frontend service shows "Live"
- [ ] Backend logs show "migrations completed"
- [ ] Can load frontend in browser
- [ ] Can submit and get responses to queries
- [ ] Both RAG and structured queries work

## 🆘 Need Help?

1. **Pre-deployment checks fail?**
   - Run: `bash backend/scripts/pre_deploy_check.sh`
   - Fix any ❌ errors shown

2. **Deployment issues?**
   - Check [RENDER_DEPLOYMENT.md](./docs/RENDER_DEPLOYMENT.md)
   - View service logs in Render dashboard

3. **Database issues?**
   - See [DATABASE_MIGRATIONS.md](./docs/DATABASE_MIGRATIONS.md)

## 🎯 Next Steps

Once deployed:
1. ✅ Test all query types
2. ✅ Monitor logs for errors
3. ✅ Set up custom domain (optional)
4. ✅ Configure alerts in Render
5. ✅ Review performance metrics

---

**Ready to deploy?** Run the pre-flight check:
```bash
bash backend/scripts/pre_deploy_check.sh
```

Then follow steps 2-5 above! 🚀
