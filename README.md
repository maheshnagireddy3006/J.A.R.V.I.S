# J.A.R.V.I.S. // Edge-First Local Graph-Agent Ecosystem

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/framework-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/llm-Ollama%20(Llama%203.1%208B)-purple.svg)](https://ollama.com/)
[![ChromaDB](https://img.shields.io/badge/memory-ChromaDB-green.svg)](https://www.trychroma.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An ultra-capable, 100% localized, edge-first AI desktop ecosystem designed for Windows 11 workstations. Built with an asymmetric compute allocation strategy: discrete GPU exclusively for local LLM reasoning and multi-threaded CPU for speech recognition, neural voice synthesis, vector embeddings, and OS automation.

---

## Key Features

- **Edge-First Neural Brain**: Powered by local `llama3.1:8b` via Ollama on an Nvidia RTX 4050 GPU (strictly bounded $\le 4.9\text{ GB}$ VRAM). Zero cloud dependencies, zero subscription APIs, 100% private.
- **Autonomous Self-Correction**: Implemented with LangGraph. When a host system automation tool encounters an error, the agent automatically diagnoses the stack trace and retries with corrected arguments.
- **Continuous Speech-to-Text (STT)**: RealtimeSTT with Whisper `base.en` (int8 quantized) running entirely on CPU with Silero Voice Activity Detection (VAD).
- **Neural Text-to-Speech (TTS)**: Zero-latency voice synthesis via Kokoro-82M ($24\text{kHz}$) on CPU, with automatic fallback to Windows SAPI `pyttsx3`.
- **Persistent Episodic Memory**: Local ChromaDB vector database with `BAAI/bge-small-en-v1.5` embeddings on CPU for cross-session recall.
- **Futuristic Dark Sci-Fi HUD**: Built with CustomTkinter featuring live CPU/RAM telemetry, active peripheral indicators, and real-time color-tagged terminal logs.

---

## Engineering Documentation

- [Product Requirements Document (PRD.md)](PRD.md)
- [High-Level Design (HLD.md)](HLD.md)
- [Low-Level Design (LLD.md)](LLD.md)

---

## Hardware Profile & Resource Allocation

| Subsystem | Hardware Target | Compute Constraints |
| :--- | :--- | :--- |
| **LLM Inference** | Nvidia RTX 4050 Laptop GPU (6GB) | $\le 4.9\text{ GB}$ Dedicated VRAM |
| **STT Pipeline** | Intel Core i5-13450HX CPU | Whisper `base.en` (int8) |
| **TTS Pipeline** | Intel Core i5-13450HX CPU | Kokoro-82M (`af_heart`) |
| **Vector Embeddings** | Intel Core i5-13450HX CPU | BGE-small-en-v1.5 (384-dim) |
| **HUD Dashboard** | Intel Core i5-13450HX CPU | CustomTkinter (Non-blocking) |

---

## Quick Start

### 1. Prerequisites
- Windows 11 (x64)
- Python 3.12
- [Ollama](https://ollama.com/) installed with `llama3.1:8b` pulled:
  ```bash
  ollama pull llama3.1:8b
  ```

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/maheshnagireddy3006/J.A.R.V.I.S.git
cd J.A.R.V.I.S

# Create and activate virtual environment
python -m venv jarvis_env
.\jarvis_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching JARVIS
Ensure Ollama is running (`ollama serve`), then execute:
```bash
run_jarvis.bat
```
or run directly via Python:
```bash
python main.py
```

---

## License
MIT License. Created by [Mahesh Balaji Nagireddy](https://github.com/maheshnagireddy3006).