# Contributing to AI SQL Query Optimizer

Thanks for your interest in contributing! This guide covers how to set up the project locally and submit changes.

---

## Prerequisites

| Tool | Version | Required For |
|------|---------|-------------|
| **Java** | 17+ | Backend (Spring Boot) |
| **Maven** | 3.9+ | Backend build (or use included `mvnw`) |
| **Node.js** | 18+ | Frontend (React + Vite) |
| **Python** | 3.11+ | ML Service + Dataset Generator |
| **Docker** | 24+ | Full-stack deployment |

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/asechan/sql-optimizer.git
cd sql-optimizer/ai-sql-optimizer
```

### 2. Start services

**Option A: Docker (recommended for first run)**

```bash
docker-compose up --build
```

**Option B: Run each service manually**

```bash
# Terminal 1 — ML Service
cd ml-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Backend
cd backend
./mvnw spring-boot:run

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev
```

### 3. Verify everything is running

| Service | URL | Expected |
|---------|-----|----------|
| Frontend | http://localhost:5173 | React UI |
| Backend | http://localhost:8080/api/health | `{"status":"UP"}` |
| ML Service | http://localhost:8000/health | `{"status":"ok","models_loaded":true,...}` |

---

## Project Structure

| Directory | Language | Description |
|-----------|----------|-------------|
| `backend/` | Java 17 | Spring Boot REST API, SQL parsing, optimization |
| `frontend/` | JavaScript | React + Vite UI |
| `ml-service/` | Python | FastAPI ML prediction service |
| `dataset-generator/` | Python | Synthetic SQL dataset generator |
| `docs/` | Markdown | Architecture diagrams, API docs |

---

## Making Changes

### Branch naming

```
feature/short-description
fix/issue-description
docs/what-changed
```

### Workflow

1. **Fork** the repository and create a feature branch
2. Make your changes with clear, focused commits
3. Run the relevant tests / linting (see below)
4. Open a **Pull Request** against `master`

### Commit messages

Use clear, imperative-mood messages:

```
Add LIMIT optimization rule for unbounded queries
Fix JSqlParser crash on nested subqueries
Update API docs for /predict endpoint
```

---

## Code Style

### Java (Backend)

- Follow standard Java conventions
- Use `final` for immutable variables
- Prefer records for DTOs where applicable
- Service classes should be annotated with `@Service`

### JavaScript (Frontend)

- Functional React components with hooks
- CSS modules per component (`Component.css`)
- API calls in `api.js`

### Python (ML Service)

- PEP 8 style
- Type hints on function signatures
- Pydantic models for request/response schemas
- Use `async def` for FastAPI endpoints

---

## Testing

### Backend

```bash
cd backend
./mvnw test
```

### Frontend

```bash
cd frontend
npm test        # if test runner is configured
npm run lint    # ESLint
```

### ML Service

```bash
cd ml-service
python -m pytest  # if tests are added
```

### Full stack via Docker

```bash
docker-compose up --build
# Then manually test at http://localhost:5173
```

---

## Retraining the ML Model

If you change the dataset generator or feature extraction:

```bash
# 1. Generate a new dataset
cd dataset-generator
python generate_dataset.py --num 10000 --seed 42 --out ../ml-service/data/training.csv

# 2. Retrain models
cd ../ml-service
python train_model.py
```

Model artifacts are saved to `ml-service/models/`.

---

## Reporting Issues

When opening an issue please include:

- **What you expected** vs **what happened**
- Steps to reproduce
- Browser / OS / Docker version if relevant
- Any error messages or logs

---

## License

By contributing you agree that your contributions will be licensed under the [MIT License](LICENSE).
