#!/usr/bin/env bash

# Quick Start Script for Deployment Preparation
# Run this on Windows using Git Bash or WSL

echo "🚀 Preparing your app for Render deployment..."
echo ""

# Step 1: Make build.sh executable
echo "✅ Step 1: Making build.sh executable..."
git update-index --chmod=+x build.sh
echo "   Done!"
echo ""

# Step 2: Show git status
echo "📋 Step 2: Checking file status..."
git status --short
echo ""

# Step 3: Reminder about .env
echo "⚠️  Step 3: Checking .env is NOT tracked..."
if git ls-files | grep -q "^.env$"; then
    echo "   ❌ WARNING: .env is tracked! Run: git rm --cached .env"
else
    echo "   ✅ Good! .env is not tracked"
fi
echo ""

# Step 4: Instructions
echo "📝 Next steps:"
echo "   1. Review changes: git diff"
echo "   2. Stage files: git add ."
echo "   3. Commit: git commit -m 'Ready for Render deployment'"
echo "   4. Push: git push origin main"
echo ""
echo "   Then go to: https://dashboard.render.com/"
echo "   Click: New + → Blueprint → Select your repo"
echo ""
echo "✨ Read DEPLOYMENT_SUMMARY.md for complete guide!"
