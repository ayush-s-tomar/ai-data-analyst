# 🤖 AI Data Analyst Agent
Upload any CSV → Ask questions in plain English → Get instant charts & insights.

**Powered by Groq (free) + llama-3.3-70b**

---

## 🔑 Get a FREE Groq API Key
1. Go to https://console.groq.com
2. Sign up (free, no credit card needed)
3. Go to API Keys → Create API Key
4. Copy it — you'll need it below

---

## 🚀 Local Setup (Windows)

### Step 1 — Extract ZIP
Extract `ai-data-analyst.zip` anywhere, then open that folder in VS Code.

### Step 2 — Backend (run each line separately in PowerShell terminal)
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
Now open `.env` and change it to:
```
GROQ_API_KEY=gsk_your_key_here
```
Then start the server:
```powershell
uvicorn main:app --reload --port 8000
```
✅ Backend running at http://localhost:8000

### Step 3 — Frontend (open a NEW terminal tab)
```powershell
cd frontend
npm install
npm start
```
✅ App running at http://localhost:3000

---

## ☁️ Deploy FREE to Production

### Backend → Render.com
1. Push to GitHub
2. Render.com → New Web Service → connect repo
3. Root dir: `backend`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Environment variable: `GROQ_API_KEY` = your key
7. Deploy → copy your URL (e.g. `https://ai-data-analyst.onrender.com`)

### Frontend → Vercel
1. Vercel.com → New Project → connect same repo
2. Root dir: `frontend`
3. Environment variable: `REACT_APP_API_URL` = your Render URL
4. Deploy

---

## 💡 Example Questions
- "Show me a bar chart of sales by region"
- "What's the profit trend over time?"
- "Which product performs best?"
- "Compare customer segments by revenue"
