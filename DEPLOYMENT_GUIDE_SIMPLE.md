# 🚀 Simple Deployment Guide

Deploy your app to the cloud in just a few clicks! Your teammates won't need to install anything.

---

## 🎯 What We'll Do

1. **Backend** → Railway (free)
2. **Frontend** → Vercel (free)

Both connect to GitHub and auto-deploy when you push code!

---

## 📋 Step 1: Create Accounts (5 minutes)

1. **GitHub**: https://github.com (if you don't have one)
2. **Railway**: https://railway.app - Sign up with GitHub
3. **Vercel**: https://vercel.com - Sign up with GitHub

All free! ✅

---

## 🚂 Step 2: Deploy Backend to Railway (10 minutes)

### 2.1 Push Code to GitHub

1. Create a new repository on GitHub
2. Push your code:
   ```bash
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

### 2.2 Deploy on Railway

1. Go to https://railway.app
2. Click **"New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your repository
5. Railway will auto-detect Python ✅

### 2.3 Configure Settings

1. Click on your service
2. Go to **"Settings"** tab
3. Set **Root Directory** to: `backend`
4. Set **Start Command** to: `python railway_start.py`

### 2.4 Add Environment Variables

1. Go to **"Variables"** tab
2. Click **"New Variable"**
3. Add these three variables:

   **Variable 1:**
   - Name: `OPENAI_API_KEY`
   - Value: `your_openai_key_here`

   **Variable 2:**
   - Name: `PERPLEXITY_API_KEY`
   - Value: `your_perplexity_key_here`

   **Variable 3:**
   - Name: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Value: `{"type":"service_account",...}` (paste your full JSON here, all on one line)

4. Click **"Deploy"**

### 2.5 Get Backend URL

1. Once deployed, go to **"Settings"** tab
2. Under **"Domains"**, click **"Generate Domain"**
3. Copy the URL (looks like: `https://your-app-name.up.railway.app`)
4. **Save this URL** - you'll need it next!

---

## ⚡ Step 3: Deploy Frontend to Vercel (10 minutes)

### 3.1 Deploy on Vercel

1. Go to https://vercel.com
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Vercel will auto-detect React ✅

### 3.2 Configure Settings

1. **Root Directory**: Set to `frontend`
2. **Build Command**: `npm run build` (auto-filled)
3. **Output Directory**: `build` (auto-filled)

### 3.3 Add Environment Variable

1. Scroll down to **"Environment Variables"**
2. Click **"Add"**
3. Add:
   - **Name**: `REACT_APP_API_BASE`
   - **Value**: `https://your-railway-url.up.railway.app` (paste the Railway URL from Step 2.5)
4. Click **"Deploy"**

### 3.4 Get Frontend URL

1. Wait for deployment (2-3 minutes)
2. Vercel will give you a URL like: `https://your-app-name.vercel.app`
3. **This is your app!** 🎉
4. Share this URL with your teammates

---

## ✅ Done!

Your app is now live! Your teammates can:
- Just open the Vercel URL in their browser
- No installation needed
- No setup needed
- It just works! ✨

---

## 🔄 Making Updates

When you make changes:

1. Push code to GitHub: `git push`
2. Railway and Vercel auto-deploy (takes 2-3 minutes)
3. Your teammates see updates automatically!

---

## 💰 Cost

- **Railway**: Free tier = $5/month credit (enough for small apps)
- **Vercel**: Free tier is very generous
- **Total**: $0/month! 🎉

---

## 🆘 Troubleshooting

### Backend not working?
- Check Railway logs: Click on your service → "Deployments" → View logs
- Make sure environment variables are set correctly
- Check that Root Directory is set to `backend`

### Frontend can't connect to backend?
- Make sure `REACT_APP_API_BASE` in Vercel matches your Railway URL
- Make sure Railway domain is generated and active
- Check browser console (F12) for errors

### Need help?
- Railway docs: https://docs.railway.app
- Vercel docs: https://vercel.com/docs
- Both have great support!

---

## 📝 Quick Checklist

- [ ] GitHub account created
- [ ] Code pushed to GitHub
- [ ] Railway account created
- [ ] Backend deployed to Railway
- [ ] Environment variables added to Railway
- [ ] Railway URL copied
- [ ] Vercel account created
- [ ] Frontend deployed to Vercel
- [ ] `REACT_APP_API_BASE` set in Vercel
- [ ] Frontend URL working! 🎉

---

**That's it! Your app is now in the cloud and ready to share!** 🚀

