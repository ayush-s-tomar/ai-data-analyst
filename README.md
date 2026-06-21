# 🤖 AI Data Analyst Agent

[![Live Frontend](https://img.shields.io/badge/demo-vercel-black)](https://ai-data-analyst-six-sooty.vercel.app)
[![Backend](https://img.shields.io/badge/backend-render-46E3B7)](https://ai-data-analyst-fdcx.onrender.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Upload any CSV → Ask questions in plain English → Get instant charts & insights.

**Powered by Groq (free) + Llama 3.3 70B**

---

## 🌐 Live Demo

- **App:** [ai-data-analyst-six-sooty.vercel.app](https://ai-data-analyst-six-sooty.vercel.app)
- **API:** [ai-data-analyst-fdcx.onrender.com](https://ai-data-analyst-fdcx.onrender.com)

> ⏳ Note: the backend is on Render's free tier and may take 30–60s to wake up after inactivity.

---

## ✨ Features

- 📁 Drag-and-drop CSV upload
- 💬 Ask data questions in natural language
- 📊 Auto-generated charts (bar, line, scatter)
- ⚡ Fast inference via Groq's free Llama 3.3 70B
- 🆓 100% free to run and deploy — no paid API keys required

---

## 🛠️ Tech Stack

| Layer    | Tech                          |
|----------|--------------------------------|
| Frontend | React                          |
| Backend  | FastAPI, Python                |
| AI       | Groq API (Llama 3.3 70B)       |
| Data     | pandas, matplotlib             |
| Hosting  | Vercel (frontend), Render (backend) |

---

## 🔑 Get a FREE Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free, no credit card needed)
3. Go to **API Keys** → **Create API Key**
4. Copy it — you'll need it below

---

## 🚀 Local Setup (Windows)

### Step 1 — Extract ZIP
Extract `ai-data-analyst.zip` anywhere, then open that folder in VS Code.

### Step 2 — Backend
*(run each line separately in a PowerShell terminal)*

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set:

GROQ_API_KEY=gsk_your_key_here

Then start the server:

```powershell
uvicorn main:app --reload --port 8000
```

✅ Backend running at http://localhost:8000

### Step 3 — Frontend
*(open a NEW terminal tab)*

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

## 📂 Project Structure
ai-data-analyst/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
└── render.yaml

---

## 💡 Example Questions

- "Show me a bar chart of sales by region"
- "What's the profit trend over time?"
- "Which product performs best?"
- "Compare customer segments by revenue"

---

## 📄 License

MIT — free to use, modify, and deploy.

