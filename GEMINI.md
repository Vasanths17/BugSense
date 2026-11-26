# GEMINI.md — BugSense Project Rules & Guidelines

## 1. Project Overview & Goal
- **Project Name:** BugSense
- **Full Title:** BugSense: An Explainable AI-Assisted Software Debugging System
- **Context:** MSc Final-Year Academic Project
- **Primary Objective:** Build an explainable software debugging system that analyzes uploaded projects, detects bugs/vulnerabilities/code smells, and provides clear, human-understandable explanations and recommendations without relying on external paid AI APIs.

---

## 2. Tech Stack & Exact Versions

### Backend (`/backend`)
- **Runtime:** Python 3.10+
- **Framework:** FastAPI (`fastapi==0.111.0`)
- **ASGI Server:** Uvicorn (`uvicorn[standard]==0.29.0`)
- **Validation / Schemas:** Pydantic (`pydantic==2.7.1`)
- **Multipart Form Parser:** `python-multipart==0.0.9`

### Frontend (`/frontend`)
- **Framework:** React 18 (`react: ^18.3.1`, `react-dom: ^18.3.1`)
- **Build Tool:** Vite (`vite: ^5.4.10`, `@vitejs/plugin-react: ^4.3.1`)
- **Styling:** Tailwind CSS (`tailwindcss: ^3.4.14`, `postcss: ^8.4.47`, `autoprefixer: ^10.4.20`)
- **Package Manager:** `pnpm` (or `npm`)

---

## 3. Strict Architectural & Security Constraints
The following rules must NEVER be violated by any agent or contributor:

1. **No Paid AI APIs:**
   - Do NOT add dependencies for OpenAI, Anthropic, Gemini API keys, or any other paid cloud-hosted AI APIs.
   - All debugging intelligence must use local static analysis (AST parsers, regex patterns, static checkers like Bandit/Flake8/Pylint/Semgrep/ESLint logic) combined with local rule-based explainability engines and local knowledge mappings.
2. **Never Execute Uploaded Code:**
   - Uploaded user source code must NEVER be executed, evaluated, imported, or run in any runtime environment (no `exec()`, `eval()`, `subprocess.Popen` running user code, or dynamic importing).
   - Only read, parse, and analyze source code as plain text / AST structures.
3. **Never Modify or Rewrite User Source Files:**
   - Uploaded files are strictly treated as read-only inputs for analysis.
   - Never write to or mutate files inside user project directories.
4. **Offline & Self-Contained:**
   - The system must function completely without outbound network requirements for analysis.

---

## 4. Coding Conventions & Directory Structure

### Project Layout
```
BugSense/
├── GEMINI.md               # Permanent rules & conventions for all AI agents
├── HANDOVER.md             # Migration state & status
├── README.md               # Project documentation & setup instructions
├── .gitignore              # Root gitignore (venv, node_modules, temp uploads)
├── backend/
│   ├── main.py             # FastAPI entrypoint, middleware, router mounts
│   ├── requirements.txt    # Pinned Python dependencies
│   ├── routers/            # Endpoint handlers (health, upload, analysis, etc.)
│   ├── services/           # Core business logic, AST parsers, analysis engines
│   ├── models/             # Pydantic schemas for request/response validation
│   └── knowledge_base/     # Static explainability rules & error dictionary
└── frontend/
    ├── index.html          # HTML entry point (title: "BugSense - AI Debugging")
    ├── package.json        # Frontend scripts and dependencies
    ├── vite.config.js      # Vite configuration
    ├── tailwind.config.js  # Tailwind CSS configuration
    ├── postcss.config.js   # PostCSS configuration
    └── src/
        ├── main.jsx        # React root mounting
        ├── App.jsx         # App container, top nav, sidebar, layout
        ├── index.css       # Tailwind directives
        └── components/     # Modular view and UI components
```

### Conventions
- **Backend:**
  - Keep route definitions in `routers/` light; delegate analysis logic to `services/`.
  - Always validate incoming and outgoing payloads using Pydantic models in `models/`.
  - Prefix all API routes with `/api/` (e.g., `/api/health`, `/api/upload`, `/api/analyze`).
  - Maintain CORS support for `http://localhost:5173` and `http://127.0.0.1:5173`.
- **Frontend:**
  - Keep styling strictly in Tailwind utility classes; do not introduce heavy UI component libraries.
  - Maintain consistent color palette: Slate header & sidebar (`slate-900`, `slate-800`), light main canvas (`gray-50`), blue accents (`blue-600`).
  - Isolate distinct view pages (Upload, Dashboard, Issues Explorer, Reports) into modular components under `src/components/` as development progresses.

---

## 5. How to Run the Application

### Backend Server
- **Directory:** `/backend`
- **Port:** `8000` (`http://localhost:8000`)
- **Commands:**
  ```bash
  cd backend
  python -m venv venv
  # Windows:
  venv\Scripts\activate
  # Linux/macOS:
  # source venv/bin/activate
  pip install -r requirements.txt
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Health Verification:** `GET http://localhost:8000/api/health`

### Frontend Server
- **Directory:** `/frontend`
- **Port:** `5173` (`http://localhost:5173`)
- **Commands:**
  ```bash
  cd frontend
  pnpm install
  pnpm dev
  ```
- **Access UI:** `http://localhost:5173`
