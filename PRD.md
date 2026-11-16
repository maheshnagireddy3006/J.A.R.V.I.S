# Product Requirements Document (PRD)

## Project Name: J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Subtitle: Edge-First Local Graph-Agent & Microservices Ecosystem
**Document Version:** 2.0.0  
**Author:** Mahesh Balaji Nagireddy (@maheshnagireddy3006)  
**Date:** November 2026  
**Status:** Fully Implemented & Validated  

---

## 1. Problem Modeling
Modern digital assistants and cloud-based AI tools pose severe limitations:
1. **Privacy Insecurity**: Sending microphone audio, system logs, personal data, and operational files to third-party cloud servers compromises enterprise and personal confidentiality.
2. **Network Fragility & Latency**: Latency spikes, rate limits, and outages render cloud assistants unavailable during intermittent connectivity.
3. **Monolithic & Fragile Automations**: Traditional tool execution frameworks lack self-healing capabilities, failing when OS commands or file paths experience runtime errors.
4. **Disjointed Ecosystems**: Users typically juggle disparate tools for voice control, desktop monitoring, RESTful microservices, real-time data streaming, and web dashboards.

**J.A.R.V.I.S.** addresses this problem space through an edge-first, asymmetric hardware paradigm. It bundles stateful multi-step agent reasoning (`LangGraph`), continuous local speech processing (`RealtimeSTT` & `Kokoro-82M`), persistent vector memory (`ChromaDB`), relational and document storage (`SQLAlchemy` & `Mongo-style Document Store`), real-time streaming microservices (`FastAPI` & `WebSockets`), and a responsive web dashboard (`React`).

---

## 2. Executive Summary & Product Vision
J.A.R.V.I.S. is an edge-first AI workstation operating system. The system runs 100% locally on workstation hardware (Intel Core i5-13450HX CPU + Nvidia RTX 4050 6GB GPU). By isolating VRAM exclusively for a quantized large language model (`Llama 3.1 8B` via `Ollama`), J.A.R.V.I.S. prevents out-of-memory thrashing while offloading sensory perception, vector retrieval, and microservices to multi-core CPU threads.

---

## 3. Product Goals & Scope

### 3.1. Goals
* **Complete Edge Independence**: Zero cloud token dependencies for core inference, speech-to-text, speech synthesis, and vector memory.
* **Autonomous Error Self-Correction**: When an automation tool fails, the agent intercepts the stack trace, diagnoses the root cause, and retries with repaired arguments.
* **Unified Microservices & Web Tier**: Expose high-throughput RESTful endpoints, real-time WebSockets, Server-Side Rendering (SSR), and a responsive React client.
* **Dual Database Architecture**: Combine ACID relational schema modeling (users, sessions, task audit logs) with flexible NoSQL document storage (metadata, notes, aggregation pipelines).
* **Enterprise Security Standards**: Implement salted PBKDF2/bcrypt password hashing, JWT authentication, sliding-window rate limiting, RBAC authorization, and prompt injection sanitization.

### 3.2. Non-Goals
* Cloud-hosted subscription multi-tenancy.
* Cross-device mobile sync.

---

## 4. Target User Personas

| Persona | Role | Primary Need | Key Feature Utilized |
| :--- | :--- | :--- | :--- |
| **Alex (Software Architect)** | Tech Lead | High-throughput local REST API, automated task execution, and system diagnostics. | RESTful API, LocalTools, multi-step agent self-correction. |
| **Sarah (Security Officer)** | Compliance Analyst | 100% private desktop intelligence without outbound network leakage. | Local Ollama inference, JWT auth, RBAC, input sanitization. |
| **David (Accessibility User)** | Creator | Zero-latency voice-to-voice interaction and live status visualization. | RealtimeSTT (Whisper on CPU), Kokoro-82M TTS, Web HUD. |

---

## 5. Functional Requirements (FR)

### Module A: AI App Engineering
* **FR-AI-01: Multi-Step Agent**: The cognitive engine must use LangGraph state machines with cyclic conditional routing (`intent_router` $\rightarrow$ `tool_executor` $\leftrightarrow$ `error_recovery` $\rightarrow$ `response_generator`).
* **FR-AI-02: LLM API Integration**: Interface with local Ollama daemon over low-latency HTTP sockets (`http://localhost:11434`), supporting temperature tuning, timeouts, and streaming.
* **FR-AI-03: Function Calling / Tool Use**: Support deterministic execution of `get_system_health`, `launch_application`, `execute_shell_command`, and `search_local_files`.
* **FR-AI-04: Structured Outputs**: Intent router and self-correction nodes must enforce strict JSON output schemas, guarded by regex fallback parsing.
* **FR-AI-05: Prompt Engineering**: Implement role-conditioned system prompts, context-augmented formatting, and voice-readiness constraints.
* **FR-AI-06: RAG — Embeddings & Vector Retrieval**: Persist epistemic memory in ChromaDB using `BAAI/bge-small-en-v1.5` embeddings on CPU, querying top-3 semantic records.
* **FR-AI-07: Streaming Responses**: Stream token chunks via Server-Sent Events (SSE) and WebSockets for real-time vocal and UI rendering.
* **FR-AI-08: LLM Eval Sets**: Provide automated evaluation suites assessing intent classification accuracy, tool precision, and latency benchmarks.
* **FR-AI-09: Token & Cost Monitoring**: Track cumulative prompt/completion tokens, compute inference latency, and calculate local GPU cost savings.
* **FR-AI-10: Prompt Injection Awareness & Defenses**: Filter adversarial jailbreaks, system override strings, and privilege escalation attempts before inference.

### Module B: Backend & System Design
* **FR-BE-01: RESTful Endpoint Design**: Clean resource-oriented API routes (`/api/v1/health`, `/api/v1/agent/query`, `/api/v1/auth/*`, `/api/v1/documents`, `/api/v1/files/upload`).
* **FR-BE-02: HTTP Status Codes Used Correctly**: Deterministic usage of 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 413 Payload Too Large, 422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Error.
* **FR-BE-03: Server-Side Error Handling**: Global custom exception handlers translating unhandled exceptions to RFC 7807 compliant problem JSON structures.
* **FR-BE-04: Middleware**: Implement custom ASGI middleware for sliding-window rate limiting, request latency timing headers (`X-Process-Time-Ms`), structured logging, and CORS.
* **FR-BE-05: Request Body Validation**: Strict Pydantic models validating all payload fields, data types, string lengths, and email formats.
* **FR-BE-06: File Upload Handling**: Multipart upload endpoint enforcing MIME checking, extension whitelisting, 10MB size capping, and atomic persistence.
* **FR-BE-07: Backend Deployment**: Support production deployments via multi-worker Uvicorn, Systemd daemon, and Docker containers.

### Module C: Authentication & Security
* **FR-SEC-01: Password Hashing**: Cryptographic password storage using salted PBKDF2-HMAC-SHA256 with 100,000 iterations and random salt generation.
* **FR-SEC-02: JWT Issuance & Verification**: Generate and verify signed HMAC-SHA256 bearer tokens with 120-minute expiration windows.
* **FR-SEC-03: Role-Based Authorization Checks (RBAC)**: Enforce hierarchical permissions (`admin` > `operator` > `guest`) via dependency injection.
* **FR-SEC-04: Rate Limiting**: In-memory sliding window rate limiter restricting clients to 100 requests per minute.
* **FR-SEC-05: Input Sanitization & Injection Awareness**: Intercept dangerous shell commands (`rm -rf`, `format`, `del /f`) and SQL/prompt injection vectors.
* **FR-SEC-06: OAuth / 3rd-Party Login**: Simulate OAuth 2.0 authorization code flow for Google and GitHub identity verification.

### Module D: Databases (SQL & NoSQL)
* **FR-DB-01: Relational Schema Design with PK/FK**: 3NF normalized schema featuring `users`, `user_sessions`, and `task_audit_logs`.
* **FR-DB-02: SQL JOINs**: Multi-table inner joins correlating user identity with execution audit records.
* **FR-DB-03: Indexing for Query Performance (SQL)**: Composite B-Tree indexes on `(user_id, action_type)` and `created_at`.
* **FR-DB-04: Filtering, Ordering, Grouping**: Complex SQL queries utilizing `WHERE`, `ORDER BY created_at DESC`, `GROUP BY tool_name`, and aggregations (`COUNT`, `AVG`).
* **FR-DB-05: Normalization Basics**: Eliminate update and deletion anomalies via Third Normal Form relational decomposition.
* **FR-DB-06: ORM Usage**: Declarative models, relationship mapping, and session scopes via SQLAlchemy.
* **FR-DB-07: Transactions**: ACID transactional boundaries with explicit commit and rollback handling.
* **FR-DB-08: Schema Modeling (Mongo)**: Document-oriented collection with flexible JSON document structures.
* **FR-DB-09: CRUD Operations (Mongo)**: Support `insert_one`, `find`, `update_one`, and `delete_one`.
* **FR-DB-10: Embedding vs Referencing Relationships**: Support embedded sub-documents (e.g. user preferences) alongside foreign key references.
* **FR-DB-11: Aggregation Pipelines**: Multi-stage document transformation pipeline supporting `$match`, `$group`, `$sort`, and `$project`.
* **FR-DB-12: Indexing for Query Performance (Mongo)**: In-memory inverted indexes accelerating single-field and tag lookups.

### Module E: Frontend & User Interface
* **FR-FE-01: React Component Composition**: Modular UI hierarchy (`App` $\rightarrow$ `Dashboard` $\rightarrow$ `TelemetryCard`, `CommandForm`, `TerminalConsole`).
* **FR-FE-02: State Management with useState**: Manage active telemetry metrics, event logs, form input, and loading states.
* **FR-FE-03: Side Effects with useEffect**: Manage periodic API polling, WebSocket listeners, and clean unmount teardown.
* **FR-FE-04: Async Data Fetching from API**: Asynchronous HTTP consumption using `fetch` with `async/await` and retry logic.
* **FR-FE-05: Client-Side Routing**: State-based view transitions between Live Dashboard and Architecture Specification views.
* **FR-FE-06: Loading & Error UI States**: Disabled inputs, processing indicators, error alert banners, and connection pills.
* **FR-FE-07: Form Handling — Controlled Inputs**: Bidirectional data binding with `value` and `onChange` handlers.
* **FR-FE-08: Form Validation**: Pre-submission character checks, length constraints, and inline validation messages.
* **FR-FE-09: Responsive Layout & Styling Competence**: Modern dark sci-fi aesthetic, CSS flexbox, responsive media wrappers.
* **FR-FE-10: Frontend Deployment**: Vite production bundling with minified static asset distribution.
* **FR-FE-11: JavaScript Concepts**: Documented implementations of Event Loop, Promises vs Callbacks, async/await, Closures, and Hoisting.

### Module F: System & Integration
* **FR-SYS-01: Caching with Redis**: Multi-tier caching connecting to remote Redis with in-memory TTL LRU fallback.
* **FR-SYS-02: WebSocket / Real-Time Communication**: Bidirectional `/ws/telemetry` socket streaming metrics at 1Hz.
* **FR-SYS-03: Scheduled Jobs / Cron**: Background recurring tasks performing vector maintenance and cache eviction.
* **FR-SYS-04: 3rd-Party API Integration**: External REST lookup to Open-Meteo weather API with offline fallback.
* **FR-SYS-05: Server-Side Rendering (SSR)**: Dynamic server-rendered HTML dashboard via Jinja2 templates.
* **FR-SYS-06: Payment Gateway Integration**: Stripe/Razorpay checkout session creation and HMAC webhook verification.

### Module G: Engineering Practices
* **FR-ENG-01: Git Workflow**: Documented Git flow, feature branch model, and semantic commit conventions.
* **FR-ENG-02: Environment Variables & Secrets Management**: Strict `.env` and `.env.example` configurations.
* **FR-ENG-03: Writing Unit Tests**: Comprehensive unit test suite covering auth, database, security, and agent graph.
* **FR-ENG-04: Automated API Testing / Integration Tests**: Automated API test suite verifying status codes and validation.
* **FR-ENG-05: Containerization with Docker**: Multi-stage `Dockerfile` and `docker-compose.yml` service orchestration.

---

## 6. Non-Functional Requirements (NFR)

* **NFR-01: Privacy & Zero-Cloud Leakage**: 100% of speech audio, vector queries, and reasoning remain local.
* **NFR-02: Hardware Resource Budget**: VRAM usage $\le 4.9\text{ GB}$ on Nvidia RTX 4050 6GB; CPU threads $\le 8$.
* **NFR-03: Latency Benchmarks**: STT transcription $<1.2\text{s}$; TTS synthesis initiation $<0.6\text{s}$; API latency $<50\text{ms}$.
* **NFR-04: High Availability**: Decoupled multi-threading prevents GUI and API lockups during heavy inference.
* **NFR-05: Test Coverage**: $\ge 90\%$ test pass rate across unit, integration, and security test suites.