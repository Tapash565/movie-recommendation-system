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

> **🔒 Security Note:** Environment variables are injected at **runtime** and are never baked into Docker images. The `.env` files are excluded from version control and should never be committed.

---

### 2. Run with Docker Compose (Recommended)

The easiest way to run the full stack is via Docker Compose:

```bash
docker-compose up --build
```

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000/docs](http://localhost:8000/docs)

**Environment Variable Injection:**
Docker Compose automatically loads environment variables from `backend/.env` via the `env_file` directive. Secrets are never copied into image layers.

**Alternative methods for production:**
```bash
# Method 1: Direct environment variables
docker run -e DATABASE_URL="postgresql://..." -e SECRET_KEY="..." -p 8000:8000 backend

# Method 2: Environment file
docker run --env-file backend/.env -p 8000:8000 backend

# Method 3: Docker Compose environment key
# See docker-compose.yml for the environment: configuration example
```

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
- **🔐 Environment Variables:** Configure via Render's dashboard (never commit to repo):
  - `DATABASE_URL` - Your database connection string
  - `SECRET_KEY` - JWT secret key for authentication
  - `HUGGINGFACEHUB_API_TOKEN` - HuggingFace API token

### Frontend (Vercel)
- **Repo:** Connect this repository.
- **Root Directory:** `frontend`
- **Framework Preset:** Next.js
- **🔐 Environment Variables:** Configure via Vercel dashboard:
  - `NEXT_PUBLIC_API_URL` - Your production backend URL (e.g., `https://your-api.render.com/api`)

### Other Production Platforms

**Kubernetes:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
data:
  DATABASE_URL: <base64-encoded>
  SECRET_KEY: <base64-encoded>
```

**AWS ECS/Fargate:**
Use AWS Secrets Manager or Parameter Store, then reference in task definitions.

**Docker Swarm:**
```bash
docker secret create db_url /path/to/db_url.txt
docker service create --secret db_url backend
```

## 🧪 CI/CD

GitHub Actions automatically validate pull requests:
- **Backend CI:** Linting & Docker Build test.
- **Frontend CI:** Build check & Docker Standalone conversion test.
