# Auto-Task-Generator 🤖📋

An intelligent autonomous AI agent that automatically reads emails from Gmail, filters out newsletters/spam, extracts actionable tasks, plans step-by-step workflows, and runs executions with minimal human intervention.

Developed with a premium, highly responsive **Bento-Grid Dashboard** in React and a robust **FastAPI backend** running local LLMs securely.

---

## 🎯 Project Overview
The **Auto-Task-Generator** streamlines workspace productivity by automatically converting unstructured communication into actionable tasks. Utilizing a state-of-the-art **ReAct (Reasoning + Acting) agent pattern** powered by local Large Language Models (via Ollama), it reads emails, negotiates priority, assigns due dates, categorizes tags, plans execution paths, and updates task statuses.

---

## ✨ Features
- **Google OAuth 2.0 Integration:** Secure login and persistent token storage inside SQLite database.
- **AI Task Extraction:** Automatically parses subjects, bodies, and senders into validated structured database schemas.
- **Smart Newsletter Filter:** Multi-factor heuristics to completely skip Category Promotions/Social updates and unsubscribe mailers.
- **ReAct Workflow Planning:** Local LLMs plan precise workflow execution steps, tools needed, time estimations, and risks.
- **Bento-Grid Dashboard:** Interactive dark/light accent layout displaying real-time metrics, filtered email items, priority flow, and extraction controls.
- **Local Privacy First:** No user data leaves your machine; LLM inference is run entirely on local CPUs/GPUs.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, SQLAlchemy, SQLite, Pydantic (v2), Uvicorn
- **AI/LLM Engine:** Ollama (defaulting to `llama3.2:1b` or `mistral`)
- **Frontend:** React, Vite, Vanilla CSS (Glassmorphism & Bento Design)
- **Integration:** Google Gmail API Client, Google Auth OAuthlib

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.11 / 3.12**
- **Node.js (v18+) & npm**
- **Ollama** installed locally ([ollama.com/download](https://ollama.com/download))

### 1. Clone & Set Up Backend
```bash
git clone https://github.com/prakharshrestha/Auto-Task-Generator.git
cd Auto-Task-Generator

# Create virtual environment
python -m venv venv
# Activate on Windows:
.\venv\Scripts\activate
# Activate on macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` in both the root folder and the `backend` folder:
```bash
copy .env.example .env
copy .env.example backend/.env
```
Fill in the following Google OAuth credentials in your `.env`:
```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```
*Note: Make sure your email is added as a **Test User** in Google Cloud OAuth Consent Screen if your project is in Testing mode.*

### 3. Initialize Ollama Model
```bash
# Start Ollama service (runs on port 11434)
ollama serve

# Pull your model of choice
ollama pull llama3.2:1b
# or
ollama pull mistral
```

---

## ⚙️ Running the Application

### Start the FastAPI Backend
Ensure your virtual environment is active, then run:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs)
- Google Login: [http://localhost:8000/auth/google/login](http://localhost:8000/auth/google/login)

### Start the Frontend Dev Server
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📁 Project Structure
```
Auto-Task-Generator/
├── backend/
│   ├── config.py              # Configuration & Environment loading
│   ├── main.py                # FastAPI entry point
│   └── app/
│       ├── database.py        # SQLite Engine & SQLAlchemy Session
│       ├── agents/            # ReAct autonomous TaskAgent logic
│       ├── models/            # SQLAlchemy (DBTask) & Pydantic models
│       ├── routes/            # routers (auth, gmail, health, tasks)
│       ├── services/          # Services (gmail, oauth, llm, workflow)
│       └── utils/             # Prompts & system templates
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React Bento Dashboard component
│   │   ├── api.js             # API communications module
│   │   └── index.css          # Premium design variables
│   └── package.json           # Frontend dependencies
├── PROJECT_DOCUMENTATION.md   # Comprehensive Developer Documentation
└── README.md                  # This file
```

---

## 🤝 Contribution Steps
1. Fork the repository and create your feature branch: `git checkout -b feature/AmazingFeature`
2. Keep PEP 8 formatting and maintain docstrings.
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request.

---

## 👥 Authors & Contributors
- **Prakhar Kle** - Primary architect, lead developer, and repository maintainer.

---

*For detailed explanations, architectural patterns, and API descriptions, refer to the [PROJECT_DOCUMENTATION.md](file:///e:/devops_proj/Auto-Task-Generator/PROJECT_DOCUMENTATION.md) file.*
