"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - MAIN BOOTSTRAPPER
Orchestrates:
  - CustomTkinter Visual UI Dashboard (Main GUI Thread)
  - Async LangGraph Agent with Self-Correction (Dedicated Worker Thread)
  - RealtimeSTT Whisper Streaming on CPU (Audio Listener Thread)
  - Kokoro-82M Text-to-Speech Streaming on CPU (Audio Playback Thread)
  - Thread-Safe queue.Queue Inter-Process Communication
"""

import sys
import queue
import logging
import threading
from typing import Dict, Any

import config
from brain import JarvisBrain
from audio_engine import AudioEngine
from ui_panel import JarvisUIPanel

# Setup Root Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s"
)
logger = logging.getLogger("JarvisMain")


class JarvisEcosystem:
    """
    Core Controller binding Sensory Pipelines, Neural Brain Graph,
    and the Holographic Visual Interface.
    """

    def __init__(self):
        logger.info("Bootstrapping Jarvis Edge-First Graph-Agent Ecosystem...")

        # 1. Thread-Safe Communication Queues
        self.ui_queue: queue.Queue = queue.Queue()
        self.agent_task_queue: queue.Queue = queue.Queue()
        self.is_running = True

        # 2. Initialize Brain Engine with UI Logging Hook
        self.brain = JarvisBrain(log_callback=self.emit_ui_log)

        # 3. Initialize Sensory Pipelines (STT & TTS strictly on CPU)
        self.audio = AudioEngine(
            on_user_speech=self.handle_user_input,
            log_callback=self.emit_ui_log
        )

        # 4. Initialize Visual Dashboard
        self.app = JarvisUIPanel(
            ui_queue=self.ui_queue,
            on_user_submit=self.handle_user_input,
            on_toggle_mute=self.audio.toggle_mute,
            on_system_health_click=self.handle_health_check
        )

        # Intercept window close for clean resource deallocation
        self.app.protocol("WM_DELETE_WINDOW", self.shutdown)

        # 5. Start Dedicated Agent Processing Thread
        self.agent_thread = threading.Thread(
            target=self._agent_worker_loop,
            daemon=True,
            name="JarvisAgentWorker"
        )
        self.agent_thread.start()

    # -------------------------------------------------------------
    # UI LOGGING & STATUS HOOKS
    # -------------------------------------------------------------
    def emit_ui_log(self, tag: str, message: str):
        """Dispatches a log event to the UI thread via thread-safe queue."""
        self.ui_queue.put(("log", (tag, message)))

    def emit_ui_status(self, status_text: str, color_hex: str):
        """Dispatches a status badge update to the UI header."""
        self.ui_queue.put(("status", (status_text, color_hex)))

    # -------------------------------------------------------------
    # USER INPUT INGESTION (VOICE OR TEXT)
    # -------------------------------------------------------------
    def handle_user_input(self, text: str):
        """
        Ingestion point for both spoken audio (from RealtimeSTT)
        and typed commands (from CustomTkinter entry).
        """
        if not text or not text.strip():
            return
        clean_text = text.strip()
        logger.info(f"Ingested prompt: {clean_text}")
        self.agent_task_queue.put(clean_text)

    def handle_health_check(self):
        """Quick trigger for system health telemetry check."""
        self.handle_user_input("Check current system health and hardware diagnostics.")

    # -------------------------------------------------------------
    # AGENT PROCESSING LOOP (ISOLATED WORKER THREAD)
    # -------------------------------------------------------------
    def _agent_worker_loop(self):
        """
        Dedicated worker thread executing the LangGraph state machine.
        Guarantees that heavy LLM reasoning and tool execution never lock the UI.
        """
        logger.info("Agent Worker Thread initialized and listening for tasks.")
        while self.is_running:
            try:
                user_text = self.agent_task_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if user_text == "__SHUTDOWN__":
                break

            try:
                self.emit_ui_status("THINKING...", config.COLOR_CYAN)
                
                # Execute LangGraph Workflow with Self-Correction
                result_state: Dict[str, Any] = self.brain.process_query(user_text)
                final_response = result_state.get("final_response", "Operation completed.")

                # Log final answer to UI terminal
                self.emit_ui_log("JARVIS", final_response)

                # Vocalize answer asynchronously via CPU Kokoro TTS
                self.emit_ui_status("VOCALIZING", config.COLOR_NEON_GREEN)
                self.audio.speak(final_response)

            except Exception as e:
                logger.error(f"Error during agent task execution: {e}", exc_info=True)
                self.emit_ui_log("ERROR", f"Agent execution fault: {str(e)}")
                self.emit_ui_status("FAULT", config.COLOR_ALERT_RED)
            finally:
                self.emit_ui_status("ONLINE : IDLE", config.COLOR_NEON_GREEN)
                self.agent_task_queue.task_done()

    # -------------------------------------------------------------
    # LIFECYCLE MANAGEMENT & RUN
    # -------------------------------------------------------------
    def start(self):
        """Boots sensory pipelines and launches the UI main loop."""
        self.emit_ui_log("SYSTEM", "Starting sensory pipelines (STT & TTS on CPU)...")
        self.audio.start()
        self.emit_ui_log("SYSTEM", "Jarvis Core online. Ready for audio or text directives.")
        
        # Start CustomTkinter GUI mainloop (blocks on main thread until window closed)
        try:
            self.app.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Gracefully halts all worker threads, audio devices, and closes the application."""
        logger.info("Initiating graceful shutdown sequence...")
        self.is_running = False

        # Stop audio sensory pipelines
        try:
            self.audio.stop()
        except Exception as e:
            logger.warning(f"Error stopping audio engine: {e}")

        # Signal agent worker to stop
        self.agent_task_queue.put("__SHUTDOWN__")

        # Destroy UI window safely
        try:
            self.app.destroy()
        except Exception:
            pass

        logger.info("Shutdown sequence complete. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    ecosystem = JarvisEcosystem()
    ecosystem.start()
