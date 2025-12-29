# Simple Deployment Guide - Data Structuring Sheet App

This guide will help you deploy the app to the cloud so your teammates can use it without any local setup! 🚀

We'll use:
- **Railway** for the backend (free tier available)
- **Vercel** for the frontend (free tier available)

Both are very easy to use and connect directly to GitHub.

---

## 📋 Prerequisites

1. A **GitHub account** (free)
2. A **Railway account** (free) - Sign up at https://railway.app
3. A **Vercel account** (free) - Sign up at https://vercel.com

---

## 🚂 Part 1: Deploy Backend to Railway

### Step 1: Push Your Code to GitHub

1. Create a new repository on GitHub (if you haven't already)
2. Push your code to GitHub

### Step 2: Deploy to Railway

1. Go to https://railway.app and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Select your repository
5. Railway will automatically detect it's a Python project
6. Click **"Add Service"** → **"GitHub Repo"**
7. Select your repository again

### Step 3: Configure Environment Variables

1. In Railway, click on your service
2. Go to the **"Variables"** tab
3. Add these environment variables:

```
OPENAI_API_KEY=your_openai_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

4. Click **"Deploy"**

### Step 4: Get Your Backend URL

1. Once deployed, Railway will give you a URL like: `https://your-app-name.up.railway.app`
2. Copy this URL - you'll need it for the frontend

---

## ⚡ Part 2: Deploy Frontend to Vercel

### Step 1: Prepare Frontend for Deployment

1. Make sure your frontend code is pushed to GitHub

### Step 2: Deploy to Vercel

1. Go to https://vercel.com and sign in
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Vercel will auto-detect it's a React app
5. In **"Environment Variables"**, add:

```
REACT_APP_API_BASE=https://your-railway-url.up.railway.app
```

(Replace with your actual Railway URL from Part 1)

6. Click **"Deploy"**

### Step 3: Get Your Frontend URL

1. Vercel will give you a URL like: `https://your-app-name.vercel.app`
2. This is your app! Share this URL with your teammates

---

## ✅ That's It!

Your teammates can now access the app at the Vercel URL - no setup needed!

---

## 🔄 Updating the App

Whenever you make changes:

1. Push your code to GitHub
2. Railway and Vercel will automatically redeploy
3. Your teammates will see the updates in a few minutes

---

## 💰 Cost

- **Railway**: Free tier includes $5/month credit (usually enough for small apps)
- **Vercel**: Free tier is very generous for frontend hosting
- **Total**: $0/month for small teams! 🎉

---

## 📝 Notes

- The backend URL from Railway might change if you're on the free tier
- If it changes, update the `REACT_APP_API_BASE` variable in Vercel
- Both platforms have great documentation if you need help

---

**Need help?** Both Railway and Vercel have excellent support and documentation!

