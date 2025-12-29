# Data Structuring Sheet App - Setup Instructions

## 📋 Prerequisites

Before you begin, make sure you have the following installed on your computer:

- **Git** (to download the repository)
- **Python 3.8 or higher** (for the backend)
- **Node.js 16 or higher** (for the frontend)
- **npm** (comes with Node.js)

### How to Check if You Have These Installed:

**Windows:**
- Open PowerShell or Command Prompt
- Type: `python --version` (should show Python 3.x)
- Type: `node --version` (should show v16.x or higher)
- Type: `npm --version` (should show a version number)
- Type: `git --version` (should show a version number)

**Mac:**
- Open Terminal
- Type: `python3 --version` (should show Python 3.x)
- Type: `node --version` (should show v16.x or higher)
- Type: `npm --version` (should show a version number)
- Type: `git --version` (should show a version number)

**Linux:**
- Open Terminal
- Type: `python3 --version` (should show Python 3.x)
- Type: `node --version` (should show v16.x or higher)
- Type: `npm --version` (should show a version number)
- Type: `git --version` (should show a version number)

If any of these commands don't work, you'll need to install the missing software first.

---

## 📥 Step 1: Download the Repository

### Option A: Using Git (Recommended)

1. Open your terminal/command prompt in the location where you want to save the project
2. Run the following command:

```bash
git clone <repository-url>
```

3. Navigate into the project folder:

**Windows (PowerShell):**
```powershell
cd ai-sheet-automation
```

**Mac/Linux:**
```bash
cd ai-sheet-automation
```

### Option B: Download as ZIP

1. Download the repository as a ZIP file
2. Extract the ZIP file to your desired location
3. Open terminal/command prompt and navigate to the extracted folder:

**Windows (PowerShell):**
```powershell
cd path\to\ai-sheet-automation
```

**Mac/Linux:**
```bash
cd path/to/ai-sheet-automation
```

---

## 🔧 Step 2: Install Backend Dependencies

1. Navigate to the backend folder:

**Windows (PowerShell):**
```powershell
cd backend
```

**Mac/Linux:**
```bash
cd backend
```

2. Install Python dependencies:

**Windows:**
```powershell
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
pip3 install -r requirements.txt
```

> ⚠️ **Note:** If you get a "pip not found" error, try `pip3` instead of `pip` on Mac/Linux, or `python -m pip` on Windows.

---

## 🎨 Step 3: Install Frontend Dependencies

1. Open a **NEW** terminal/command prompt window (keep the backend one open)
2. Navigate to the frontend folder:

**Windows (PowerShell):**
```powershell
cd path\to\ai-sheet-automation\frontend
```

**Mac/Linux:**
```bash
cd path/to/ai-sheet-automation/frontend
```

3. Install Node.js dependencies:

**All Platforms:**
```bash
npm install
```

> ⏳ This may take a few minutes. Wait for it to complete.

---

## 🔐 Step 4: Configure Environment Variables

1. Navigate to the `backend` folder
2. Look for a file named `.env` (it might be hidden)
3. If the file doesn't exist, create a new file named `.env` (no extension, just `.env`)
4. Open the `.env` file in a text editor
5. Add the following content (ask your team lead for the actual values):

```env
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

> ⚠️ **Important:** 
> - Replace `your_openai_api_key_here` with your actual OpenAI API key
> - Replace `your_perplexity_api_key_here` with your actual Perplexity API key
> - Replace the entire `GOOGLE_SERVICE_ACCOUNT_JSON` value with your actual service account JSON (it should be all on one line, no line breaks)
> - Do NOT add quotes around the values
> - Do NOT share this file with anyone

---

## 🚀 Step 5: Start the Backend Server

1. Open a terminal/command prompt
2. Navigate to the backend folder:

**Windows (PowerShell):**
```powershell
cd path\to\ai-sheet-automation\backend
```

**Mac/Linux:**
```bash
cd path/to/ai-sheet-automation/backend
```

3. Start the backend server:

**Windows:**
```powershell
python run_server.py
```

**Mac/Linux:**
```bash
python3 run_server.py
```

4. You should see output like this:
```
INFO:     Uvicorn running on http://127.0.0.1:9000 (Press CTRL+C to quit)
INFO:     Started reloader process...
```

> ✅ **Success!** The backend is now running. **Keep this terminal window open.**

> 💡 **Tip:** The backend will automatically reload when you make changes to the code.

---

## 🎨 Step 6: Start the Frontend Server

1. Open a **NEW** terminal/command prompt window (keep the backend one open)
2. Navigate to the frontend folder:

**Windows (PowerShell):**
```powershell
cd path\to\ai-sheet-automation\frontend
```

**Mac/Linux:**
```bash
cd path/to/ai-sheet-automation/frontend
```

3. Start the frontend server:

**All Platforms:**
```bash
npm start
```

4. Your browser should automatically open to `http://localhost:4000`
5. If it doesn't open automatically, manually navigate to: `http://localhost:4000`

> ✅ **Success!** The frontend is now running. **Keep this terminal window open too.**

> 💡 **Tip:** The frontend will automatically reload when you make changes to the code.

---

## ✅ Step 7: Verify Everything is Working

1. **Backend Check:**
   - Open your browser
   - Go to: `http://localhost:9000`
   - You should see: `{"message": "AI Sheet Automation Backend is running"}`

2. **Frontend Check:**
   - The frontend should already be open at `http://localhost:4000`
   - You should see the "Data Structuring Sheet App" interface
   - You should see the "Usage Instructions" card

3. **Health Check:**
   - Go to: `http://localhost:9000/health`
   - You should see: `{"status": "ok", "message": "Backend is healthy"}`

---

## 🛑 How to Stop the Servers

When you're done working:

1. **Stop the Frontend:**
   - Go to the terminal window running the frontend
   - Press `Ctrl + C` (Windows/Linux) or `Cmd + C` (Mac)
   - Wait for it to stop

2. **Stop the Backend:**
   - Go to the terminal window running the backend
   - Press `Ctrl + C` (Windows/Linux) or `Cmd + C` (Mac)
   - Wait for it to stop

---

## 🔄 Daily Workflow

Once everything is set up, your daily workflow should be:

1. **Open two terminal windows:**
   - Terminal 1: Navigate to `backend` folder
   - Terminal 2: Navigate to `frontend` folder

2. **Start the backend:**
   - In Terminal 1, run: `python run_server.py` (Windows) or `python3 run_server.py` (Mac/Linux)

3. **Start the frontend:**
   - In Terminal 2, run: `npm start`

4. **Work on the application:**
   - Both servers will automatically reload when you make changes
   - The frontend will be available at `http://localhost:4000`
   - The backend will be available at `http://localhost:9000`

5. **When done:**
   - Press `Ctrl + C` (or `Cmd + C` on Mac) in both terminals to stop the servers

---

## ❓ Troubleshooting

### Backend won't start

**Error: "Module not found"**
- Solution: Make sure you installed dependencies with `pip install -r requirements.txt` (or `pip3` on Mac/Linux)

**Error: "Port 9000 already in use"**
- Solution: Another application is using port 9000. Close it or change the port in `run_server.py`

**Error: "OPENAI_API_KEY not found"**
- Solution: Make sure your `.env` file exists in the `backend` folder and has the correct API keys

### Frontend won't start

**Error: "Port 4000 already in use"**
- Solution: Another application is using port 4000. Close it or the system will ask if you want to use a different port

**Error: "Module not found"**
- Solution: Make sure you installed dependencies with `npm install` in the `frontend` folder

**Error: "npm: command not found"**
- Solution: Node.js is not installed. Install it from https://nodejs.org/

### Can't connect to backend from frontend

- Make sure the backend is running (check `http://localhost:9000`)
- Make sure you're using the correct URL (should be `http://localhost:9000`)
- Check the browser console for error messages (F12 → Console tab)

---

## 📝 Quick Reference Commands

### Backend Commands

**Navigate to backend:**
- Windows: `cd backend`
- Mac/Linux: `cd backend`

**Start backend:**
- Windows: `python run_server.py`
- Mac/Linux: `python3 run_server.py`

**Install dependencies:**
- Windows: `pip install -r requirements.txt`
- Mac/Linux: `pip3 install -r requirements.txt`

### Frontend Commands

**Navigate to frontend:**
- Windows: `cd frontend`
- Mac/Linux: `cd frontend`

**Start frontend:**
- All: `npm start`

**Install dependencies:**
- All: `npm install`

---

## 📞 Need Help?

If you encounter any issues:

1. Check the terminal output for error messages
2. Verify all prerequisites are installed
3. Make sure you're in the correct folders when running commands
4. Check that the `.env` file is properly configured
5. Contact your team lead with:
   - The error message you're seeing
   - What step you were on
   - Your operating system (Windows/Mac/Linux)

---

## ✅ Setup Checklist

Use this checklist to make sure you've completed everything:

- [ ] Git, Python, Node.js, and npm are installed
- [ ] Repository downloaded/cloned
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] `.env` file created in `backend` folder with API keys
- [ ] Backend server starts successfully (`python run_server.py`)
- [ ] Frontend server starts successfully (`npm start`)
- [ ] Backend accessible at `http://localhost:9000`
- [ ] Frontend accessible at `http://localhost:4000`
- [ ] Health check works (`http://localhost:9000/health`)

---

**🎉 Congratulations! You're all set up and ready to work on the Data Structuring Sheet App!**

