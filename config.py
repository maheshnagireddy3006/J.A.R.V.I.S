"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - SYSTEM CONFIGURATION
Hardware Profile:
  - GPU: Nvidia RTX 4050 (6GB Dedicated VRAM) -> Reserved exclusively for Ollama LLM (~4.8GB max)
  - CPU: Intel i5-13450HX (10 Cores / 16 Threads) -> Dedicated to STT, TTS, Embeddings & Orchestration
  - RAM: 24GB System Memory
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Environment variables & secrets management
# Automatically loads secrets from .env into runtime environment
load_dotenv()


# ==========================================
# 1. CORE DIRECTORIES & PATHS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma"
LOGS_DIR = DATA_DIR / "logs"

# Ensure runtime directories exist
for directory in [DATA_DIR, CHROMA_PERSIST_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. HARDWARE & THREAD ALLOCATION
# ==========================================
# Hardware binding constraints
DEVICE_LLM = "cuda"       # Served via Ollama external server with GPU acceleration
DEVICE_AUDIO = "cpu"     # Strictly isolated to 10-core CPU to preserve 6GB VRAM
DEVICE_EMBED = "cpu"     # Strictly isolated to CPU

# CPU thread allocation for torch / ONNX / Whisper
CPU_NUM_THREADS = 8
os.environ["OMP_NUM_THREADS"] = str(CPU_NUM_THREADS)
os.environ["MKL_NUM_THREADS"] = str(CPU_NUM_THREADS)
os.environ["TORCH_NUM_THREADS"] = str(CPU_NUM_THREADS)

# ==========================================
# 3. LLM BRAIN (OLLAMA ENGINE)
# ==========================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Default to quantized Llama 3.1 8B (Q4_K_M)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = 60.0
OLLAMA_TEMPERATURE = 0.2
MAX_SELF_CORRECTION_RETRIES = 2

# ==========================================
# 4. MEMORY SUBSYSTEM (CHROMADB & EMBEDDINGS)
# ==========================================
CHROMA_COLLECTION_NAME = "jarvis_episodic_memory"
# CPU-bound high-efficiency embedding model (~133MB footprint)
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
MEMORY_QUERY_TOP_K = 3

# ==========================================
# 5. SENSORY PIPELINES (STT & TTS)
# ==========================================
# Speech-to-Text: RealtimeSTT (Whisper-base on CPU with int8 quantization)
STT_MODEL_SIZE = "base.en"
STT_DEVICE = "cpu"
STT_COMPUTE_TYPE = "int8"
STT_POST_SPEECH_SILENCE = 1.0  # Seconds of silence before finalizing sentence
STT_ENERGY_THRESHOLD = 800

# Text-to-Speech: Kokoro-82M (Rapid zero-latency CPU synthesis)
TTS_MODEL_ID = "hexgrad/Kokoro-82M"
TTS_VOICE = "af_heart"
TTS_LANG_CODE = "a"  # American English
TTS_SPEED = 1.0
TTS_SAMPLE_RATE = 24000

# ==========================================
# 6. VISUAL UI (CUSTOMTKINTER SCI-FI PALETTE)
# ==========================================
UI_TITLE = "JARVIS // EDGE-FIRST GRAPH-AGENT ECOSYSTEM"
UI_GEOMETRY = "1180x760"

# Holographic Dark Sci-Fi Aesthetic Tokens
COLOR_BG = "#070b12"           # Deep space black
COLOR_PANEL_BG = "#0b1220"     # Slate cockpit panel
COLOR_PANEL_BORDER = "#162540" # Subtle structural line
COLOR_CYAN = "#00e5ff"         # Primary holographic cyan
COLOR_CYAN_DIM = "#007a8a"     # Secondary dimmed cyan
COLOR_NEON_GREEN = "#00ff88"   # Status: Active / Tool Success
COLOR_ALERT_RED = "#ff2255"    # Status: Error / Fault
COLOR_WARN_AMBER = "#ffaa00"   # Status: Self-Correction / Retrying
COLOR_TEXT_PRIMARY = "#e2e8f0" # Clear contrast text
COLOR_TEXT_SECONDARY = "#64748b" # Telemetry label text
COLOR_ACCENT_BG = "#0f1c30"    # Widget highlighted surface

FONT_FAMILY_MONO = "Consolas"
FONT_FAMILY_TITLE = "Segoe UI"
