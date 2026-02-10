# Movie Recommendation System

A modern, full-stack movie recommendation system built with **FastAPI** (Backend) and **Next.js** (Frontend). It features personalized recommendations using FAISS, a robust search engine, and a premium "Cyberpunk/Neon" UI.

## 🏗 Architecture

The project is structured as a monorepo with separate services for the frontend and backend:

```bash
movie_recommendation_system_deployment/
│
├── backend/                 # FastAPI (Python 3.11)
│   ├── app/                 # Application Code
│   ├── data/                # Movie Data & FAISS Index
│   └── Dockerfile           # Production Dockerfile
│
├── frontend/                # Next.js 15 (React 19)
│   ├── src/                 # Components, Pages, & Lib
│   └── Dockerfile           # Standalone Production Build
│
├── .github/workflows/       # CI/CD Pipelines
│   ├── backend-ci.yml       # Backend Validation
│   └── frontend-ci.yml      # Frontend Validation
│
└── docker-compose.yml       # Local Development Orchestration
```

## 🚀 Getting Started

### Prerequisites
- **Docker Desktop** (Recommended)
- **Node.js 20+** (For local frontend dev)
- **Python 3.11+** (For local backend dev)

### 1. Environment Setup

Copy the example environment files and fill in your credentials:

**Backend:**
```bash
cp backend/.env.example backend/.env
```
*Required: `DATABASE_URL`, `SECRET_KEY`, `HUGGINGFACEHUB_API_TOKEN`*

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```
*Required: `NEXT_PUBLIC_API_URL=http://localhost:8000/api`*

---

### 2. Run with Docker Compose (Recommended)

The easiest way to run the full stack is via Docker Compose:

```bash
docker-compose up --build
```

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 3. Run Locally (Manual)

If you prefer running services individually without Docker:

**Backend (Terminal 1):**
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm install
npm run dev
```

## 🛠 Deployment

### Backend (Render)
- **Repo:** Connect this repository.
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- **Environment:** Set `PYTHON_VERSION` to `3.11.0`.

### Frontend (Vercel)
- **Repo:** Connect this repository.
- **Root Directory:** `frontend`
- **Framework Preset:** Next.js
- **Environment Variables:** Set `NEXT_PUBLIC_API_URL` to your production backend URL.

## 🧪 CI/CD

GitHub Actions automatically validate pull requests:
- **Backend CI:** Linting & Docker Build test.
- **Frontend CI:** Build check & Docker Standalone conversion test.
