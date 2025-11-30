# Household Service Application - Deployment Guide

## 🚀 Deploying to Render

This guide will help you deploy your Flask application to Render with PostgreSQL database.

### Prerequisites
- GitHub account
- Render account (free tier works fine)
- Your code pushed to a GitHub repository

---

## 📋 Deployment Steps

### Step 1: Push Your Code to GitHub

Make sure your code is in a GitHub repository. If not already done:

```bash
git init
git add .
git commit -m "Initial commit - ready for deployment"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo-name.git
git push -u origin main
```

### Step 2: Deploy on Render

#### Option A: Using Blueprint (Recommended - Automated)

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Click "New +" → "Blueprint"**
3. **Connect your GitHub repository**
4. **Render will automatically**:
   - Create a PostgreSQL database (free tier)
   - Create a web service
   - Set up environment variables
   - Deploy your application

#### Option B: Manual Setup

If the blueprint doesn't work, follow these manual steps:

##### 1. Create PostgreSQL Database
1. Go to Render Dashboard
2. Click "New +" → "PostgreSQL"
3. Fill in:
   - **Name**: `household-service-db`
   - **Database**: `household_service`
   - **User**: `household_user`
   - **Region**: Choose closest to your users
   - **Plan**: Free
4. Click "Create Database"
5. **Save the Internal Database URL** (you'll need it)

##### 2. Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Fill in:
   - **Name**: `household-service-app`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn main:app`
   - **Plan**: Free

##### 3. Configure Environment Variables
In the "Environment" section, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | (Paste the Internal Database URL from Step 1) |
| `SECRET_KEY` | (Generate a random string - use: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `FLASK_ENV` | `production` |
| `PYTHON_VERSION` | `3.12.0` |

4. Click "Create Web Service"

---

## 🔧 What the Deployment Does

### Files Created for Deployment:

1. **`render.yaml`**: Blueprint configuration
   - Defines both database and web service
   - Sets up environment variables automatically

2. **`build.sh`**: Build script
   - Installs Python dependencies
   - Creates necessary directories
   - Runs database migrations

3. **Updated `main.py`**:
   - Automatically detects production environment
   - Uses PostgreSQL in production
   - Uses SQLite for local development
   - Configures host/port for Render

4. **Updated `.gitignore`**:
   - Prevents committing sensitive files
   - Excludes virtual environment
   - Excludes local database files

---

## 🎯 Key Features

### Automatic Environment Detection
The app automatically switches between:
- **Local Development**: SQLite database
- **Production (Render)**: PostgreSQL database

### Database Migration
On first deployment, all tables are created automatically using SQLAlchemy's `db.create_all()`

### Security
- Secret keys use environment variables
- Database credentials not hardcoded
- `.env` file excluded from git

---

## 🐛 Troubleshooting

### Build Fails

**Error**: `Permission denied: ./build.sh`
```bash
# On your local machine, make build.sh executable:
git update-index --chmod=+x build.sh
git commit -m "Make build.sh executable"
git push
```

### Database Connection Fails

**Check**:
1. DATABASE_URL is set correctly in environment variables
2. It starts with `postgresql://` not `postgres://` (auto-fixed in code)
3. Database service is running

### Application Crashes

**View Logs**:
1. Go to your web service in Render
2. Click "Logs" tab
3. Look for error messages

**Common Issues**:
- Missing environment variables
- Port configuration (fixed in code)
- Database connection timeout

### Import Errors

If you get `ModuleNotFoundError`:
1. Make sure all dependencies are in `requirements.txt`
2. Rebuild the service

---

## 🔄 Updating Your Application

After making changes:

```bash
git add .
git commit -m "Your update message"
git push
```

Render will automatically:
- Detect the push
- Rebuild your application
- Deploy the new version

---

## 📊 Database Management

### Viewing Data
Use Render's built-in database shell:
1. Go to your database in Render Dashboard
2. Click "Connect" → "External Connection"
3. Use provided credentials with a PostgreSQL client (like pgAdmin or DBeaver)

### Backup
Render automatically backs up your free-tier database weekly.

---

## 💰 Cost

- **Database**: Free tier (1GB storage, limited connections)
- **Web Service**: Free tier (750 hours/month, sleeps after 15 min inactivity)
- **Total**: $0/month (with limitations)

### Free Tier Limitations:
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- 750 hours/month service uptime
- 1GB database storage

---

## 🎉 Success!

Your application should be live at:
```
https://household-service-app.onrender.com
```

The first deployment takes 5-10 minutes.

---

## 📝 Next Steps

1. Test all functionality on production
2. Set up custom domain (optional)
3. Monitor application logs
4. Consider upgrading to paid tier for:
   - No spin-down
   - More storage
   - Better performance

---

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **Flask Docs**: https://flask.palletsprojects.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

---

## ⚠️ Important Notes

1. **Do NOT commit `.env` file** - It's in `.gitignore`
2. **Database data persists** - PostgreSQL data won't be lost on redeploy
3. **Static files**: Uploaded PDFs may not persist on free tier (consider cloud storage for production)
4. **First request**: May be slow due to cold start

---

## 🔐 Security Checklist

- ✅ `.env` excluded from git
- ✅ Secret keys use environment variables
- ✅ Database credentials not hardcoded
- ✅ Debug mode disabled in production
- ✅ Updated dependencies (Werkzeug 3.0.3)

---

Good luck with your deployment! 🚀
