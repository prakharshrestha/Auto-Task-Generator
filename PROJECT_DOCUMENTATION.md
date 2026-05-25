# Auto-Task-Generator: Developer & Architecture Documentation

Welcome to the comprehensive developer documentation for the **Auto-Task-Generator**. This document provides an in-depth view of the system's architecture, data flows, components, configuration, database schemas, and codebase to enable seamless extension and production deployment.

---

## 🎯 1. Project Overview
The **Auto-Task-Generator** is an autonomous AI agent system designed to bridge the gap between unstructured communication (specifically emails) and structured task management. Leveraging a local Large Language Model (LLM) and a modern FastAPI + React stack, the system reads incoming emails, intelligently filters out spam and newsletters, extracts actionable work items, proposes execution plans, and manages the lifecycle of generated tasks. 

Unlike traditional trigger-action automation tools (e.g., Zapier or rule-based parsers), this application utilizes an **agentic ReAct (Reasoning + Acting) pattern** to interpret context, negotiate priority levels, normalize metadata (such as deadlines), and structure workflows dynamically.

---

## ⚠️ 2. Problem Statement
Modern professionals are inundated with emails, many of which contain implicit or explicit actions ("Please review this proposal by Thursday", "Can you send the updated deck?"). Manual parsing of these emails is:
1. **Time-consuming & Error-prone:** Actions get lost in long message threads.
2. **Contextually Isolated:** Tasks live in the inbox, separated from official project management systems.
3. **Inelastic to Automation:** Standard rule-based automation engines fail when the wording, formatting, or sender of the request changes.

Traditional tools cannot understand the *urgency*, *sub-steps*, or *implicit assignees* embedded within natural language text without rigid, brittle templates.

---

## 🎯 3. Project Purpose
The **Auto-Task-Generator** was created to democratize AI-driven autonomous productivity:
- To automate the parsing of emails into concrete, trackable, and prioritized tasks.
- To execute semantic reasoning via local, privacy-respecting LLMs (via Ollama), ensuring sensitive corporate data never leaves the developer's workstation.
- To build a highly responsive, modern dashboard utilizing clean design principles to orchestrate this flow visually.

---

## ✨ 4. Key Features
- **Secure Google OAuth 2.0 Integration:** Facilitates one-click user sign-in and obtains offline refresh tokens. Credentials and session tokens are securely persisted in SQLite.
- **AI-Powered Task Extraction:** Harnesses local LLMs (e.g., Llama 3.2, Mistral) to extract task descriptions, due dates, categories, priority scores, and assignees directly from email text.
- **Intelligent Spam & Newsletter Filtering:** Uses advanced multi-factor heuristics (sender patterns, Gmail labels, body structure, and unsubscribe tags) to isolate promotional and social mail, preserving LLM bandwidth for genuine requests.
- **ReAct planning & Workflow Service:** Evaluates tasks to draft multi-step plans detailing required tools, parameters, expected outputs, estimated duration, and operational risks.
- **Interactive Bento-Grid Dashboard:** Designed with premium aesthetics, presenting overall task statistics, real-time filtered mail grids, priority tracking distributions, and direct triggers for manual extraction.
- **Keyword Vector-Memory Simulation:** Employs localized keyword search within SQLite as a robust MVP fallback for embedding-based task memory retrieval.

---

## 🛠️ 5. Technologies Used

### Backend Stack
- **Core Framework:** Python 3.11 / 3.12, FastAPI
- **Server Engine:** Uvicorn (ASGI web server)
- **Database ORM:** SQLAlchemy
- **Schema Validation:** Pydantic & Pydantic Settings
- **Google Integration:** Google API Python Client, Google Auth OAuthlib
- **HTTP Client:** Requests

### Local AI Infrastructure
- **LLM Engine:** Ollama (serving local models)
- **Default Models:** `llama3.2:1b` (configured by default for lightning-fast local inference), `mistral`, or `llama2`

### Frontend Stack
- **Build System:** Vite
- **UI Framework:** React (Functional Components, Hooks)
- **Styling:** Vanilla CSS (Tailored Bento-grid design, custom HSL palettes, transitions, and dark modes)

---

## 🏗️ 6. Architecture & System Design

The system implements a decoupled client-server architecture. The frontend acts as an orchestration panel, making granular asynchronous requests to the FastAPI backend, which handles database management, Gmail interactions, and Ollama reasoning.

### Component Architecture Diagram

```mermaid
graph TD
    subgraph Frontend [React Single Page App]
        UI[App.jsx - Bento UI]
        API_Client[api.js - fetch wrapper]
    end

    subgraph Backend [FastAPI Application]
        Router[main.py & Router Layer]
        Agent[TaskAgent - ReAct core]
        
        subgraph Services [Service Layer]
            GmailOAuth[GmailOAuthService]
            Gmail[GmailService]
            LLM[LLMService - Ollama API]
            Workflow[WorkflowService]
        end
        
        subgraph Database [Storage Layer]
            SQL[SQLAlchemy - SQLite]
            TokensTable[(gmail_tokens)]
            TasksTable[(tasks)]
        end
    end

    subgraph External [External Services]
        GAPI[Google API OAuth & Gmail]
        OLLAMA[Local Ollama Server:11434]
    end

    UI --> API_Client
    API_Client --> Router
    Router --> Agent
    
    Agent --> GmailOAuth
    Agent --> Gmail
    Agent --> LLM
    Agent --> Workflow
    
    GmailOAuth --> SQL
    Gmail --> GAPI
    GmailOAuth --> GAPI
    LLM --> OLLAMA
    
    SQL --> TasksTable
    SQL --> TokensTable
```

---

## 🔄 7. Workflow & Operations
The high-level lifecycle of an email turning into a reasoned task follows these steps:

1. **Authentication:**
   - The user visits `/auth/google/login` which initiates the Google OAuth 2.0 flow.
   - Upon consent, Google redirects the browser to `/auth/google/callback` with an auth `code`.
   - The `GmailOAuthService` exchanges this code for access/refresh tokens, grabs the user's email, and saves or updates the record in the `gmail_tokens` SQLite table.

2. **Ingestion & Filtering:**
   - The React client loads and sends a request to `/api/gmail/recent-plans?mode=raw`.
   - The `GmailService` pulls the latest 10 messages from the authenticated inbox.
   - The backend runs `_is_promotional_or_newsletter()` heuristics on each message. Newsletters and promotional emails are skipped.

3. **Asynchronous Task Extraction:**
   - The React UI receives the filtered emails list.
   - For each valid email, the client triggers a POST request to `/api/tasks/extract`.
   - The `TaskAgent` requests the `LLMService` to extract tasks using a structured prompt template.
   - The LLM parses the text and responds with a JSON payload of actionable items.
   - Pydantic models validate and normalize this data, inserting new entries into the `tasks` SQLite table via SQLAlchemy.

4. **Reasoning & Planning:**
   - When required, the agent calls `/api/tasks/{task_id}/reason`.
   - The `LLMService` formulates workflow steps (actions, tools, expected outputs) for the task.
   - The `WorkflowService` converts these steps into a structured `Workflow` object stored in local memory, ready for execution.

---

## ⚡ 8. Execution Flow
Below is the sequence of function calls during a task extraction request:

```mermaid
sequenceDiagram
    autonumber
    participant React as Frontend Dashboard
    participant Fast as FastAPI Router (gmail.py)
    participant Agent as TaskAgent (task_agent.py)
    participant LLM as LLMService (llm_service.py)
    participant Ollama as Ollama API
    participant DB as SQLite Database
    
    React->>Fast: POST /api/tasks/extract (email details)
    Fast->>Agent: process_email(subject, body, sender)
    Agent->>Agent: _think_about_email() logs analysis
    Agent->>LLM: extract_tasks(subject, body, sender)
    LLM->>Ollama: POST /api/chat (num_predict=800, JSON format)
    Ollama-->>LLM: JSON text response
    LLM->>LLM: _extract_json() sanitizes response
    LLM-->>Agent: Returns dict {"tasks": [...], "summary": "..."}
    
    loop Each Extracted Task
        Agent->>DB: Instantiates & inserts DBTask
    end
    
    Agent-->>Fast: Returns success & task structures
    Fast-->>React: 200 OK (Updates dashboard UI)
```

---

## 📁 9. Folder Structure
The repository is laid out systematically, splitting concerns between backend logic, persistent models, database management, services, and frontend presentation.

```
Auto-Task-Generator/
├── .env.example                 # Template for configuration secrets
├── .gitignore                   # Standard Git ignore file
├── requirements.txt             # Backend python dependency manifest
├── Project Handoff...           # Initial handoff instructions
├── README.md                    # Quick start documentation
├── PROJECT_DOCUMENTATION.md     # In-depth architectural documentation
│
├── backend/
│   ├── main.py                  # Application entry point, CORS, startup logic
│   ├── config.py                # Pydantic Settings environment configuration
│   └── app/
│       ├── __init__.py
│       ├── database.py          # SQLAlchemy engine, session maker, get_db dependency
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   └── task_agent.py    # Core Agent logic (extraction, planning, CRUD)
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── db_models.py     # SQLAlchemy DB schemas (DBTask)
│       │   └── task.py          # Pydantic validation schemas (TaskCreate, TaskUpdate)
│       │
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py          # Google OAuth endpoints
│       │   ├── gmail.py         # Gmail recent email fetch & plan endpoints
│       │   ├── health.py        # Service health checks
│       │   └── tasks.py         # Task database operations, extract, reason, execute
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── email_service.py # Generic mock helper for future expansions
│       │   ├── gmail_oauth_service.py # Token retrieval, database tokens writer
│       │   ├── gmail_service.py # Core Gmail API integrations (messages puller)
│       │   ├── llm_service.py   # Ollama chat wrapper, prompt parser, JSON cleaner
│       │   └── workflow_service.py # LangGraph-extendable stateful workflow engine
│       │
│       └── utils/
│           ├── __init__.py
│           └── prompts.py       # Centrally-managed LLM system and user prompt templates
│
└── frontend/
    ├── index.html               # Main entry HTML template
    ├── vite.config.js           # Vite server configuration
    ├── package.json             # Node dependencies and scripts
    ├── public/                  # Static assets
    └── src/
        ├── main.jsx             # React initialization
        ├── api.js               # API service integration module
        ├── index.css            # Base design variables and typography setup
        ├── App.css              # Frontend layout styling sheets
        └── App.jsx              # Main Single-Page Bento UI Dashboard
```

---

## 📦 10. Dependencies
The backend requires a few specialized packages to handle asynchronous endpoints, settings modeling, database management, and Google APIs.

### `requirements.txt` Highlight:
- `fastapi`: High-performance ASGI framework.
- `uvicorn[standard]`: Production-ready ASGI server.
- `pydantic`: Data validation using python type annotations.
- `pydantic-settings`: Dynamic settings management loaded from environment files.
- `sqlalchemy`: SQL Toolkit and Object Relational Mapper.
- `google-api-python-client` & `google-auth-oauthlib`: Safe integration with Gmail and OAuth flow.
- `requests`: Sync HTTP library for Ollama communication.

---

## 🚀 11. Installation Steps
Follow these instructions to run the Auto-Task-Generator locally:

### Prerequisites:
1. **Python 3.11 or 3.12** installed on your system.
2. **Git** for cloning.
3. **Node.js** (v18+) and **npm** for running the frontend.
4. **Ollama** installed locally.

### Step 1: Clone the Repository
```bash
git clone https://github.com/prakharshrestha/Auto-Task-Generator.git
cd Auto-Task-Generator
```

### Step 2: Set Up Python Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install Node Modules (Frontend)
```bash
cd frontend
npm install
cd ..
```

### Step 5: Install & Pull Ollama Models
1. Download Ollama from [Ollama.com](https://ollama.com/download).
2. Start the Ollama daemon:
   ```bash
   ollama serve
   ```
3. Pull the required model (we recommend `llama3.2:1b` for faster CPU testing or `mistral` for deeper accuracy):
   ```bash
   ollama pull llama3.2:1b
   # or
   ollama pull mistral
   ```

---

## ⚙️ 12. Setup Instructions

### Environment Variables Configuration
Copy the template environment file into a real `.env` file at both the root folder and inside the `backend` folder:
```bash
copy .env.example .env
copy .env.example backend/.env
```

Open the newly created `.env` file and populate it with your Google credentials:
```env
# FastAPI Configuration
ENVIRONMENT=development
API_PORT=8000
API_HOST=0.0.0.0

# Ollama LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Database Configuration
DATABASE_URL=sqlite:///./app.db
```

> [!IMPORTANT]
> **Google Cloud Setup Note:**
> Make sure your Google Cloud OAuth app is in **Testing** mode and that you have added your target email as a **Test User** in the Google Cloud Console → OAuth Consent Screen. If this is skipped, logging in will result in an unauthenticated developer block.

---

## 🌐 13. Environment Variables Overview

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Dictates verbose debug output in error trace logs. |
| `API_PORT` | `8000` | The port the FastAPI application runs on. |
| `API_HOST` | `0.0.0.0` | Binding interface for Uvicorn (allows network access). |
| `OLLAMA_BASE_URL`| `http://localhost:11434`| The local address hosting the active Ollama instance. |
| `OLLAMA_MODEL` | `llama3.2:1b` | The model name loaded by Ollama for task processing. |
| `GOOGLE_CLIENT_ID`| *Required* | OAuth Client ID generated on Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET`| *Required* | OAuth Secret generated on Google Cloud Console. |
| `GOOGLE_REDIRECT_URI`| `http://localhost:8000/...` | Authorized Redirect URI mapping exactly to the backend. |
| `DATABASE_URL` | `sqlite:///./app.db` | Target SQLAlchemy connection string for SQLite. |

---

## 🔌 14. API Usage & Specifications

The FastAPI application provides interactive swagger documentation at `http://localhost:8000/docs`.

### Health & Meta Endpoints
- **GET `/api/health`**
  - **Description:** Verifies service availability and loads build statistics.
  - **Response (200 OK):**
    ```json
    {
      "status": "healthy",
      "timestamp": "2026-05-24T18:41:55Z",
      "service": "Autonomous AI Agent API",
      "version": "1.0.0"
    }
    ```

### OAuth Endpoints
- **GET `/auth/google/login`**
  - **Description:** Generates Google authentication consent URL and redirects the browser.
- **GET `/auth/google/callback`**
  - **Description:** Consumes the OAuth callback authentication query code, exchanges it, and stores credentials.

### Gmail Operations
- **GET `/api/gmail/recent`**
  - **Description:** Fetches raw unread emails.
- **GET `/api/gmail/recent-plans`**
  - **Parameters:** `limit` (int, default=8), `mode` (string: `raw`, `extract`, `plan`)
  - **Description:** Fetches recent emails, filters spam heuristics, and dynamically runs the AI agent relative to selected `mode`.

### Task Operations
- **GET `/api/tasks/`**
  - **Description:** Lists all saved tasks in SQLite database. Supports pagination via `skip` and `limit`.
- **POST `/api/tasks/`**
  - **Description:** Manually creates a new task in the database.
  - **Request Body (JSON):**
    ```json
    {
      "title": "Review project proposal",
      "description": "Review the Q2 project proposal from marketing",
      "priority": "high",
      "due_date": "2026-05-01T00:00:00",
      "assigned_to": "john@example.com",
      "tags": ["project", "review"]
    }
    ```
- **POST `/api/tasks/extract`**
  - **Description:** Extracts structured tasks from raw text.
  - **Request Body (JSON):**
    ```json
    {
      "email_subject": "Feedback needed ASAP",
      "email_body": "Hey, I need you to double check the budget figures and let me know by Friday.",
      "sender": "lead@company.com"
    }
    ```
- **POST `/api/tasks/{task_id}/reason`**
  - **Description:** Runs ReAct workflow planning for a specific task using the local LLM.
- **POST `/api/tasks/{task_id}/execute`**
  - **Description:** Triggers simulated execution of a plan's sub-steps and updates database states.

---

## 🗄️ 15. Database Structure & Schema
The application uses SQLite (`app.db`) for lightweight local persistence.

### 1. `gmail_tokens` (Direct SQLite Manipulation)
Stores the access credentials of authenticated users.
- `email` (TEXT, Primary Key)
- `refresh_token` (TEXT)
- `access_token` (TEXT)
- `token_uri` (TEXT)
- `client_id` (TEXT)
- `client_secret` (TEXT)
- `scopes` (TEXT - JSON formatted string)
- `expiry` (TEXT - ISO format timestamp)

### 2. `tasks` (Managed via SQLAlchemy)
Stores the extracted and manually created tasks.
- `id` (VARCHAR, Primary Key)
- `title` (VARCHAR, Not Null)
- `description` (TEXT, Not Null)
- `priority` (VARCHAR, Default 'medium')
- `status` (VARCHAR, Default 'pending')
- `due_date` (DATETIME, Nullable)
- `assigned_to` (VARCHAR, Nullable)
- `tags_json` (TEXT, Default '[]') - Stores categorization tags as a stringified list.
- `source_email` (VARCHAR, Nullable)
- `extracted_from` (TEXT, Nullable)
- `created_at` (DATETIME, Default UTC Now)
- `updated_at` (DATETIME, Default UTC Now, Auto-update on modification)
- `completed_at` (DATETIME, Nullable)

---

## 📝 16. Code Explanation

### 1. Core Entrypoint (`backend/main.py`)
Responsible for configuring CORS policies (allowing connections from `localhost:3000` / `localhost:8000`), configuring global logging to both console and file handlers (`./logs/app.log`), and initializing database tables on startup event:
```python
Base.metadata.create_all(bind=engine)
```

### 2. The Task Agent (`backend/app/agents/task_agent.py`)
Acts as the central orchestrator:
- `process_email()` calls `LLMService` to extract tasks, validates payloads via `TaskCreate` Pydantic model, and saves objects to the database using SQLite sessions.
- `reason_and_plan_task()` queries the task details, feeds them to the LLM to get a sequential step-by-step workflow plan, and generates structured `WorkflowStep` objects using the `WorkflowService`.

### 3. LLM Service (`backend/app/services/llm_service.py`)
Wraps raw HTTP calls to the local Ollama backend via `/api/chat`. Sets `num_predict=800` to avoid huge generation times, restricts output strictly to JSON schemas, and cleans output formatting via regular expressions:
```python
def _extract_json(self, text: str) -> str:
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    ...
```

### 4. Interactive Bento Dashboard (`frontend/src/App.jsx`)
Features a modern dashboard splitting state management:
- Loads cached hidden items from `localStorage`.
- Instantly fetches raw email headers on user click using `api.getRawRecentEmails` to keep the UI extremely snappy.
- Fires asynchronous, parallel `api.extractTasksForEmail` requests for each email in the background, updating task badges seamlessly as local inference completes.

---

## 🚢 17. Production Deployment Process
To deploy this system into a multi-user staging or production server:

### Backend Deployment:
1. **WSGI/ASGI Server:** Use Gunicorn with Uvicorn worker threads to spawn multiple processes:
   ```bash
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```
2. **Reverse Proxy:** Set up **Nginx** in front of Gunicorn to handle SSL termination, redirect HTTP traffic to HTTPS, and cache static files.
3. **Database Migration:** Replace SQLite with a robust remote database (e.g., PostgreSQL) by updating the `DATABASE_URL` env variable in production:
   ```env
   DATABASE_URL=postgresql://user:password@hostname:5432/database_name
   ```

### Frontend Deployment:
1. Compile the static assets using Vite:
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy the generated `dist/` folder to a high-availability CDN or static web host (such as AWS S3, Cloudflare Pages, or serve directly via Nginx configuration).

---

## 🔮 18. Future Improvements
- **True Multi-Agent LangGraph Workflows:** Fully integrate Python `langgraph` state machines to coordinate complex, self-correcting agent tasks (e.g., automatically drafting responses to critical emails for review).
- **Embedded Semantic Vector Search:** Replace simple SQL string matching with high-performance vector databases (such as FAISS, ChromaDB, or pgvector) to store text embeddings for advanced historical semantic retrieval.
- **Deep Notification Channels:** Implement real-world integration routes allowing the `WorkflowService` to dispatch alerts to Slack, post cards directly to Notion tables, or file tickets in Jira.
- **OAuth Multi-User Support:** Extend database schemas to support multi-tenant session isolation and role-based permissions access control.

---

## 🤝 19. Contribution Guide
We welcome contributions to improve the **Auto-Task-Generator**!

### Guidelines:
1. **Coding Style:** Follow standard Python PEP 8 guidelines. Keep Pydantic validations up-to-date when altering schemas.
2. **Branch Naming:** Keep branches descriptive: `feature/your-feature` or `bugfix/your-fix`.
3. **Testing:** Run manual validation through the local FastAPI docs portal (`/docs`) before submitting changes.
4. **Pull Requests:** Ensure you maintain code docstrings and update this project documentation for any architectural alterations.

---

## 👥 20. Authors & Contributors
- **Prakhar Kle** - Primary Architecture Designer & Repository Maintainer.

---

*This document serves as the single source of truth for the codebase architecture of the Auto-Task-Generator project. For queries, reach out to the project repository maintainer.*
