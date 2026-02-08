# Architecture Overview

## System Architecture

The AI SQL Query Optimizer is composed of four services orchestrated via Docker Compose.

```mermaid
graph TB
    subgraph Client
        UI["React UI<br/>(Vite + Nginx)"]
    end

    subgraph Backend
        API["Spring Boot API<br/>(Java 17)"]
        Parser["JSqlParser"]
        Optimizer["Query Optimizer"]
        IndexAdvisor["Index Suggestion Engine"]
        MLClient["ML Service Client"]
    end

    subgraph ML["ML Service"]
        FastAPI["FastAPI Server"]
        GBR["GradientBoosting<br/>Regressor"]
        GBC["GradientBoosting<br/>Classifier"]
        Scaler["StandardScaler"]
    end

    subgraph Data
        PG["PostgreSQL 15"]
    end

    UI -- "POST /api/analyze" --> API
    API --> Parser
    API --> Optimizer
    API --> IndexAdvisor
    API -- "POST /predict" --> MLClient
    MLClient --> FastAPI
    FastAPI --> Scaler --> GBR
    Scaler --> GBC
    API -- "JDBC" --> PG

    style UI fill:#61dafb,color:#000
    style API fill:#6db33f,color:#fff
    style FastAPI fill:#009688,color:#fff
    style PG fill:#336791,color:#fff
```

## Request Flow

```mermaid
sequenceDiagram
    participant User
    participant React as React UI
    participant Spring as Spring Boot API
    participant Parser as JSqlParser
    participant ML as FastAPI ML Service

    User->>React: Enter SQL query
    React->>Spring: POST /api/analyze { query }
    Spring->>Parser: Parse SQL
    Parser-->>Spring: ParseResult (tables, joins, conditions...)

    Spring->>Spring: Generate index suggestions
    Spring->>Spring: Generate optimization tips

    Spring->>ML: POST /predict { features }
    ML-->>Spring: { predicted_time_ms, is_slow, confidence }

    Spring-->>React: AnalyzeResponse (JSON)
    React-->>User: Render results dashboard
```

## Service Responsibilities

| Service | Port | Role |
|---------|------|------|
| **React UI** | 5173 | User interface — query input, results dashboard |
| **Spring Boot API** | 8080 | SQL parsing, optimization, index suggestions, ML client |
| **FastAPI ML Service** | 8000 | Execution time prediction, slow-query classification |
| **PostgreSQL** | 5432 | Database (available for future EXPLAIN ANALYZE integration) |

## ML Pipeline

```mermaid
flowchart LR
    A["Dataset Generator<br/>5,000 synthetic queries"] --> B["Feature Extraction<br/>14 numeric features"]
    B --> C["Model Training<br/>GradientBoosting"]
    C --> D["Regressor<br/>(execution time)"]
    C --> E["Classifier<br/>(slow/fast)"]
    D --> F["FastAPI Service"]
    E --> F
    F --> G["Spring Boot<br/>ML Client"]
```

### Model Performance

| Metric | Value |
|--------|-------|
| **Regression R²** | 0.861 |
| **Regression MAE** | 39.9 ms |
| **Classification Accuracy** | 97.8% |
| **Classification F1** | 0.793 |

### Top Feature Importances

| Feature | Importance |
|---------|------------|
| `num_joins` | 0.419 |
| `num_tables` | 0.308 |
| `query_length` | 0.120 |
| `has_group_by` | 0.035 |
| `num_order_columns` | 0.034 |

## Directory Structure

```
ai-sql-optimizer/
├── backend/                  # Spring Boot REST API (Java 17)
│   └── src/main/java/com/sqloptimizer/
│       ├── controller/       # REST endpoints
│       ├── dto/              # Request/response DTOs
│       ├── service/          # Business logic
│       │   ├── SqlParserService.java
│       │   ├── IndexSuggestionService.java
│       │   ├── QueryOptimizerService.java
│       │   └── MlPredictionService.java
│       └── config/           # CORS, RestTemplate config
├── frontend/                 # React + Vite UI
│   └── src/
│       ├── components/       # QueryInput, ResultsPanel
│       ├── api.js            # API client
│       └── mockData.js       # Fallback mock data
├── ml-service/               # FastAPI + scikit-learn
│   ├── app.py                # Prediction endpoints
│   ├── train_model.py        # Model training script
│   └── models/               # Serialized models & metrics
├── dataset-generator/        # Synthetic SQL dataset generator
│   ├── sql_templates.py      # 10 query patterns
│   ├── features.py           # 14-feature extractor
│   ├── simulator.py          # Execution time simulator
│   └── generate_dataset.py   # CLI entry point
├── docs/                     # Architecture & API documentation
├── docker-compose.yml        # Full-stack orchestration
└── README.md
```
