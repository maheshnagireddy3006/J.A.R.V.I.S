"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - SENSORY PIPELINES (AUDIO ENGINE)
Hardware Profile:
  - Speech-to-Text (STT): RealtimeSTT with Whisper-base on CPU (int8 quantized)
  - Text-to-Speech (TTS): Kokoro-82M via KPipeline on CPU (Sample Rate: 24kHz)
  - Execution: Completely isolated from GPU to preserve 100% of 6GB VRAM for Ollama LLM.
"""

import os
import time
import queue
import logging
import threading
import numpy as np
from typing import Optional, Callable, Any

import config

logger = logging.getLogger("JarvisAudio")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# =====================================================================
# 1. KOKORO-82M ZERO-LATENCY TEXT-TO-SPEECH (CPU PIPELINE)
# =====================================================================
class KokoroTTS:
    """
    Rapid, zero-latency streaming Text-to-Speech using Kokoro-82M on CPU.
    Utilizes an isolated playback queue to prevent voice stutter or UI freezing.
    """

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        self.log_callback = log_callback or (lambda tag, msg: logger.info(f"[{tag}] {msg}"))
        self.speech_queue: queue.Queue[str] = queue.Queue()
        self.is_running = False
        self.pipeline = None
        self.fallback_engine = None
        self._worker_thread: Optional[threading.Thread] = None

        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initializes Kokoro-82M on CPU, or configures lightweight fallback if unavailable."""
        self.log_callback("SYSTEM", f"Loading Kokoro-82M on CPU (Voice: {config.TTS_VOICE})...")
        try:
            from kokoro import KPipeline
            # Explicitly bind to CPU
            self.pipeline = KPipeline(lang_code=config.TTS_LANG_CODE, device=config.DEVICE_AUDIO)
            self.log_callback("SYSTEM", "Kokoro-82M TTS Pipeline ready on CPU.")
        except Exception as e:
            self.log_callback("WARN", f"Kokoro initialization deferred/unavailable: {e}. Checking pyttsx3 fallback...")
            try:
                import pyttsx3  # type: ignore
                self.fallback_engine = pyttsx3.init()
                self.fallback_engine.setProperty("rate", 185)
                self.log_callback("SYSTEM", "Pyttsx3 offline fallback TTS initialized.")
            except Exception as fe:
                self.log_callback("WARN", f"TTS fallback unavailable: {fe}. Audio output will be muted.")

    def start(self):
        """Starts the background audio synthesis and playback thread."""
        if self.is_running:
            return
        self.is_running = True
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True, name="JarvisTTSWorker")
        self._worker_thread.start()

    def stop(self):
        """Stops the speech playback thread."""
        self.is_running = False
        self.speech_queue.put("__STOP__")

    def speak(self, text: str):
        """Enqueues text for asynchronous vocalization."""
        if not text or not text.strip():
            return
        self.speech_queue.put(text.strip())

    def _speech_worker(self):
        """Worker thread consuming speech requests and streaming audio output."""
        while self.is_running:
            try:
                text = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if text == "__STOP__":
                break

            try:
                self.log_callback("SPEAK", f"Vocalizing: '{text[:50]}...'")
                self._synthesize_and_play(text)
            except Exception as e:
                self.log_callback("ERROR", f"Audio vocalization error: {e}")
            finally:
                self.speech_queue.task_done()

    def _synthesize_and_play(self, text: str):
        """Synthesizes text with Kokoro and streams to sounddevice."""
        if self.pipeline is not None:
            try:
                import sounddevice as sd
                # Kokoro generator yields (graphemes, phonemes, audio_tensor)
                generator = self.pipeline(
                    text,
                    voice=config.TTS_VOICE,
                    speed=config.TTS_SPEED,
                    split_pattern=r'\n+'
                )

                for _, _, audio in generator:
                    if not self.is_running:
                        break
                    if audio is not None:
                        # Convert torch tensor or numpy array to float32 ndarray
                        audio_obj: Any = audio
                        if hasattr(audio_obj, "numpy"):
                            audio_data = audio_obj.numpy()
                        else:
                            audio_data = np.array(audio_obj, dtype=np.float32)

                        # Play audio segment synchronously in this dedicated worker thread
                        sd.play(audio_data, samplerate=config.TTS_SAMPLE_RATE)
                        sd.wait()
                return
            except Exception as e:
                self.log_callback("WARN", f"Kokoro streaming failed: {e}. Attempting fallback...")

        # Fallback to pyttsx3 if Kokoro failed or was not initialized
        if self.fallback_engine is not None:
            try:
                self.fallback_engine.say(text)
                self.fallback_engine.runAndWait()
            except Exception as fe:
                self.log_callback("ERROR", f"Fallback TTS error: {fe}")


# =====================================================================
# 2. REALTIME-STT WHISPER-BASE STREAMING (CPU INT8 PIPELINE)
# =====================================================================
class RealtimeSTTListener:
    """
    Streaming Speech-to-Text utilizing RealtimeSTT and Whisper-base.
    Runs completely on CPU with int8 quantization to prevent VRAM competition.
    """

    def __init__(
        self,
        on_transcription: Callable[[str], None],
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.on_transcription = on_transcription
        self.log_callback = log_callback or (lambda tag, msg: logger.info(f"[{tag}] {msg}"))
        self.recorder = None
        self.is_running = False
        self.is_muted = False
        self._listener_thread: Optional[threading.Thread] = None

        self._initialize_recorder()

    def _initialize_recorder(self):
        """Initializes RealtimeSTT AudioToTextRecorder on CPU."""
        self.log_callback("SYSTEM", f"Configuring RealtimeSTT (Whisper '{config.STT_MODEL_SIZE}' on CPU-int8)...")
        try:
            from RealtimeSTT.audio_recorder import AudioToTextRecorder
            self.recorder = AudioToTextRecorder(
                model=config.STT_MODEL_SIZE,
                device=config.STT_DEVICE,
                compute_type=config.STT_COMPUTE_TYPE,
                post_speech_silence_duration=config.STT_POST_SPEECH_SILENCE,
                silero_sensitivity=0.4,
                wake_words="",  # Continuous listening mode
                spinner=False,
                level=logging.WARNING
            )
            self.log_callback("SYSTEM", "RealtimeSTT Whisper Engine online.")
        except Exception as e:
            self.log_callback("WARN", f"RealtimeSTT initialization deferred/unavailable: {e}")
            self.log_callback("WARN", "Jarvis will accept manual text input via UI dashboard.")
            self.recorder = None

    def start(self):
        """Starts the background listening loop."""
        if self.is_running or self.recorder is None:
            return
        self.is_running = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True, name="JarvisSTTWorker")
        self._listener_thread.start()

    def stop(self):
        """Stops the listening loop and releases the microphone."""
        self.is_running = False
        if self.recorder is not None:
            try:
                self.recorder.stop()
            except Exception:
                pass

    def toggle_mute(self) -> bool:
        """Toggles microphone mute state."""
        self.is_muted = not self.is_muted
        status = "MUTED" if self.is_muted else "UNMUTED"
        self.log_callback("SYSTEM", f"Microphone {status}.")
        return self.is_muted

    def _listen_loop(self):
        """Continuous polling loop capturing transcribed sentences."""
        self.log_callback("AUDIO", "Microphone listening stream active.")
        while self.is_running:
            try:
                if self.recorder and not self.is_muted:
                    text = self.recorder.text()
                    if text and text.strip() and not self.is_muted:
                        clean_text = text.strip()
                        self.log_callback("MIC", f"Transcribed speech: '{clean_text}'")
                        self.on_transcription(clean_text)
                else:
                    time.sleep(0.2)
            except Exception as e:
                self.log_callback("ERROR", f"Speech recognition loop error: {e}")
                time.sleep(0.5)


# =====================================================================
# 3. HIGH-LEVEL AUDIO ENGINE COORDINATOR
# =====================================================================
class AudioEngine:
    """Coordinates both STT and TTS sensory pipelines."""

    def __init__(
        self,
        on_user_speech: Callable[[str], None],
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.tts = KokoroTTS(log_callback=log_callback)
        self.stt = RealtimeSTTListener(on_transcription=on_user_speech, log_callback=log_callback)

    def start(self):
        """Boots both audio workers."""
        self.tts.start()
        self.stt.start()

    def stop(self):
        """Shuts down both audio workers."""
        self.stt.stop()
        self.tts.stop()

    def speak(self, text: str):
        """Speaks text asynchronously."""
        self.tts.speak(text)

    def toggle_mute(self) -> bool:
        """Toggles microphone mute."""
        return self.stt.toggle_mute()
