# 🚂 Railway Deployment Guide for ArtLock

Complete guide to deploy ArtLock (frontend + backend) to Railway.

## Current Status

✅ **Backend Deployed**: `https://artlockr-production.up.railway.app`

## Quick Deploy: Frontend

### Step 1: Push Latest Changes to GitHub

```bash
# Make sure all fixes are pushed
git push origin claude/art-copyright-detection-model-011CUc3YS4Zy7aPDkHdka217
```

### Step 2: Create Frontend Service in Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click your **ArtLock project**
3. Click **"+ New"** → **"GitHub Repo"**
4. Select your `artlockr` repository
5. Railway will ask **"Where is the code?"**
   - Select **Root Directory**: `frontend`
   - Railway auto-detects `frontend/Dockerfile`

### Step 3: Configure Environment Variables

In the Railway frontend service settings:

**Required Environment Variables:**

```bash
VITE_API_URL=https://artlockr-production.up.railway.app/api/v1
```

**Optional (for Stripe):**

```bash
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
```

### Step 4: Generate Public Domain

1. In Railway frontend service → **Settings**
2. Scroll to **Networking** → **Public Networking**
3. Click **"Generate Domain"**
4. You'll get: `https://artlockr-frontend-production.up.railway.app`

### Step 5: Update Backend CORS

Add your frontend URL to backend environment variables:

1. Go to backend service in Railway
2. **Variables** tab
3. Add or update:

```bash
BACKEND_CORS_ORIGINS=["https://artlockr-frontend-production.up.railway.app","http://localhost:3000"]
```

### Step 6: Access Your App! 🎉

- **Frontend (User Interface)**: `https://artlockr-frontend-production.up.railway.app`
- **Backend API**: `https://artlockr-production.up.railway.app`
- **API Docs**: `https://artlockr-production.up.railway.app/docs`

---

## Backend Environment Variables

Make sure these are set in your **backend service**:

### Required:

```bash
# Database (Auto-set by Railway when you add PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/database

# Security (Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-secret-key-here

# CORS (Add your frontend URL)
BACKEND_CORS_ORIGINS=["https://artlockr-frontend-production.up.railway.app"]

# Stripe (Get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Frontend URL (for redirects)
FRONTEND_URL=https://artlockr-frontend-production.up.railway.app
```

### Optional:

```bash
# ML Settings
SIMILARITY_THRESHOLD=0.85
DEVICE=cpu

# File Storage
UPLOAD_DIR=/app/data/uploads
FEATURES_DIR=/app/data/features
```

---

## Troubleshooting

### Frontend shows blank page

**Check:**
1. Browser console for errors
2. Environment variable `VITE_API_URL` is set correctly
3. Backend CORS includes your frontend URL

**Fix:** Redeploy frontend after setting `VITE_API_URL`

### API calls fail with CORS error

**Fix:** Update backend `BACKEND_CORS_ORIGINS` to include frontend URL

### Database connection errors

**Check:**
1. PostgreSQL service is running in Railway
2. `DATABASE_URL` is set in backend environment variables
3. Database is provisioned and connected

**Fix:**
- Go to Railway → **"+ New"** → **"Database"** → **"PostgreSQL"**
- Railway auto-connects it to your backend service

### Images not uploading

**Check:** Railway has persistent storage configured

**Fix:** Railway provides ephemeral storage by default. For production:
- Use AWS S3 for image storage
- Or add Railway Volume (in service Settings → Volumes)

---

## Cost Estimate

Railway Free Tier includes:
- $5 free credit per month
- Enough for small projects

Expected costs:
- **Backend**: ~$3-5/month (512MB RAM)
- **Frontend**: ~$1-2/month (minimal resources)
- **PostgreSQL**: ~$5/month (shared)

**Total**: ~$9-12/month (after free credit)

---

## Production Checklist

Before going live:

- [ ] Set production `SECRET_KEY` (not the default)
- [ ] Use production Stripe keys (not test keys)
- [ ] Configure Stripe webhook in Dashboard
- [ ] Set up database backups (Railway → Settings → Backups)
- [ ] Add custom domain (Railway → Settings → Domains)
- [ ] Enable HTTPS (automatic with Railway domains)
- [ ] Test registration, login, upload, search
- [ ] Monitor logs (Railway → Deployments → View Logs)

---

## Alternative: Deploy Both to Vercel + Render

If Railway doesn't work, use:

**Frontend → Vercel (Free):**
```bash
cd frontend
vercel --prod
```

**Backend → Render (Free tier):**
- Go to https://render.com
- New Web Service → Connect GitHub
- Select `backend/` directory
- Add PostgreSQL database

---

## Need Help?

- Railway Docs: https://docs.railway.app
- ArtLock Issues: https://github.com/yamaneaugust/artlockr/issues
- This session: https://claude.ai/code/session_011CUc3YS4Zy7aPDkHdka217
