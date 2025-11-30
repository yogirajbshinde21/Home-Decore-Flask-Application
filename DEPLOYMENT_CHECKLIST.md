# 🚀 Render Deployment Checklist

Use this checklist to deploy your application step by step.

---

## ✅ Pre-Deployment Checklist

- [ ] **1. Make build.sh executable**
  ```bash
  git update-index --chmod=+x build.sh
  ```

- [ ] **2. Verify .env is not tracked**
  ```bash
  git status
  # .env should NOT appear in the list
  ```

- [ ] **3. Test locally**
  ```bash
  .\myvenv\Scripts\python312.exe main.py
  # Visit http://localhost:5000
  # Test basic functionality
  ```

- [ ] **4. Review changes**
  ```bash
  git diff main.py
  git diff requirements.txt
  ```

---

## 📤 Push to GitHub

- [ ] **5. Stage all changes**
  ```bash
  git add .
  ```

- [ ] **6. Commit**
  ```bash
  git commit -m "Ready for Render deployment with PostgreSQL"
  ```

- [ ] **7. Push to GitHub**
  ```bash
  git push origin main
  ```

---

## 🌐 Deploy on Render

### Option A: Blueprint (Recommended)

- [ ] **8. Go to Render Dashboard**
  - Visit: https://dashboard.render.com/
  - Sign in or create account

- [ ] **9. Create new Blueprint**
  - Click "New +" button
  - Select "Blueprint"
  - Connect GitHub account (if not already)
  - Select your repository

- [ ] **10. Review Blueprint**
  - Render will read `render.yaml`
  - Review the resources:
    - PostgreSQL database: `household-service-db`
    - Web service: `household-service-app`

- [ ] **11. Deploy**
  - Click "Apply"
  - Wait 5-10 minutes for initial deployment
  - Monitor logs for any errors

### Option B: Manual Setup

If Blueprint doesn't work, see `DEPLOYMENT.md` Section "Option B: Manual Setup"

---

## 🔍 Post-Deployment Verification

- [ ] **12. Check deployment status**
  - Go to Services in Render Dashboard
  - Ensure both Database and Web Service show "Live"

- [ ] **13. Open your application**
  - Click on web service
  - Click the URL (e.g., `https://household-service-app.onrender.com`)
  - ⏰ First request may take 30 seconds (cold start)

- [ ] **14. Test basic functionality**
  - [ ] Homepage loads
  - [ ] Admin login works
  - [ ] Can create categories
  - [ ] Can create services
  - [ ] Can register professionals/customers

- [ ] **15. Check database**
  - Go to Database in Render Dashboard
  - Click "Connect" tab
  - Verify connection is working

---

## 🐛 Troubleshooting

### If deployment fails:

- [ ] **Check Logs**
  - Go to your web service
  - Click "Logs" tab
  - Look for error messages

- [ ] **Common fixes:**
  - [ ] Verify `build.sh` is executable
  - [ ] Check all dependencies in `requirements.txt`
  - [ ] Verify environment variables are set
  - [ ] Check DATABASE_URL format

### If app crashes:

- [ ] **View Runtime Logs**
  - Check for import errors
  - Check for database connection errors
  - Check for missing environment variables

---

## 🎯 Success Criteria

✅ **Deployment Successful When:**
- Web service shows "Live" status
- Application URL is accessible
- No errors in logs
- Can access homepage
- Admin login works
- Database operations work

---

## 📝 Environment Variables to Set (Manual Setup Only)

If using manual setup, add these in Render:

| Variable | Value | Where to get it |
|----------|-------|-----------------|
| `DATABASE_URL` | Auto-set by Render | Link database in settings |
| `SECRET_KEY` | Random string | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | `production` | Type manually |
| `PYTHON_VERSION` | `3.12.0` | Type manually |

---

## 🔄 Future Updates

To deploy updates later:

```bash
# 1. Make your changes
# 2. Test locally
# 3. Commit and push
git add .
git commit -m "Description of changes"
git push origin main

# 4. Render will auto-deploy (takes 2-5 minutes)
```

---

## 📚 Need Help?

- See `DEPLOYMENT.md` for detailed guide
- See `DEPLOYMENT_SUMMARY.md` for overview
- Check Render docs: https://render.com/docs

---

**Ready? Start with item #1 above! 🚀**
