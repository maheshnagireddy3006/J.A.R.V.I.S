# J.A.R.V.I.S. // Edge-First Local Graph-Agent & Microservices Ecosystem

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI%20%7C%20REST-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/frontend-React%2018%20%7C%20Vite-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/framework-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/llm-Ollama%20(Llama%203.1%208B)-purple.svg)](https://ollama.com/)
[![ChromaDB](https://img.shields.io/badge/vector%20db-ChromaDB-green.svg)](https://www.trychroma.com/)
[![SQLAlchemy](https://img.shields.io/badge/orm-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/container-Docker%20%7C%20Compose-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-19%20passed-brightgreen.svg)](tests/)

An ultra-capable, localized, edge-first AI workstation ecosystem combining:
1. **Autonomous Multi-Step Agent** with LangGraph and self-correction loops.
2. **Local Sensory Perception**: RealtimeSTT (Whisper on CPU) and Kokoro-82M neural TTS.
3. **High-Throughput Microservices**: RESTful API, WebSockets, SSR, and Redis caching.
4. **Dual Database Architecture**: 3NF normalized SQL ORM (SQLite/PostgreSQL) and NoSQL Document Store with aggregation pipelines.
5. **Modern React Web HUD Dashboard**: Component composition, hooks, controlled inputs, and real-time streaming telemetry.
6. **Enterprise Security**: Salted PBKDF2 password hashing, JWT authentication, RBAC, rate limiting, and prompt injection defenses.

---

## Architecture Specifications & Design Documents

Comprehensive engineering documentation detailing all 50 system concepts:
- [Product Requirements Document (PRD.md)](PRD.md)
- [High-Level Design (HLD.md)](HLD.md)
- [Low-Level Design (LLD.md)](LLD.md)

---

## Implemented Concept Matrix

| Category | Key Concepts Implemented | Codebase Module |
| :--- | :--- | :--- |
| **AI App Engineering** | Multi-step agent, Function calling / tool use, LLM API integration, Prompt engineering, Structured outputs, Streaming responses, RAG vector retrieval, LLM eval sets, Token & cost monitoring, Prompt injection defenses | `brain.py`, `server.py`, `config.py` |
| **Backend & System Design**| RESTful endpoint design, HTTP status codes, Server-side error handling, Custom ASGI middleware, Request body validation, File upload handling, Backend deployment | `server.py`, `deploy.sh` |
| **Auth & Security** | Password hashing (PBKDF2/bcrypt), JWT issuance & verification, Role-based authorization checks (RBAC), Rate limiting, Input sanitization & injection awareness, OAuth / 3rd-party login | `auth.py`, `server.py` |
| **SQL (Postgres/SQLite)** | Relational schema design with PK/FK, SQL JOINs, Indexing for query performance, Filtering, ordering, grouping, Normalization basics (3NF), ORM usage (SQLAlchemy), ACID transactions | `database.py` |
| **NoSQL (Mongo-style)** | Document schema modeling, CRUD operations (`insert_one`, `find`, `update_one`, `delete_one`), Embedding vs referencing relationships, Aggregation pipelines (`$match`, `$group`, `$sort`, `$project`), Indexing | `database.py` |
| **Frontend & React** | React component composition, State management with `useState`, Side effects with `useEffect`, Async data fetching from API, Client-side routing, Loading & error UI states, Form handling (controlled inputs), Form validation, Responsive styling, Frontend deployment | `web/src/App.jsx`, `web/src/components/*` |
| **JavaScript Fundamentals**| Event loop, Promises vs callbacks, async/await, Closures, Hoisting | `web/src/utils/js_concepts.js` |
| **System & Integration** | Caching with Redis & In-Memory fallback, WebSocket real-time communication, Scheduled jobs / cron, 3rd-party API integration, Server-side rendering (SSR), Payment gateway integration | `server.py`, `cache.py`, `payment.py` |
| **Engineering Practices** | Writing unit tests, Automated API testing / integration tests, Git workflow, Environment variables & secrets management, Containerization with Docker | `tests/*`, `.env.example`, `Dockerfile`, `docker-compose.yml` |

---

## Automated Test Suite

Run the full unit and integration test suite:
```bash
pytest tests/ -v
```
**Results: 19 passed across all modules (100% pass rate).**

---

## Quick Start & Execution

### 1. Start Background Services
```bash
# Start Ollama local LLM server
ollama serve

# (Optional) Start Redis cache
docker compose up -d redis
```

### 2. Launch FastAPI REST & WebSocket Microservices
```bash
uvicorn server:app --host 127.0.0.1 --port 8000
```
API Documentation will be live at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`
- SSR Dashboard: `http://127.0.0.1:8000/ssr/dashboard`

### 3. Launch Holographic Desktop HUD
```bash
python main.py
```

### 4. Launch React Web HUD
```bash
cd web
npm install
npm run dev
```

---

## License
MIT License. Created by [Mahesh Balaji Nagireddy](https://github.com/maheshnagireddy3006).
