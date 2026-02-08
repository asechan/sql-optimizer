# Frontend — AI SQL Query Optimizer

React + Vite UI for the AI SQL Query Optimizer.

## Features

- **Query Input** — SQL editor with syntax highlighting placeholder
- **Results Dashboard** — Performance badge, predicted time, confidence, slow probability
- **Index Suggestions** — Displays recommended `CREATE INDEX` statements
- **Optimized Query** — Shows rewritten query with applied optimizations
- **Optimization Tips** — Lists actionable performance improvement suggestions
- **Query Features** — Shows parsed structural breakdown (tables, joins, conditions, etc.)
- **Graceful Fallback** — Uses mock data when backend is unavailable

## Quick Start

```bash
npm install
npm run dev
```

Open http://localhost:5173

## Build for Production

```bash
npm run build
```

Output is in `dist/`, served by Nginx in Docker.

## Project Structure

```
src/
├── App.jsx              # Main app layout
├── App.css              # App-level styles
├── api.js               # Backend API client (/api/analyze)
├── mockData.js          # Fallback mock analysis data
├── main.jsx             # React entry point
├── index.css            # Global styles
└── components/
    ├── QueryInput.jsx   # SQL input textarea + analyze button
    ├── QueryInput.css
    ├── ResultsPanel.jsx # Analysis results dashboard
    └── ResultsPanel.css
```

## API Integration

The frontend calls `POST /api/analyze` with `{ "query": "..." }`.

- **Docker**: Nginx proxies `/api` → `backend:8080`
- **Dev**: Vite proxy configured in `vite.config.js`

If the backend is unavailable, the app falls back to mock data and shows a warning banner.
