# GEMINI.md — BugSense Project Rules & Guidelines

## 1. Project Overview & Goal
- **Project Name:** BugSense
- **Full Title:** BugSense: An Explainable AI-Assisted Software Debugging System
- **Context:** MSc Final-Year Academic Project
- **Primary Objective:** Build an explainable software debugging system that analyzes uploaded projects, detects bugs/vulnerabilities/code smells, and provides clear, human-understandable explanations and recommendations without relying on external paid AI APIs.

---

## 2. Tech Stack & Exact Versions

### Backend (`/backend`)
- **Runtime:** Python 3.10+ (Verified on Python 3.11.3)
- **Framework:** FastAPI (`fastapi==0.111.0`)
- **ASGI Server:** Uvicorn (`uvicorn[standard]==0.29.0`)
- **Validation / Schemas:** Pydantic v2 (`pydantic==2.7.1`)
- **Multipart Form Parser:** `python-multipart==0.0.9`
- **Static Bug Linter:** Ruff (`ruff==0.4.4`)
- **Security Scanner:** Bandit (`bandit==1.7.8`)
- **Code Quality & Metrics:** Radon (`radon==6.0.1`)
- **PDF Generation:** ReportLab (`reportlab==4.2.0`)
- **Test Framework:** Pytest (`pytest==8.2.0`)

### Frontend (`/frontend`)
- **Framework:** React 18 (`react: ^18.3.1`, `react-dom: ^18.3.1`)
- **Build Tool:** Vite (`vite: ^5.4.10`, `@vitejs/plugin-react: ^4.3.1`)
- **Styling:** Tailwind CSS (`tailwindcss: ^3.4.14`, `postcss: ^8.4.47`, `autoprefixer: ^10.4.20`)
- **Data Visualization:** Recharts (`recharts: ^3.11.1`)
- **Package Manager:** `pnpm` (or `npm`)

---

## 3. Strict Architectural & Security Constraints
The following rules must NEVER be violated by any agent or contributor:

1. **No Paid AI APIs:**
   - Do NOT add dependencies for OpenAI, Anthropic, Gemini API keys, or any other paid cloud-hosted AI APIs.
   - All debugging intelligence uses local static analysis (AST parsers, regex patterns, Ruff, Bandit, Radon) combined with a local rule-based explainability engine (`backend/knowledge_base/rules.json`) and fallback templates.
2. **Never Execute Uploaded Code:**
   - Uploaded user source code must NEVER be executed, evaluated, imported, or run in any runtime environment (no `exec()`, `eval()`, `subprocess.Popen` running user code, or dynamic importing).
   - Only read, parse, and analyze source code as plain text / AST structures.
3. **Never Modify or Rewrite User Source Files:**
   - Uploaded files are strictly treated as read-only inputs for analysis.
   - Never write to or mutate files inside user project directories.
4. **Offline & Self-Contained:**
   - The system functions completely without outbound network requirements for analysis.
5. **Path Traversal & Archive Security:**
   - All archive uploads are strictly validated against Zip Slip (rejecting any members with `..` or absolute paths) and bounded by a 25 MB archive limit and 150 MB uncompressed ceiling (zip-bomb guard).
6. **Credential Masking:**
   - Any detected hardcoded passwords, AWS credentials, or API tokens must be masked in outputs and code snippets (`sk****90`) so secrets are never leaked.

---

## 4. Coding Conventions & Directory Structure

### Project Layout
```
BugSense/
├── GEMINI.md                   # Permanent rules & conventions for all AI agents
├── HANDOVER.md                 # Migration state & complete feature status
├── README.md                   # Project documentation & setup instructions
├── .gitignore                  # Root gitignore (venv, node_modules, temp uploads)
├── backend/
│   ├── main.py                 # FastAPI entrypoint, middleware, router mounts
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── routers/                # Endpoint handlers
│   │   ├── __init__.py
│   │   ├── health.py           # GET /api/health
│   │   ├── upload.py           # POST /api/upload, GET /api/project/{id}/file
│   │   └── analysis.py         # POST /api/analyze/{id}, GET /api/analysis/{id}, GET /api/report/{id}/pdf, DELETE /api/project/{id}
│   ├── services/               # Core business logic & analysis engines
│   │   ├── __init__.py
│   │   ├── upload_service.py   # Safe ZIP extraction, recursive tree scanner
│   │   ├── bug_detector.py     # AST parser, Ruff runner, JS/TS patterns
│   │   ├── security_scanner.py # Bandit runner, secrets/SQLi/exec patterns, secret masking
│   │   ├── quality_analyzer.py # Radon complexity, maintainability index, raw LOC
│   │   ├── health_score.py     # 0-100 Project Health Score calculation
│   │   ├── explainer.py        # Rule translation to 9 required fields & severity
│   │   └── pdf_generator.py    # ReportLab PDF report builder with NumberedCanvas
│   ├── models/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── upload.py           # FileNode, UploadResponse, FileContentResponse
│   │   └── finding.py          # RawFinding, ExplainedIssue, AnalysisReport, HealthScoreDetails
│   ├── knowledge_base/         # Static explainability rules dictionary
│   │   └── rules.json          # Curated mappings (Bug, Security, Quality)
│   ├── tests/                  # Pytest test suite (24 unit tests)
│   └── temp_uploads/           # Isolated temporary project extractions
└── frontend/
    ├── index.html              # HTML entry point (title: "BugSense - AI Debugging")
    ├── package.json            # Frontend scripts and dependencies
    ├── vite.config.js          # Vite configuration
    ├── tailwind.config.js      # Tailwind CSS configuration
    ├── postcss.config.js       # PostCSS configuration
    └── src/
        ├── main.jsx            # React root mounting
        ├── App.jsx             # Top nav, sidebar, router state, analysis trigger
        ├── config.js           # API_BASE endpoint configuration
        ├── index.css           # Tailwind directives
        └── components/         # Modular views and components
            ├── UploadZone.jsx          # Drag-and-drop ZIP upload with validation
            ├── FileTree.jsx            # Collapsible directory tree explorer
            ├── CodeViewer.jsx          # Read-only code viewer with line numbers
            ├── DashboardView.jsx       # Health gauge, KPI cards, Recharts charts, metrics table
            ├── IssuesExplorerView.jsx  # Filter toolbar & 9-field Explainable Issue Card modal
            └── LangPill.jsx            # Per-language badges
```

### Conventions
- **Backend:**
  - Route handlers in `routers/` remain lightweight; business logic lives in `services/`.
  - Validate all inputs and outputs using Pydantic models in `models/`.
  - Prefix all API routes with `/api/`.
  - Maintain CORS support for `http://localhost:5173` and `http://127.0.0.1:5173`.
  - Automated 1-hour cleanup purges stale extracted folders in `temp_uploads/`.
- **Frontend:**
  - Keep styling strictly in Tailwind utility classes; avoid heavy external UI widget kits.
  - Consistent color palette: Slate header & sidebar (`slate-900`, `slate-800`), light canvas (`gray-50`), blue accents (`blue-600`), and semantic severity badges (Critical: red, High: orange, Medium: yellow, Low: blue).
  - All views (Upload, Dashboard, Issues Explorer, Reports) are modularized under `src/components/`.

---

## 5. How to Run the Application

### Backend Server
- **Directory:** `/backend`
- **Port:** `8000` (`http://localhost:8000`)
- **Commands:**
  ```powershell
  cd backend
  .\venv\Scripts\Activate.ps1
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Run Unit Tests:**
  ```powershell
  cd backend
  .\venv\Scripts\python.exe -m pytest tests/ -v
  ```

### Frontend Server
- **Directory:** `/frontend`
- **Port:** `5173` (`http://localhost:5173`)
- **Commands:**
  ```powershell
  cd frontend
  pnpm install
  pnpm dev
  ```
- **Production Build:**
  ```powershell
  cd frontend
  pnpm run build
  ```
- **Access UI:** `http://localhost:5173`
