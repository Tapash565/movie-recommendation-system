# Movie Recommendation System

A full-stack movie recommendation application powered by AI. The system uses FastAPI for the backend, Next.js for the frontend, PostgreSQL for data storage, and FAISS vector search with LangChain for intelligent movie recommendations.

## Features

- **AI-Powered Recommendations**: Semantic similarity search using FAISS vector database and LangChain with HuggingFace embeddings
- **Personalized Discovery**: Recommends movies based on user's watch history and ratings
- **User Library Management**: Save movies to watch later, mark as watched, and rate movies
- **Advanced Search**: Fuzzy matching search across movie titles and keywords
- **Firebase Authentication**: Secure user authentication via Firebase
- **Responsive UI**: Modern Next.js interface with smooth animations

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database for user data
- **LangChain** - LLM framework for AI components
- **FAISS** - Vector similarity search
- **HuggingFace** - Sentence transformer embeddings
- **Firebase Admin SDK** - Server-side authentication
- **SlowAPI** - Rate limiting

### Frontend
- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling
- **Framer Motion** - Animations
- **Firebase Client SDK** - Client-side authentication
- **Axios** - HTTP client

## Project Structure

```text
movie-recommendation-system/
├── backend/
│   ├── app/
│   │   ├── database.py       # PostgreSQL connection pool
│   │   ├── dependencies.py  # FastAPI dependencies (auth, data)
│   │   ├── logger.py         # Logging configuration
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── rate_limit.py     # Rate limiting configuration
│   │   ├── repositories/
│   │   │   └── user_repository.py  # Database operations
│   │   ├── routers/
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── movies.py     # Movie search & details
│   │   │   ├── recommendations.py  # Personalized recommendations
│   │   │   └── users.py      # User library management
│   │   ├── schemas.py        # Pydantic models
│   │   └── services/
│   │       ├── firebase_service.py   # Firebase initialization
│   │       ├── movie_service.py      # Movie & recommendation logic
│   │       └── user_service.py       # User data operations
│   ├── data/
│   │   ├── movie_list.pkl          # Movie dataset
│   │   └── movie_recommendation_faiss/  # FAISS index
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── discover/page.tsx    # Personalized recommendations
│   │   │   ├── library/page.tsx     # User's saved movies
│   │   │   ├── login/page.tsx       # Login page
│   │   │   ├── movie/[id]/page.tsx  # Movie details
│   │   │   ├── search/page.tsx      # Search page
│   │   │   ├── signup/page.tsx       # Signup page
│   │   │   ├── layout.tsx           # Root layout
│   │   │   └── page.tsx             # Home page
│   │   ├── components/              # Reusable UI components
│   │   └── lib/
│   │       ├── api.ts              # Axios configuration
│   │       ├── auth.ts             # Authentication utilities
│   │       ├── firebase.ts         # Firebase client setup
│   │       └── utils.ts            # Helper functions
│   ├── package.json
│   └── next.config.ts
└── docker-compose.yml               # Docker orchestration
```

## API Endpoints

### Movies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/movies/trending` | Get random trending movies |
| GET | `/api/movies/search` | Search movies with pagination |
| GET | `/api/movies/{movie_id}` | Get movie details with recommendations |

### Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/discover` | Get personalized recommendations (requires auth) |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/library` | Get user's movie library |
| POST | `/api/bookmark` | Add/update movie bookmark |
| POST | `/api/remove_bookmark` | Remove movie bookmark |
| POST | `/api/rate` | Rate a movie |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me` | Get current user info |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/api/health` | Deep health check (includes DB & data) |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL database
- Firebase project with Authentication enabled

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env.development` file (copy from `.env.example`):
   ```bash
   cp .env.example .env.development
   ```

5. Configure the following environment variables in `.env.development`:
   ```env
   DATABASE_URL=
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your_password
   FIREBASE_SERVICE_ACCOUNT_PATH=path/to/firebase-adminsdk.json
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
   CORS_ORIGINS=http://localhost:3000
   ```

6. Run the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`. API documentation is at `/api/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Configure Firebase (create `src/lib/firebase.ts` with your Firebase config):
   ```typescript
   import { initializeApp } from 'firebase/app';
   import { getAuth } from 'firebase/auth';

   const firebaseConfig = {
     // Your Firebase config here
   };

   const app = initializeApp(firebaseConfig);
   export const auth = getAuth(app);
   ```

5. Run the development server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`.

### Docker Setup

You can also run the application using Docker Compose:

```bash
docker-compose up --build
```

This will start both the backend (port 8000) and frontend (port 3000).

## Recommendation Algorithm

The system uses a hybrid recommendation approach:

1. **Content-Based Filtering**: Uses FAISS vector store with sentence-transformer embeddings (`all-MiniLM-L6-v2`) to find semantically similar movies based on titles and metadata
2. **Personalization**: Analyzes user's library (watched movies, highly-rated movies 4+ stars) to generate personalized recommendations
3. **Scoring**: Recommends movies that appear frequently in similar movie searches, weighted by their average rating

## Security

- **Authentication**: Firebase JWT tokens for API authentication
- **Rate Limiting**: Configurable rate limits per endpoint using SlowAPI
- **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options, HSTS
- **CORS**: Configurable allowed origins

## Development

### Running Tests

Backend tests:
```bash
cd backend
pytest
```

### Linting

Frontend:
```bash
cd frontend
npm run lint
```

## License

MIT License
