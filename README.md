<div align="center">

# 🤖 AI Data Analyst

**Upload any CSV. Ask questions in plain English. Get instant charts & insights.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Visit_App-6366f1?style=for-the-badge&logo=vercel&logoColor=white)](https://ai-data-analyst-six-sooty.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://ai-data-analyst-fdcx.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Powered by Groq](https://img.shields.io/badge/Powered_by-Groq_%2B_Llama_3.3_70B-f97316?style=for-the-badge)](https://console.groq.com)

</div>

---

## 📸 Demo

![AI Data Analyst — Sales Rep Performance Heatmap](demo.png)

> *Asking "Show me the sales rep performance heatmap by region" generates an interactive heatmap instantly — no code required.*

---

## ✨ Features

| Feature | Description |
|---|---|
| 📁 **Drag-and-drop CSV upload** | No setup — just drop your file and start asking |
| 💬 **Natural language queries** | Ask questions the way you'd ask a colleague |
| 📊 **Auto-generated charts** | Bar, line, scatter, heatmap, and more |
| 🧠 **Session memory** | Follow-up questions build on previous answers |
| ⚡ **Fast inference** | Powered by Groq's free Llama 3.3 70B |
| 🆓 **100% free to run** | No paid API keys required |

---

## 🌐 Live Links

| Service | URL |
|---|---|
| Frontend | [ai-data-analyst-six-sooty.vercel.app](https://ai-data-analyst-six-sooty.vercel.app) |
| Backend API | [ai-data-analyst-fdcx.onrender.com](https://ai-data-analyst-fdcx.onrender.com) |

> ⏳ **Note:** The backend runs on Render's free tier and may take **30–60 seconds to wake up** after a period of inactivity.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React |
| **Backend** | FastAPI, Python |
| **AI Model** | Groq API — Llama 3.3 70B |
| **Data Processing** | pandas, matplotlib |
| **Hosting** | Vercel (frontend) · Render (backend) |

---

## 🚀 Local Setup (Windows)

### Prerequisites

Get a **free** Groq API key — no credit card needed:

1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **API Keys → Create API Key**
3. Copy it — you'll need it in Step 2

---

### Step 1 — Extract & Open

Extract `ai-data-analyst.zip` anywhere, then open that folder in VS Code.

---

### Step 2 — Backend

Open a PowerShell terminal and run each line separately:

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set your key:

```env
GROQ_API_KEY=gsk_your_key_here
```

Start the server:

```powershell
uvicorn main:app --reload --port 8000
```

✅ Backend running at **http://localhost:8000**

---

### Step 3 — Frontend

Open a **new terminal tab** and run:

```powershell
cd frontend
npm install
npm start
```

✅ App running at **http://localhost:3000**

---

## ☁️ Free Production Deployment

### Backend → [Render.com](https://render.com)

1. Push your project to GitHub
2. Render → **New Web Service** → connect your repo
3. Set **Root Directory** to `backend`
4. **Build command:** `pip install -r requirements.txt`
5. **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `GROQ_API_KEY` = your key
7. Deploy → copy your URL (e.g. `https://your-app.onrender.com`)

### Frontend → [Vercel.com](https://vercel.com)

1. Vercel → **New Project** → connect the same repo
2. Set **Root Directory** to `frontend`
3. Add environment variable: `REACT_APP_API_URL` = your Render URL
4. Deploy

---

## 📂 Project Structure

```
ai-data-analyst/
├── backend/
│   ├── main.py               # FastAPI app & Groq integration
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   └── App.css
│   └── package.json
└── render.yaml               # Render deployment config
```

---

## 💡 Example Prompts

Try asking things like:

- *"Show me a bar chart of sales by region"*
- *"What's the revenue trend over time?"*
- *"Which product performs best by units sold?"*
- *"Compare customer ratings across segments"*
- *"Show me the sales rep performance heatmap by region"*

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and deploy.
