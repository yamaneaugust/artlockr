# ArtLockr - Streamlit Deployment Guide

This guide will help you deploy ArtLockr to Streamlit Cloud and get a public URL that anyone can access.

## What You Get

- ✅ Free public URL (e.g., `https://your-app.streamlit.app`)
- ✅ No server setup required
- ✅ Auto-updates when you push to GitHub
- ✅ HTTPS enabled by default
- ✅ Easy to share with friends

## Quick Start (5 Minutes)

### Step 1: Push to GitHub

The code is already on your branch `claude/access-resource-url-rAvil`. Just make sure it's pushed:

```bash
git push -u origin claude/access-resource-url-rAvil
```

### Step 2: Sign Up for Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Click "Sign up" (it's FREE!)
3. Sign in with your GitHub account
4. Authorize Streamlit to access your repositories

### Step 3: Deploy Your App

1. Click "New app" button
2. Select your repository: `yamaneaugust/artlockr`
3. Select branch: `claude/access-resource-url-rAvil`
4. Set main file path: `streamlit_app.py`
5. Click "Deploy!"

### Step 4: Get Your URL

After deployment (takes ~2 minutes), you'll get a public URL like:

```
https://artlockr.streamlit.app
```

Share this URL with anyone - they can access the app directly in their browser!

## Alternative: Run Locally (Optional)

If you want to test locally first:

```bash
# Install streamlit
pip install streamlit pillow

# Run the app
streamlit run streamlit_app.py
```

This will open at `http://localhost:8501`

## Features Included

✅ **Upload Artwork** - Upload and protect your artwork
✅ **Copyright Detection** - Scan for potential infringement
✅ **Block Organizations** - Prevent unauthorized access
✅ **Analytics Dashboard** - Track your protection activity
✅ **Privacy First** - Feature-only storage (demo mode)
✅ **Beautiful UI** - Modern, responsive design

## Differences from Full Version

This Streamlit version is a simplified demo:

- **Mock Detection**: Uses simulated detection (full version uses ResNet + FAISS)
- **Session Storage**: Data stored in browser session (full version uses PostgreSQL)
- **No Authentication**: Single user demo (full version has multi-user auth)
- **Simplified Features**: Core functionality only

Perfect for demonstrating the concept and UI to your friend!

## Updating the App

After deploying, any changes you push to GitHub will automatically redeploy:

```bash
# Make changes to streamlit_app.py
# Then commit and push
git add streamlit_app.py
git commit -m "Update app"
git push
```

Streamlit Cloud will detect the changes and redeploy automatically!

## Troubleshooting

**App won't start?**
- Check that `streamlit_requirements.txt` is in the repository
- Verify the file path is `streamlit_app.py`

**Need help?**
- Streamlit docs: https://docs.streamlit.io/
- Streamlit community: https://discuss.streamlit.io/

## Custom Domain (Optional)

You can also set up a custom domain like `artlockr.com` in Streamlit Cloud settings!

---

**That's it!** Your app will be live at a public URL in just a few minutes. 🚀
