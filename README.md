# AI SQL Query Optimizer

An intelligent, ML-powered tool that analyzes SQL queries, predicts execution performance, and suggests optimizations — built with Java Spring Boot, Python ML, and React.

---

## Architecture

```
┌──────────────┐     HTTP      ┌──────────────────┐     HTTP      ┌──────────────────┐
│              │  ──────────►  │                  │  ──────────►  │                  │
│   React UI   │               │  Spring Boot API │               │  Python ML API   │
│   (Vite)     │  ◄──────────  │  (Java 17)       │  ◄──────────  │  (FastAPI)       │
│              │     JSON      │                  │     JSON      │                  │
└──────────────┘               └────────┬─────────┘               └──────────────────┘
                                        │
                                        │ JDBC
                                        ▼
                               ┌──────────────────┐
                               │                  │
                               │   PostgreSQL     │
                               │                  │
                               └──────────────────┘
```

---

## Planned Features

- **SQL Query Analysis** — Parse and extract structural features (joins, subqueries, table scans)
- **Performance Prediction** — ML model predicts query execution time and slow-query probability
- **Index Recommendations** — Suggests optimal indexes based on query patterns
- **Query Optimization** — Rewrites queries for better performance
- **Visual Dashboard** — Clean UI showing analysis results, badges, and suggestions

---

## Tech Stack

| Layer            | Technology                        |
|------------------|-----------------------------------|
| Frontend         | React 18 + Vite                   |
| Backend API      | Java 17 + Spring Boot 3           |
| SQL Parsing      | JSqlParser                        |
| ML Service       | Python 3.11 + FastAPI + scikit-learn |
| Database         | PostgreSQL 15                     |
| Containerization | Docker + Docker Compose           |

---

## Project Structure

```
ai-sql-optimizer/
├── backend/              # Spring Boot REST API
├── frontend/             # React + Vite UI
├── ml-service/           # FastAPI ML prediction service
├── dataset-generator/    # Synthetic SQL dataset generator
├── docs/                 # Architecture diagrams & API docs
├── docker-compose.yml    # Full-stack local orchestration
└── README.md
```

---

## Development Roadmap

- [x] **Phase 0** — Repository scaffold & documentation
- [x] **Phase 1** — Frontend UI with mock data
- [x] **Phase 2** — Spring Boot API (dummy response)
- [x] **Phase 3** — Real SQL parsing with JSqlParser
- [x] **Phase 4** — Dataset generator for ML training
- [ ] **Phase 5** — ML model training & FastAPI prediction service
- [ ] **Phase 6** — Dockerized full-stack deployment
- [ ] **Phase 7** — GitHub polish (diagrams, screenshots, API docs)

---

## Quick Start

```bash
# Full stack (after Phase 6)
docker-compose up

# Frontend only (after Phase 1)
cd frontend && npm install && npm run dev

# Backend only (after Phase 2)
cd backend && ./mvnw spring-boot:run
```

---

## License

MIT
