# Product Requirements Document (PRD)

## Project Name: J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Subtitle: Edge-First Local Graph-Agent Desktop Ecosystem
**Document Version:** 1.0.0  
**Author:** Mahesh Balaji Nagireddy (@maheshnagireddy3006)  
**Date:** November 2026  
**Status:** Implemented & Validated  

---

## 1. Executive Summary
J.A.R.V.I.S. is a fully localized, privacy-first, edge-computing desktop AI assistant engineered to run entirely on consumer-grade workstation hardware without external cloud API dependencies. Built with an asymmetric hardware allocation strategy, J.A.R.V.I.S. integrates a local Quantized Large Language Model (Llama 3.1 8B via Ollama) accelerated exclusively on an Nvidia RTX 4050 GPU (6GB VRAM budget), while offloading real-time sensory pipelines (RealtimeSTT Whisper speech recognition and Kokoro-82M neural speech synthesis), persistent episodic vector memory (ChromaDB + BGE embeddings), and execution workflows strictly to a multi-core CPU. 

The cognitive architecture is powered by a stateful LangGraph state machine featuring autonomous intent routing, tool execution, and an automated closed-loop self-correction engine capable of analyzing execution stack traces and repairing failed system automation commands without user intervention.

---

## 2. Problem Statement & Motivation
Cloud-based AI assistants (such as Siri, Alexa, Google Assistant, and cloud LLM wrappers) suffer from three critical bottlenecks:
1. **Privacy & Data Security Vulnerabilities**: Streaming audio, desktop actions, and personal context to third-party cloud servers presents substantial data exposure risks.
2. **Network Dependency & Latency Degradation**: Unstable internet connections degrade latency, disabling essential voice and desktop automation during network drops.
3. **Fragile, Linear Execution Pipelines**: Conventional tool-use bots fail catastrophically when a command returns an error code, lacking dynamic reflection, diagnostic reasoning, and autonomous self-correction.

J.A.R.V.I.S. solves these issues by hosting all neural intelligence, sensory perception, vector retrieval, and desktop controls directly on local hardware, bounded by deterministic safety guardrails and autonomous self-healing execution loops.

---

## 3. Product Goals & Non-Goals

### 3.1. Goals
* **100% Offline Capability**: Guarantee zero reliance on external APIs, subscription tokens, or cloud servers for speech-to-text, reasoning, vector storage, and speech synthesis.
* **Asymmetric Hardware Specialization**: Constrain LLM VRAM utilization strictly under 5.0 GB on an Nvidia RTX 4050 (6GB total), dedicating the remaining CPU threads to STT, TTS, embeddings, and UI rendering to avoid Out-Of-Memory (OOM) deadlocks.
* **Autonomous Error Recovery**: Implement self-healing tool execution loops where execution faults are dynamically diagnosed and retried with corrected arguments.
* **Persistent Episodic Memory**: Store and recall user preferences, past interactions, and operational facts across application restarts via local vector embeddings.
* **Modern Holographic HUD**: Deliver a high-performance, non-blocking CustomTkinter desktop interface featuring real-time hardware telemetry and ANSI-formatted terminal stream logging.

### 3.2. Non-Goals
* Cloud sync or remote multi-tenant infrastructure.
* Distributed multi-node clustering.
* Mobile or browser extensions (pure desktop-native architecture).

---

## 4. User Personas

| Persona | Role | Core Need | Key Feature Used |
| :--- | :--- | :--- | :--- |
| **Alex (Developer / Power User)** | Software Engineer | Fast hands-free OS control, local file search, command execution without cloud tracking. | RealtimeSTT voice commands, LocalTools shell execution, system health telemetry. |
| **Sarah (Privacy Advocate)** | Data Analyst | A conversational desktop assistant that retains personal context locally without transmitting logs to external vendors. | ChromaDB episodic memory, local Llama 3.1 8B inference via Ollama. |
| **David (Accessibility User)** | Content Creator | Low-latency voice interaction and high-fidelity vocal responses without stutter or GUI freezing. | Kokoro-82M zero-latency CPU synthesis, CustomTkinter holographic HUD. |

---

## 5. Functional Requirements (FR)

### FR1: Edge-First Local LLM Brain
* **FR1.1**: The system must interface with a local Ollama server over a low-latency HTTP REST socket (`http://localhost:11434`).
* **FR1.2**: Default model must be quantized `llama3.1:8b` (4-bit quantization, Q4_K_M) consuming $\le 4.9\text{ GB}$ VRAM.
* **FR1.3**: Inference temperature must default to $0.2$ for deterministic intent classification and tool execution.

### FR2: Continuous Low-Latency Speech-to-Text (STT)
* **FR2.1**: Audio capture must run in a dedicated background worker utilizing `RealtimeSTT` with `faster-whisper`.
* **FR2.2**: The transcription model must be `base.en` with `int8` quantization running exclusively on the CPU.
* **FR2.3**: Must include Silero VAD (Voice Activity Detection) with configurable sensitivity ($0.4$) and post-speech silence window ($1.0\text{s}$) to avoid cutting off sentences.
* **FR2.4**: Continuous listening mode must route transcribed text directly to the agent input pipeline without requiring cloud wake-word servers.

### FR3: Zero-Latency Neural Text-to-Speech (TTS)
* **FR3.1**: Speech synthesis must utilize `Kokoro-82M` via `KPipeline` on CPU with sample rate $24\text{kHz}$ and American English voice `af_heart`.
* **FR3.2**: Audio playback must occur in an isolated asynchronous worker thread using `sounddevice` to prevent blocking the GUI.
* **FR3.3**: Must provide an automatic offline fallback to `pyttsx3` if neural weights or dependencies are unavailable.

### FR4: Stateful Autonomous Graph Agent with Self-Correction
* **FR4.1**: State orchestration must be managed via `LangGraph` using a typed state structure (`JarvisState`).
* **FR4.2**: The agent must classify incoming prompts into three operational intents:
  1. `automation`: Invoking system tools (`get_system_health`, `launch_application`, `execute_shell_command`, `search_local_files`).
  2. `memory_query`: Retrieving contextual records from vector storage.
  3. `conversation`: Standard reasoning, conversational Q&A, and dialogue.
* **FR4.3**: Tool execution must catch execution errors and route to an `error_recovery` node.
* **FR4.4**: The self-correction loop must analyze error tracebacks using Llama 3.1 8B and formulate corrected arguments, supporting up to $2$ automated retries (`MAX_SELF_CORRECTION_RETRIES = 2`).

### FR5: Persistent Vector Memory Subsystem
* **FR5.1**: Epistemic and conversational memory must be persisted using a local `ChromaDB` client saved in `data/chroma`.
* **FR5.2**: Embeddings must be generated using `BAAI/bge-small-en-v1.5` ($384$-dimensional vectors, $\approx 133\text{MB}$ memory footprint) strictly bound to CPU.
* **FR5.3**: Semantic search must retrieve top-$K$ ($K=3$) relevant memories and format them into contextual system prompts.
* **FR5.4**: Meaningful user statements ($>10$ characters) must automatically persist into the memory collection.

### FR6: Local Edge Automation Tools
* **FR6.1**: **System Health Monitoring**: Provide CPU usage, physical/logical core counts, virtual memory metrics, per-partition disk metrics, and battery state via `psutil`.
* **FR6.2**: **Application Launcher**: Launch common desktop applications (`notepad`, `calculator`, `terminal`, `chrome`, `edge`, `code`, `explorer`) or file paths via OS subprocesses.
* **FR6.3**: **Sandboxed Shell Execution**: Execute PowerShell commands with non-interactive execution, UTF-8 output decoding, a 15-second execution timeout, and destructive command filters (blocking `format`, `del /f /s /q c:`, etc.).
* **FR6.4**: **File Search**: Recursively traverse local project directories matching glob patterns with capped result counts.

### FR7: Futuristic Dark Sci-Fi HUD Interface
* **FR7.1**: The user interface must be built in `CustomTkinter` in Dark Mode with a holographic cyan and slate palette.
* **FR7.2**: Must display real-time live telemetry: CPU load gauge, RAM percentage, Ollama status badge, and Microphone status indicator updated at $1\text{Hz}$.
* **FR7.3**: Main console must display timestamped, color-tagged event logs (`[JARVIS]`, `[ROUTER]`, `[TOOL]`, `[RETRY]`, `[ERROR]`, `[MIC]`).
* **FR7.4**: UI must support keyboard input (`<Return>`), dedicated vocal mute toggling, quick system health execution, and clear screen controls.

---

## 6. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Validation Metric |
| :--- | :--- | :--- | :--- |
| **NFR1** | **Privacy** | 100% of telemetry, speech, LLM inference, and memory queries remain on local machine. | 0 outbound network requests during voice interaction and tool execution (excluding local loopback). |
| **NFR2** | **Resource Budget** | LLM VRAM utilization must not exceed 5.0 GB on 6GB RTX 4050; CPU usage bounded to designated thread allocation. | VRAM consumption $\le 5.0\text{ GB}$; CPU thread pool $\le 8$ threads. |
| **NFR3** | **Latency** | STT transcription delay $<1.2\text{s}$; TTS synthesis initiation $<0.6\text{s}$; LLM Time-to-First-Token (TTFT) $<0.8\text{s}$. | End-to-end voice query response $\le 2.5\text{s}$ for short conversational turns. |
| **NFR4** | **Stability** | Multi-threaded decoupling ensures the GUI maintains 60 FPS refresh without freezing during LLM inference or audio generation. | Tkinter mainloop latency $<16\text{ms}$; 0 unresponsive window warnings. |
| **NFR5** | **Safety** | Guardrails intercept dangerous or catastrophic system destruction commands. | Forbidden shell regex blocks destructive disk formatting or recursive Windows drive deletion. |

---

## 7. System Hardware & Environment Profile
* **Target OS**: Windows 11 (x64)
* **Processor (CPU)**: Intel Core i5-13450HX (10 Cores, 16 Threads) — allocated for STT, TTS, Embeddings, Orchestration.
* **Graphics (GPU)**: Nvidia GeForce RTX 4050 Laptop GPU (6GB Dedicated GDDR6 VRAM) — reserved exclusively for Ollama LLM.
* **System Memory (RAM)**: 24GB DDR5.
* **Python Runtime**: Python 3.12 (Virtual Environment: `jarvis_env`).

---

## 8. Success Metrics & Verification Criteria
* **Validation Check Compliance**: 100% pass on repository validity, original authorship, PRD, HLD, and LLD checks.
* **Autonomous Error Recovery Rate**: $\ge 80\%$ recovery on repairable shell and file-path command errors within 2 retries.
* **Vector Semantic Accuracy**: Top-3 retrieval precision $\ge 90\%$ for stored user facts and session preferences.
* **Zero Thread Deadlocks**: Continuous 1-hour operation with active microphone recording and continuous speech queries without process crash.