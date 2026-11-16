# Low-Level Design (LLD)

## Project Name: J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Subtitle: Edge-First Local Graph-Agent & Microservices Ecosystem
**Document Version:** 2.0.0  
**Author:** Mahesh Balaji Nagireddy (@maheshnagireddy3006)  
**Date:** November 2026  
**Status:** Fully Implemented & Validated  

---

## 1. Codebase Architecture & File Hierarchy

```
d:\Jarvis_core/
├── .env                       # Local secrets and configuration variables
├── .env.example               # Template for environment variables & secrets management
├── .gitignore                 # Version control exclusion rules (protects logs, cache, venv)
├── GIT_WORKFLOW.md            # Git Flow, branch conventions, PR template & semantic commits
├── package.json               # Node.js backend dependencies (Sequelize, Mongoose, Express, etc.)
├── package-lock.json          # Deterministic Node dependency lockfile
├── .vscode/
│   └── settings.json          # Python interpreter path and analysis bindings
├── backend/                   # Express Microservices & Database Tier
│   ├── server.js              # Express REST API, WebSockets, rate limiting, SSR & Stripe
│   └── models/
│       ├── sqlModels.js       # Sequelize ORM, PK/FK, SQL JOINs, transactions, 3NF
│       └── mongoModels.js     # Mongoose Schemas, embedded/referenced, indexes, aggregation
├── data/
│   ├── chroma/                # Persistent vector database (SQLite3 + HNSW indexes)
│   ├── jarvis_relational.db   # SQLite relational database (Users, Sessions, AuditLogs)
│   ├── jarvis_documents.json  # Document store persistence file
│   └── logs/                  # System operational logs
├── jarvis_env/                # Local Python 3.12 virtual environment
├── tests/                     # Comprehensive test suite (Unit & Integration)
│   ├── test_agent.py          # Multi-step agent, intent router, tools, self-correction tests
│   ├── test_api.py            # Automated API integration tests (HTTP codes, validation, SSR, payments)
│   ├── test_auth.py           # Password hashing, JWT, RBAC, and rate limiting tests
│   ├── test_database.py       # SQL JOINs, transactions, ORM, NoSQL CRUD & aggregation tests
│   └── test_security.py       # Prompt injection defenses and shell sanitization tests
├── web/                       # React Web HUD Frontend
│   ├── index.html             # Single-page application root HTML
│   ├── package.json           # React & React-Router dependencies
│   ├── vite.config.js         # Vite bundler configuration
│   └── src/
│       ├── App.jsx            # Client-side routing via react-router-dom
│       ├── index.css          # Responsive layout & styling with media queries
│       ├── main.jsx           # React DOM root bootstrapping
│       ├── components/
│       │   ├── CommandForm.jsx     # Controlled inputs, validation, loading/error UI states
│       │   ├── Dashboard.jsx       # Component composition, useState, useEffect, async fetch
│       │   ├── LoginForm.jsx       # Form validation, email regex, error boundaries
│       │   ├── TelemetryCard.jsx   # Props composition & responsive styling
│       │   └── TerminalConsole.jsx # Event streaming console
│       └── utils/
│           └── js_concepts.js      # JS Event Loop, Promises, async/await, Closures, Hoisting
├── audio_engine.py            # STT (RealtimeSTT Whisper) & TTS (Kokoro-82M) pipelines
├── auth.py                    # Password hashing, JWT, RBAC, rate limiting, sanitizer, OAuth
├── brain.py                   # LangGraph multi-step agent, ChromaDB RAG, LocalTools
├── cache.py                   # Redis caching client with in-memory TTL LRU fallback
├── config.py                  # Global hardware configuration, constants, & themes
├── database.py                # Relational ORM (SQLAlchemy), NoSQL Document Store (Mongo-style)
├── deploy.sh                  # Backend & Frontend deployment automation script
├── Dockerfile                 # Multi-stage Linux container definition
├── docker-compose.yml         # Container orchestration (Jarvis backend + Redis)
├── main.py                    # Ecosystem bootstrapper & multi-threaded coordinator
├── payment.py                 # Payment gateway integration (Stripe/Razorpay, webhooks)
├── pyrightconfig.json         # Static typing and language server configuration
├── requirements.txt           # Strict dependency pinning
├── run_jarvis.bat             # Windows one-click initialization batch launcher
├── server.py                  # FastAPI RESTful API, WebSockets, Middleware, SSR, Eval
├── ui_panel.py                # CustomTkinter holographic sci-fi desktop HUD
├── PRD.md                     # Product Requirements Document
├── HLD.md                     # High-Level Design Document
└── LLD.md                     # Low-Level Design Document
```

---

## 2. Authentication & Security Subsystem (`auth.py`)

### 2.1. Password Hashing
* **Algorithm**: PBKDF2 with HMAC-SHA256 and cryptographically random 16-byte salt (`os.urandom(16)`).
* **Iterations**: 100,000 iterations to resist GPU-based brute force cracking.
* **Storage Format**: `f"{salt.hex()}${key.hex()}"`.
* **Verification**: Uses constant-time equality check (`hmac.compare_digest`) to prevent timing side-channel attacks.

### 2.2. JWT Issuance & Verification
* **Algorithm**: HMAC-SHA256 (`HS256`).
* **Claims Structure**:
  ```python
  {
      "sub": str(username),
      "role": role,
      "iat": int(now.timestamp()),
      "exp": int(expire.timestamp())  # 120-minute validity
  }
  ```
* **Verification**: Cryptographic signature validation catching `jwt.ExpiredSignatureError` and `jwt.InvalidTokenError`, raising `PermissionError`.

### 2.3. Role-Based Authorization Checks (RBAC)
* **Hierarchy**: `{"admin": 3, "operator": 2, "guest": 1}`.
* **Enforcement**: Evaluates whether `user_level >= required_level`. Raises `PermissionError` when unauthorized.
* **API Integration**: FastAPI dependency injection `require_role("operator")` validates token claims before controller execution.

### 2.4. Rate Limiting (Sliding Window)
* **Algorithm**: In-memory sliding window tracking timestamp lists per client IP.
* **Eviction**: Discards timestamps outside `(current_time - window_seconds)`.
* **Threshold**: Blocks requests exceeding 100 requests / 60 seconds with HTTP 429 Too Many Requests.

### 2.5. Input Sanitization & Injection Awareness
* **Prompt Injection Defense**: Evaluates inputs against adversarial jailbreaks:
  `r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions"`, `r"(?i)you\s+are\s+now\s+dan"`, `r"(?i)system\s+override"`.
* **Shell Injection Defense**: Evaluates shell commands against chained malicious operations:
  `r"[;&|`$]\s*(rm\s+-rf|del\s+/f|format|shutdown|reg\s+delete)"`.

### 2.6. OAuth / 3rd-Party Login
* **Endpoints**: Builds authorization URLs for Google / GitHub OAuth2 grant flows with cryptographic `state` token guards.
* **Code Exchange**: Exchanges authorization code for verified identity claims (`provider_user_id`, `email`, `verified: True`).

---

## 3. Relational & NoSQL Database Subsystem (`database.py`)

### 3.1. Relational Schema Design with PK / FK & Normalization Basics
Architected in Third Normal Form (3NF) to eliminate data redundancy and insertion anomalies:

* **`User` (Entity)**:
  * `id`: Integer Primary Key, Auto-increment.
  * `username`: String(64), Unique, Indexed.
  * `email`: String(128), Unique, Indexed.
  * `password_hash`: String(256), Not Null.
  * `role`: String(32), Default "guest".
  * `created_at`: DateTime UTC.
* **`UserSession` (Entity)**:
  * `id`: Integer Primary Key.
  * `user_id`: Integer, Foreign Key (`users.id`, ondelete="CASCADE"), Indexed.
  * `token`: String(512), Unique, Not Null.
  * `expires_at`: DateTime.
* **`TaskAuditLog` (Entity)**:
  * `id`: Integer Primary Key.
  * `user_id`: Integer, Foreign Key (`users.id`, ondelete="SET NULL").
  * `action_type`: String(64), Not Null.
  * `tool_name`: String(64), Nullable.
  * `status`: String(32) ("SUCCESS", "FAILED", "RETRY").
  * `duration_ms`: Float.
  * `created_at`: DateTime UTC.

### 3.2. Indexing for Query Performance (SQL)
* **Composite Index**: `Index("idx_audit_user_action", "user_id", "action_type")` optimizes timeline filtering.
* **Temporal Index**: `Index("idx_audit_created", "created_at")` optimizes range scans and reverse ordering.

### 3.3. SQL JOINs, Filtering, Ordering & Grouping
* **Relational JOIN**: Inner joins `users` and `task_audit_logs` on `task_audit_logs.user_id == users.id` with `WHERE users.username == ?` and `ORDER BY created_at DESC`.
* **Aggregations & Grouping**:
  ```python
  select(
      TaskAuditLog.tool_name,
      func.count(TaskAuditLog.id).label("total_invocations"),
      func.avg(TaskAuditLog.duration_ms).label("avg_duration_ms")
  ).group_by(TaskAuditLog.tool_name).order_by(func.count(TaskAuditLog.id).desc())
  ```

### 3.4. ORM Usage & Transactions
* **ORM Framework**: SQLAlchemy 2.0 Declarative Mapping with `SessionLocal` scopes.
* **ACID Transactions**:
  ```python
  with session.begin():
      session.add(user)
      session.flush()
      session.add(initial_session)
  # Automatic commit on block exit; automatic rollback upon exception.
  ```

### 3.5. NoSQL Schema Modeling & CRUD Operations (Mongo-style)
* **Storage Model**: Flexible JSON document collections with `_id`, `created_at`, `category`, and nested dictionaries.
* **CRUD API**:
  * `insert_one(document) -> doc_id`: Inserts and persists document.
  * `find(query, limit) -> List[dict]`: Queries with index acceleration.
  * `update_one(query, update_values) -> bool`: Mutates document fields.
  * `delete_one(query) -> bool`: Removes document and updates indexes.
* **Embedding vs Referencing**:
  * Embedded pattern: `{ "title": "Note", "embedded_profile": { "theme": "dark" } }`.
  * Referencing pattern: `{ "title": "Note", "user_ref_id": 42 }`.
* **Aggregation Pipeline Engine**:
  Executes `$match`, `$group` (with `$count` and `$sum`), `$sort`, and `$project` stages.
* **NoSQL Indexing**:
  Maintains in-memory inverted indexes mapping field values to matching document IDs for $O(1)$ lookups.

---

## 4. Multi-Tier Caching Subsystem (`cache.py` & `backend/services/redisService.js`)

* **Redis Client Integration (Node.js & Python)**:
  * Node.js: `backend/services/redisService.js` initializes `createClient({ url: process.env.REDIS_URL })` with auto-reconnect strategy, `client.setEx(key, ttl, value)`, `client.get(key)`, and `client.del(key)`.
  * Python: `cache.py` connects to `redis://` via `redis.from_url` with strict `socket_connect_timeout=0.2s` and fallback.
* **Express Caching Middleware**: Intercepts HTTP requests, serves cached responses with `X-Cache: HIT`, or executes route and caches responses with `X-Cache: MISS`.
* **In-Memory Fallback**: Thread-safe LRU dictionary storing `{"val": Any, "exp": float}` with exact epoch expiration when Redis server is offline.
* **Cache Telemetry**: Tracks hits, misses, hit ratio percentage, and active key counts exposed at `GET /api/v1/cache/telemetry` and `GET /api/v1/cache/stats`.

---

## 5. RESTful API & Server-Side Implementation (`server.py` & `backend/server.js`)

* **Frameworks**: FastAPI (ASGI on port 8000) and Express.js (on port 5000).
* **Status Codes & Semantics**:
  * `200 OK`: Successful retrieval, tool execution, telemetry fetch.
  * `201 Created`: Successful user registration, document insertion, cache set.
  * `400 Bad Request`: Validation failure, prompt injection flagged.
  * `401 Unauthorized`: Missing or expired JWT bearer token.
  * `403 Forbidden`: Insufficient RBAC role permissions.
  * `413 Payload Too Large`: Uploaded file exceeds 10MB limit.
  * `422 Unprocessable Entity`: Request body schema validation error.
  * `429 Too Many Requests`: Client exceeded sliding-window rate limit.
  * `500 Internal Server Error`: Centralized server-side error handling middleware.
* **WebSocket / Real-Time Communication**:
  * Node.js: `backend/services/websocketService.js` creates a native `ws.Server` mounted on `/ws/telemetry`, maintaining connection sets, ping/pong heartbeats (30s), and broadcasting 2s live system metrics.
  * Python: FastAPI `@app.websocket("/ws/telemetry")` streams live hardware pulses at 1Hz.
  * Frontend: `web/src/hooks/useWebSocket.js` custom React hook and `web/src/components/LiveTelemetry.jsx` providing bi-directional full-duplex communication and command dispatching.
* **Server-Side Rendering (SSR)**:
  * React SSR Engine (`backend/ssr/reactSSR.js`): Uses `react-dom/server`'s `renderToString` to pre-render the `ServerHUD` React component tree on the server with injected hydration state (`window.__INITIAL_STATE__`) at `GET /ssr` and `GET /ssr/react`.
  * Express EJS Engine (`backend/views/dashboard.ejs`): Server-rendered templates at `GET /ssr/ejs`.
  * Python Jinja2 Engine (`templates/dashboard.html`): Server-rendered template response via FastAPI `Jinja2Templates` at `GET /ssr/dashboard`.
* **Payment Gateway Integration**:
  * `POST /api/v1/payments/create-checkout`: Creates session ID and checkout URL.
  * `POST /api/v1/payments/webhook`: Validates HMAC-SHA256 signature header and triggers fulfillment.

---

## 6. Frontend & User Interface Architecture (`web/`)

### 6.1. React Component Composition
* **`App.jsx`**: Root container providing navigation bar and client-side view switching.
* **`Dashboard.jsx`**: Orchestrates child components, manages telemetry polling, and coordinates directive submission.
* **`TelemetryCard.jsx`**: Modular card receiving `label`, `value`, `unit`, `colorHex`, and `subtext` via props.
* **`CommandForm.jsx`**: Encapsulates controlled input, form validation, and submit mechanics.
* **`TerminalConsole.jsx`**: Renders event stream with dynamic tag colorization.

### 6.2. State Management & Hooks
* **`useState`**:
  * `telemetry`: CPU, RAM, cache hit ratio, and online status.
  * `logs`: Chronological array of `{ timestamp, tag, message }`.
  * `isLoading`: Boolean controlling transmit button disabling and indicators.
  * `validationError`: Tracks inline form validation failure notices.
  * `networkError`: Captures API connection failure alerts.
* **`useEffect`**:
  * Implements periodic polling loop calling `/api/v1/health` every 3000ms.
  * Implements unmount cleanup canceling intervals (`isMounted = false`).

### 6.3. Form Handling & Controlled Inputs
* Input field strictly bound to `directive` state via `value={directive}` and `onChange={(e) => setDirective(e.target.value)}`.
* Form validation intercepts submissions if input length $< 3$ characters or empty, rendering error UI alerts.

### 6.4. Client-Side Routing
* State-based route manager switching between `"dashboard"` and `"architecture"` views without triggering page reloads.

### 6.5. JavaScript Core Concepts (`web/src/utils/js_concepts.js`)
* **Event Loop**: Demonstrates execution ordering between synchronous call stack, microtasks (`Promise.then`, `queueMicrotask`), and macrotasks (`setTimeout`).
* **Promises vs Callbacks**: Contrasts legacy error-first callbacks with composable Promises.
* **async / await**: Linear asynchronous execution utilizing `try/catch` error boundaries and backoff retries.
* **Closures**: `createTelemetryRecorder` encapsulates private `telemetryHistory` inside lexical scope.
* **Hoisting**: Explains complete hoisting of function declarations versus Temporal Dead Zone (TDZ) for `let`/`const`.

---

## 7. Engineering Practices & Testing Suite (`tests/`)

### 7.1. Writing Unit Tests
* **`test_auth.py`**: Validates PBKDF2 password hashing, salt integrity, JWT generation/decoding, RBAC hierarchies, and rate limiting windows.
* **`test_database.py`**: Validates transactional user creation, SQL JOIN queries, NoSQL CRUD operations, and multi-stage aggregation pipelines.
* **`test_security.py`**: Validates prompt injection pattern detection and dangerous shell syntax sanitization.
* **`test_agent.py`**: Validates local tools, guardrails, LangGraph state machine initialization, and self-correction conditional edges.

### 7.2. Automated API Testing / Integration Tests
* **`test_api.py`**: Uses `fastapi.testclient.TestClient` to execute automated API integration tests verifying:
  * Health endpoint returns `200 OK` with telemetry structure.
  * Missing schema fields return `422 Unprocessable Entity`.
  * Unauthorized requests return `401 Unauthorized`.
  * Valid JWT tokens permit authorized operations.
  * Payment checkout returns valid session structures.
  * SSR endpoint returns dynamic HTML content.

### 7.3. Environment Variables & Secrets Management
* Centrally managed via `.env` and `.env.example`, loaded via `python-dotenv`.
* Secrets (such as `JARVIS_JWT_SECRET`) possess production-grade defaults with explicit override capabilities.

### 7.4. Git Workflow
* **Branching Strategy**: Trunk-based development with short-lived feature branches (`feature/*`, `fix/*`).
* **Semantic Commits**: Adheres to Conventional Commits specification (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
* **Code Review & Quality Gates**: Mandatory pytest execution before merging to `main`.

### 7.5. Containerization with Docker
* **`Dockerfile`**: Multi-stage Linux build installing system audio libraries (`libportaudio2`, `libasound2-dev`, `ffmpeg`), Python dependencies, and healthcheck probing.
* **`docker-compose.yml`**: Multi-container composition linking `jarvis-backend` with `redis` cache container over virtual bridge networks.