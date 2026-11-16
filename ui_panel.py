"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - VISUAL UI DASHBOARD
Framework: CustomTkinter (Futuristic Dark Sci-Fi Aesthetic)
Architecture:
  - Completely non-blocking: isolates heavy LLM & audio threads from UI rendering loop
  - Uses thread-safe queue.Queue for bi-directional communication
  - Hardware Telemetry & Real-Time Terminal Log Stream with ANSI-like color tags
"""

import time
import queue
import psutil
import threading
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any

import config

# Set CustomTkinter global appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class JarvisUIPanel(ctk.CTk):
    """
    Futuristic dark sci-fi desktop dashboard for Jarvis.
    Communicates with Agent and Audio threads via thread-safe queues.
    """

    def __init__(
        self,
        ui_queue: queue.Queue,
        on_user_submit: Callable[[str], None],
        on_toggle_mute: Optional[Callable[[], bool]] = None,
        on_system_health_click: Optional[Callable[[], None]] = None
    ):
        super().__init__()

        self.ui_queue = ui_queue
        self.on_user_submit = on_user_submit
        self.on_toggle_mute = on_toggle_mute
        self.on_system_health_click = on_system_health_click

        # Window Configuration
        self.title(config.UI_TITLE)
        self.geometry(config.UI_GEOMETRY)
        self.minsize(1020, 680)
        self.configure(fg_color=config.COLOR_BG)

        # Bring window to foreground on launch
        self.lift()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))
        self.focus_force()

        # Build Layout
        self._setup_grid()
        self._build_header()
        self._build_sidebar_telemetry()
        self._build_center_terminal()
        self._build_bottom_input()

        # Start periodic queue polling (50ms interval)
        self.after(50, self._process_queue)

        # Start periodic hardware telemetry polling (1000ms interval)
        self.after(1000, self._update_hardware_telemetry)

    # -------------------------------------------------------------
    # 1. LAYOUT & GEOMETRY SETUP
    # -------------------------------------------------------------
    def _setup_grid(self):
        """Sets up the responsive grid hierarchy."""
        self.grid_columnconfigure(0, weight=0, minsize=260)  # Telemetry Sidebar
        self.grid_columnconfigure(1, weight=1)               # Main Terminal Console
        self.grid_rowconfigure(0, weight=0, minsize=65)      # Top Header Bar
        self.grid_rowconfigure(1, weight=1)                  # Content Area
        self.grid_rowconfigure(2, weight=0, minsize=70)      # Bottom Command Bar

    # -------------------------------------------------------------
    # 2. HEADER COMPONENT
    # -------------------------------------------------------------
    def _build_header(self):
        """Futuristic top status and telemetry banner."""
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=config.COLOR_PANEL_BG,
            border_width=1,
            border_color=config.COLOR_PANEL_BORDER,
            corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=4, pady=(4, 2))

        # Title / Identity
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="◈ JARVIS // EDGE-FIRST GRAPH-AGENT ECOSYSTEM",
            font=ctk.CTkFont(family=config.FONT_FAMILY_TITLE, size=17, weight="bold"),
            text_color=config.COLOR_CYAN
        )
        self.title_label.pack(side="left", padx=20, pady=12)

        # Hardware Allocation Summary Badge
        self.hw_badge = ctk.CTkLabel(
            self.header_frame,
            text="[GPU: RTX 4050 6GB (Ollama LLM)  |  CPU: i5-13450HX (STT/TTS/VEC)]",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11),
            text_color=config.COLOR_TEXT_SECONDARY
        )
        self.hw_badge.pack(side="left", padx=15)

        # Live State Pill Indicator
        self.status_pill = ctk.CTkLabel(
            self.header_frame,
            text="● ONLINE : IDLE",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=12, weight="bold"),
            text_color=config.COLOR_NEON_GREEN,
            fg_color=config.COLOR_ACCENT_BG,
            corner_radius=8,
            padx=14,
            pady=4
        )
        self.status_pill.pack(side="right", padx=20, pady=12)

    # -------------------------------------------------------------
    # 3. SIDEBAR TELEMETRY COMPONENT
    # -------------------------------------------------------------
    def _build_sidebar_telemetry(self):
        """Telemetry sidebar monitoring real-time system resources."""
        self.sidebar_frame = ctk.CTkFrame(
            self,
            fg_color=config.COLOR_PANEL_BG,
            border_width=1,
            border_color=config.COLOR_PANEL_BORDER,
            corner_radius=6
        )
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(4, 2), pady=2)

        # Sidebar Title
        telemetry_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="HARDWARE TELEMETRY",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=12, weight="bold"),
            text_color=config.COLOR_CYAN_DIM
        )
        telemetry_title.pack(anchor="w", padx=16, pady=(16, 8))

        # CPU Metric
        self.cpu_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="CPU UTILIZATION: 0%",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11),
            text_color=config.COLOR_TEXT_PRIMARY
        )
        self.cpu_label.pack(anchor="w", padx=16, pady=(8, 2))

        self.cpu_bar = ctk.CTkProgressBar(
            self.sidebar_frame,
            fg_color=config.COLOR_ACCENT_BG,
            progress_color=config.COLOR_CYAN,
            height=8
        )
        self.cpu_bar.pack(fill="x", padx=16, pady=(0, 10))
        self.cpu_bar.set(0.0)

        # RAM Metric
        self.ram_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="RAM USAGE: 0.0 / 24.0 GB",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11),
            text_color=config.COLOR_TEXT_PRIMARY
        )
        self.ram_label.pack(anchor="w", padx=16, pady=(6, 2))

        self.ram_bar = ctk.CTkProgressBar(
            self.sidebar_frame,
            fg_color=config.COLOR_ACCENT_BG,
            progress_color=config.COLOR_NEON_GREEN,
            height=8
        )
        self.ram_bar.pack(fill="x", padx=16, pady=(0, 10))
        self.ram_bar.set(0.0)

        # Architecture Constraints Card
        arch_card = ctk.CTkFrame(self.sidebar_frame, fg_color=config.COLOR_ACCENT_BG, corner_radius=6)
        arch_card.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            arch_card,
            text="VRAM CEILING: 6.0 GB\nLLM BOUND: ~4.8 GB\nEMBEDDING: BGE-Small (CPU)\nSTT: Whisper-base (CPU)\nTTS: Kokoro-82M (CPU)",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=10),
            text_color=config.COLOR_TEXT_SECONDARY,
            justify="left"
        ).pack(anchor="w", padx=12, pady=10)

        # Control Actions Header
        actions_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="SYSTEM CONTROLS",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=12, weight="bold"),
            text_color=config.COLOR_CYAN_DIM
        )
        actions_title.pack(anchor="w", padx=16, pady=(16, 6))

        # Mic Toggle Button
        self.mute_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🎙 MUTE MIC",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11, weight="bold"),
            fg_color=config.COLOR_ACCENT_BG,
            hover_color="#1a2d4c",
            border_width=1,
            border_color=config.COLOR_CYAN_DIM,
            command=self._handle_toggle_mute
        )
        self.mute_btn.pack(fill="x", padx=16, pady=4)

        # Health Diagnostics Button
        self.health_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="⚡ DIAGNOSTICS",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11, weight="bold"),
            fg_color=config.COLOR_ACCENT_BG,
            hover_color="#1a2d4c",
            border_width=1,
            border_color=config.COLOR_CYAN_DIM,
            command=self._handle_health_click
        )
        self.health_btn.pack(fill="x", padx=16, pady=4)

        # Clear Logs Button
        self.clear_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="⌫ CLEAR TERMINAL",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11),
            fg_color="transparent",
            hover_color=config.COLOR_ACCENT_BG,
            text_color=config.COLOR_TEXT_SECONDARY,
            command=self._clear_logs
        )
        self.clear_btn.pack(fill="x", padx=16, pady=(4, 16))

    # -------------------------------------------------------------
    # 4. TERMINAL LOG CONSOLE COMPONENT
    # -------------------------------------------------------------
    def _build_center_terminal(self):
        """Holographic terminal logging graph transitions, tool operations, and responses."""
        self.terminal_frame = ctk.CTkFrame(
            self,
            fg_color=config.COLOR_PANEL_BG,
            border_width=1,
            border_color=config.COLOR_PANEL_BORDER,
            corner_radius=6
        )
        self.terminal_frame.grid(row=1, column=1, sticky="nsew", padx=(2, 4), pady=2)

        # Terminal Header
        term_header = ctk.CTkFrame(self.terminal_frame, fg_color="transparent")
        term_header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            term_header,
            text="NEURAL GRAPH CONSOLE // REAL-TIME EXECUTION STREAM",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=11, weight="bold"),
            text_color=config.COLOR_CYAN_DIM
        ).pack(side="left")

        # Scrollable Textbox with color styling
        self.terminal_text = ctk.CTkTextbox(
            self.terminal_frame,
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=12),
            fg_color=config.COLOR_BG,
            text_color=config.COLOR_TEXT_PRIMARY,
            wrap="word",
            corner_radius=4,
            border_width=1,
            border_color=config.COLOR_PANEL_BORDER
        )
        self.terminal_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Configure ANSI-like text tags on the underlying tkinter widget
        self.text_widget = self.terminal_text._textbox
        self.text_widget.tag_config("TAG_TIMESTAMP", foreground=config.COLOR_TEXT_SECONDARY)
        self.text_widget.tag_config("TAG_SYSTEM", foreground=config.COLOR_CYAN_DIM)
        self.text_widget.tag_config("TAG_USER", foreground="#ffffff", font=(config.FONT_FAMILY_MONO, 12, "bold"))
        self.text_widget.tag_config("TAG_JARVIS", foreground=config.COLOR_CYAN, font=(config.FONT_FAMILY_MONO, 12, "bold"))
        self.text_widget.tag_config("TAG_AGENT", foreground=config.COLOR_CYAN)
        self.text_widget.tag_config("TAG_ROUTER", foreground="#bb86fc")
        self.text_widget.tag_config("TAG_TOOL", foreground="#ffd600")
        self.text_widget.tag_config("TAG_SUCCESS", foreground=config.COLOR_NEON_GREEN)
        self.text_widget.tag_config("TAG_ERROR", foreground=config.COLOR_ALERT_RED, font=(config.FONT_FAMILY_MONO, 12, "bold"))
        self.text_widget.tag_config("TAG_WARN", foreground=config.COLOR_WARN_AMBER)
        self.text_widget.tag_config("TAG_RETRY", foreground=config.COLOR_WARN_AMBER, font=(config.FONT_FAMILY_MONO, 12, "bold"))
        self.text_widget.tag_config("TAG_SPEAK", foreground="#ff79c6")
        self.text_widget.tag_config("TAG_MIC", foreground="#a060ff")
        self.text_widget.tag_config("TAG_MEMORY", foreground="#8be9fd")

    # -------------------------------------------------------------
    # 5. BOTTOM INPUT / COMMAND BAR
    # -------------------------------------------------------------
    def _build_bottom_input(self):
        """Manual text entry bar for keyboard interaction."""
        self.input_frame = ctk.CTkFrame(
            self,
            fg_color=config.COLOR_PANEL_BG,
            border_width=1,
            border_color=config.COLOR_PANEL_BORDER,
            corner_radius=0
        )
        self.input_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=4, pady=(2, 4))

        # Command Entry
        self.command_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter prompt or command (or speak into microphone)...",
            placeholder_text_color=config.COLOR_TEXT_SECONDARY,
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=13),
            fg_color=config.COLOR_BG,
            border_color=config.COLOR_PANEL_BORDER,
            text_color=config.COLOR_TEXT_PRIMARY,
            height=42
        )
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(16, 8), pady=12)
        self.command_entry.bind("<Return>", lambda event: self._handle_submit())

        # Send Button
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="TRANSMIT ❯",
            font=ctk.CTkFont(family=config.FONT_FAMILY_MONO, size=12, weight="bold"),
            fg_color=config.COLOR_CYAN,
            text_color=config.COLOR_BG,
            hover_color="#33eeff",
            height=42,
            width=130,
            command=self._handle_submit
        )
        self.send_btn.pack(side="right", padx=(0, 16), pady=12)

    # -------------------------------------------------------------
    # 6. QUEUE-DRIVEN NON-BLOCKING UPDATES
    # -------------------------------------------------------------
    def _process_queue(self):
        """Processes pending log and status updates from the worker threads."""
        while not self.ui_queue.empty():
            try:
                event_type, payload = self.ui_queue.get_nowait()
                if event_type == "log":
                    tag, message = payload
                    self._append_log(tag, message)
                elif event_type == "status":
                    text, color = payload
                    self._set_status(text, color)
                self.ui_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error processing UI queue item: {e}")

        # Re-arm timer
        self.after(50, self._process_queue)

    def _append_log(self, tag: str, message: str):
        """Appends a tagged message into the scrollable terminal."""
        now = time.strftime("%H:%M:%S")
        tag_clean = tag.upper()
        tag_name = f"TAG_{tag_clean}" if f"TAG_{tag_clean}" in self.text_widget.tag_names() else "TAG_SYSTEM"

        self.text_widget.insert(tk.END, f"[{now}] ", "TAG_TIMESTAMP")
        self.text_widget.insert(tk.END, f"[{tag_clean:7}] ", tag_name)
        self.text_widget.insert(tk.END, f"{message}\n")
        self.text_widget.see(tk.END)

    def _set_status(self, text: str, color: str):
        """Updates the top right state indicator pill."""
        self.status_pill.configure(text=f"● {text}", text_color=color)

    def _update_hardware_telemetry(self):
        """Updates CPU and RAM metrics without freezing the mainloop."""
        try:
            cpu_val = float(psutil.cpu_percent())
            vm = psutil.virtual_memory()
            ram_used_gb = round(vm.used / (1024 ** 3), 1)
            ram_total_gb = round(vm.total / (1024 ** 3), 1)

            self.cpu_label.configure(text=f"CPU UTILIZATION: {cpu_val}%")
            self.cpu_bar.set(cpu_val / 100.0)

            self.ram_label.configure(text=f"RAM USAGE: {ram_used_gb} / {ram_total_gb} GB")
            self.ram_bar.set(vm.percent / 100.0)
        except Exception:
            pass

        self.after(1000, self._update_hardware_telemetry)

    # -------------------------------------------------------------
    # 7. EVENT HANDLERS
    # -------------------------------------------------------------
    def _handle_submit(self):
        """Pushes user prompt from command entry to the agent loop."""
        text = self.command_entry.get().strip()
        if text:
            self.command_entry.delete(0, tk.END)
            self._append_log("USER", text)
            self.on_user_submit(text)

    def _handle_toggle_mute(self):
        """Calls mute toggle callback and updates button label."""
        if self.on_toggle_mute:
            muted = self.on_toggle_mute()
            if muted:
                self.mute_btn.configure(text="🔇 UNMUTE MIC", border_color=config.COLOR_ALERT_RED)
            else:
                self.mute_btn.configure(text="🎙 MUTE MIC", border_color=config.COLOR_CYAN_DIM)

    def _handle_health_click(self):
        """Triggers direct system diagnostics."""
        if self.on_system_health_click:
            self.on_system_health_click()
        else:
            self.on_user_submit("What is my current system health and hardware telemetry?")

    def _clear_logs(self):
        """Clears the terminal console."""
        self.text_widget.delete("1.0", tk.END)
        self._append_log("SYSTEM", "Terminal console cleared.")
