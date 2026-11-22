# BugSense: Explainable AI-Assisted Software Debugging System

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)
![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF)
![Tailwind CSS](https://img.shields.io/badge/Styles-Tailwind%20CSS-38BDF8)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

---

## Overview

**BugSense** is an AI-powered software debugging platform that goes beyond surface-level error detection. It ingests your project's source code (as a ZIP archive), runs intelligent static and dynamic analysis, and surfaces explainable, human-readable insights about bugs, code smells, and potential vulnerabilities — all through a clean, interactive web interface.

> Think of BugSense as your always-on senior code reviewer: it not only spots what's wrong, but explains *why* it matters and *how* to fix it.

---

## Tech Stack

| Layer      | Technology            | Purpose                                   |
|------------|-----------------------|-------------------------------------------|
| **Backend**  | Python 3.10+         | Core runtime                              |
| **Backend**  | FastAPI               | REST API framework                        |
| **Backend**  | Uvicorn               | ASGI server                               |
| **Backend**  | Pydantic              | Data validation & settings management     |
| **Backend**  | LangChain / Gemini    | AI analysis & explainability engine       |
| **Backend**  | Ruff / AST            | Static code analysis                      |
| **Frontend** | React 18              | UI framework                              |
| **Frontend** | Vite                  | Build tool & dev server                   |
| **Frontend** | Tailwind CSS          | Utility-first styling                     |
| **Frontend** | Axios                 | HTTP client for API calls                 |

---

## Project Structure

```
BugSense/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── routers/
│   │   ├── health.py            # Health check endpoint
│   │   ├── upload.py            # ZIP upload & extraction
│   │   └── analysis.py          # AI analysis routes
│   ├── services/
│   │   ├── parser.py            # Source code parser
│   │   ├── analyzer.py          # Static analysis engine
│   │   └── explainer.py         # AI explainability layer
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── utils/
│   │   └── file_utils.py        # ZIP handling & temp file management
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Route-level page components
│   │   ├── api/                 # Axios API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── uploads/                     # Temporary uploaded ZIPs (git-ignored)
├── temp/                        # Extracted project files (git-ignored)
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18+ and **pnpm** (install pnpm via `npm install -g pnpm`)
- **Git**

---

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**  
Interactive docs (Swagger UI) at **http://localhost:8000/docs**

---

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
pnpm install

# 3. Start the development server
pnpm dev
```

The frontend will be available at **http://localhost:5173**

---

## API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| `GET`  | `/api/health`         | Health check — returns service status    |
| `POST` | `/api/upload`         | Upload a ZIP file for analysis           |
| `GET`  | `/api/analysis/{id}`  | Retrieve analysis results by session ID  |
| `GET`  | `/api/report/{id}`    | Download a formatted bug report          |

---

## Roadmap

| Phase | Description                                | Status        |
|-------|--------------------------------------------|---------------|
| **Phase 1** | Base Setup — project scaffold, FastAPI skeleton, React + Vite + Tailwind bootstrap | ✅ Complete |
| **Phase 2** | ZIP Upload & Parsing — file ingestion, extraction, language detection | 🔲 Planned |
| **Phase 3** | AI Analysis Engine — static analysis + LLM-driven bug detection | 🔲 Planned |
| **Phase 4** | Explainability Layer — natural-language explanations, severity scoring | 🔲 Planned |
| **Phase 5** | Reports — exportable PDF/HTML bug reports, historical dashboard | 🔲 Planned |

---

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change, then submit a pull request against the `main` branch.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with ❤️ using FastAPI, React, and Gemini AI</p>
