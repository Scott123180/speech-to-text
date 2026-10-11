import math
import os
import queue
import tempfile
import threading
import time
import tkinter as tk

import customtkinter as ctk

from src.app_state import AppState
from src.audio.recorder import AudioRecorder
from src.config.settings import SettingsStore
from src.transcription.engine import TranscriptionEngine
from src.ui import theme
from src.ui.meter import LevelSmoother, format_elapsed, lit_bars
from src.ui.theme import BG, BORDER, ERROR, FG, MUTED, Pill

METER_BARS = 12
FRAME_MS = 33
PULSE_SECONDS = 1.4
SLIDE_SECONDS = 1.1

STATUS_LABELS = {
    AppState.RECORDING: "Listening",
    AppState.TRANSCRIBING: "Transcribing…",
}


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(
        self,
        recorder: AudioRecorder,
        engine: TranscriptionEngine,
        settings_store: SettingsStore,
    ) -> None:
        super().__init__(fg_color=BG)
        theme.match_font_dpi(self)
        self._recorder = recorder
        self._engine = engine
        self._settings_store = settings_store
        self._result_queue: queue.Queue = queue.Queue()
        self._state = AppState.IDLE
        self._smoother = LevelSmoother()
        self._state_started = 0.0
        self._animating = False

        self.title("Speech to Text")
        self.geometry("640x520")
        self.minsize(420, 240)
        self.resizable(True, True)

        self._build_ui()
        self._apply_state(AppState.IDLE)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # The writing surface fills the window, borderless, like waypoint's box.
        self._output = ctk.CTkTextbox(
            self,
            wrap="word",
            corner_radius=0,
            border_width=0,
            fg_color=BG,
            text_color=FG,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=MUTED,
            font=theme.font(),
            padx=14,
            pady=12,
            spacing1=2,
            spacing2=4,
            spacing3=2,
        )
        self._output.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=(4, 0))

        self._placeholder = ctk.CTkLabel(
            self._output,
            text="Press Record and start talking.",
            text_color=MUTED,
            fg_color=BG,
            font=theme.font(),
        )
        self._placeholder.bind("<Button-1>", lambda _e: self._output.focus_set())
        self._output.bind("<KeyRelease>", lambda _e: self._sync_placeholder())

        self._build_footer()
        self._build_notice()
        self._sync_placeholder()

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="ew", padx=18, pady=(8, 12))

        # Left slot: a quiet hint when idle, the live status otherwise.
        self._hint_label = ctk.CTkLabel(
            footer, text="", text_color=MUTED, font=theme.font(theme.SMALL_SIZE)
        )
        self._hint_label.pack(side="left")

        self._status = ctk.CTkFrame(footer, fg_color="transparent")
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        self._px = lambda n: round(n * scale)

        self._dot = tk.Canvas(
            self._status,
            width=self._px(9),
            height=self._px(9),
            highlightthickness=0,
        )
        self._dot.pack(side="left", padx=(0, 8))
        self._status_label = ctk.CTkLabel(
            self._status, text="", font=theme.font(theme.SMALL_SIZE)
        )
        self._status_label.pack(side="left", padx=(0, 8))
        self._meter = tk.Canvas(
            self._status,
            width=self._px(METER_BARS * 5 - 2),
            height=self._px(12),
            highlightthickness=0,
        )
        self._elapsed = ctk.CTkLabel(
            self._status, text="", text_color=MUTED, font=theme.font(theme.SMALL_SIZE)
        )
        self._working = tk.Canvas(
            self._status,
            width=self._px(92),
            height=self._px(3),
            highlightthickness=0,
        )

        # Right slot: actions, quietest first, the primary pill last.
        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.pack(side="right")

        # Secondary actions hide while busy, leaving the slot to the status.
        self._secondary = ctk.CTkFrame(actions, fg_color="transparent")
        self._secondary.pack(side="left", padx=(0, 10))
        for text, command in (
            ("Copy", self._on_copy),
            ("Clear", self._on_clear),
            ("Settings", self._on_settings),
        ):
            Pill(self._secondary, text, command, variant="link").pack(
                side="left", padx=(0, 2)
            )

        primary = ctk.CTkFrame(actions, fg_color="transparent")
        primary.pack(side="left")
        self._primary = primary
        self._record_btn = Pill(primary, "Record", self._on_record, variant="filled")
        self._discard_btn = Pill(primary, "Discard", self._on_discard, large=True)
        self._accept_btn = Pill(
            primary, "Accept", self._on_accept, variant="filled", accent=True
        )

    def _build_notice(self) -> None:
        self._notice = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._notice.grid_columnconfigure(0, weight=1)
        ctk.CTkFrame(self._notice, height=1, fg_color=BORDER, corner_radius=0).grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )
        self._notice_label = ctk.CTkLabel(
            self._notice,
            text="",
            text_color=ERROR,
            font=theme.font(13),
            anchor="w",
            justify="left",
        )
        self._notice_label.grid(row=1, column=0, sticky="ew", padx=18, pady=8)
        self._notice_label.bind(
            "<Configure>",
            lambda e: self._notice_label.configure(wraplength=max(e.width - 8, 100)),
        )
        Pill(self._notice, "Dismiss", self._clear_notice, accent=True).grid(
            row=1, column=1, padx=(0, 18), pady=8
        )

    # ── Notice ───────────────────────────────────────────────────────────────

    def _show_notice(self, message: str) -> None:
        self._notice_label.configure(text=message)
        self._notice.grid(row=2, column=0, sticky="ew")

    def _clear_notice(self) -> None:
        self._notice.grid_remove()

    # ── State machine ────────────────────────────────────────────────────────

    def _apply_state(self, state: AppState) -> None:
        self._state = state
        self._state_started = time.monotonic()

        for btn in (self._record_btn, self._discard_btn, self._accept_btn):
            btn.pack_forget()
        if state == AppState.IDLE:
            self._record_btn.pack(side="left")
        elif state == AppState.RECORDING:
            self._discard_btn.pack(side="left", padx=(0, 6))
            self._accept_btn.pack(side="left")
        if state == AppState.IDLE:
            self._secondary.pack(side="left", padx=(0, 10), before=self._primary)
            self._status.pack_forget()
            self._hint_label.pack(side="left")
            self._refresh_device_label()
            return

        self._secondary.pack_forget()
        self._hint_label.pack_forget()
        self._status.pack(side="left")
        recording = state == AppState.RECORDING
        self._status_label.configure(
            text=STATUS_LABELS[state], text_color=ERROR if recording else FG
        )
        for widget in (self._meter, self._elapsed, self._working):
            widget.pack_forget()
        if recording:
            self._smoother.reset()
            self._meter.pack(side="left", padx=(0, 8))
            self._elapsed.pack(side="left")
        else:
            self._working.pack(side="left")
        if not self._animating:
            self._animating = True
            self._animate()

    def _animate(self) -> None:
        """Repaint the live status; runs every frame while not idle."""
        if self._state == AppState.IDLE:
            self._animating = False
            return
        t = time.monotonic() - self._state_started
        bg = theme.resolve(BG)
        for canvas in (self._dot, self._meter, self._working):
            canvas.configure(bg=bg)

        self._dot.delete("all")
        if self._state == AppState.RECORDING:
            # Opacity 1 → 0.25 → 1, emulated by blending toward the background.
            fade = 0.375 - 0.375 * math.cos(2 * math.pi * t / PULSE_SECONDS)
            dot_color = theme.blend(ERROR, BG, fade)
            self._paint_meter()
            self._elapsed.configure(text=format_elapsed(t))
        else:
            dot_color = theme.resolve(MUTED)
            self._paint_working(t)
        self._dot.create_oval(0, 0, self._px(9), self._px(9), fill=dot_color, width=0)

        self.after(FRAME_MS, self._animate)

    def _paint_meter(self) -> None:
        level = self._smoother.update(self._recorder.level)
        lit = lit_bars(level, METER_BARS)
        full = self._px(12)
        self._meter.delete("all")
        for i in range(METER_BARS):
            on = i < lit
            height = full * (0.28 + 0.72 * (i + 1) / METER_BARS if on else 0.28)
            x = self._px(i * 5)
            self._meter.create_rectangle(
                x,
                full - height,
                x + self._px(3),
                full,
                fill=theme.resolve(ERROR if on else BORDER),
                width=0,
            )

    def _paint_working(self, t: float) -> None:
        # Indeterminate by design — whisper cannot report true progress.
        width, height = self._px(92), self._px(3)
        segment = width * 0.4
        phase = (t % SLIDE_SECONDS) / SLIDE_SECONDS
        eased = 0.5 - 0.5 * math.cos(math.pi * phase)
        x = segment * (-1 + 3.5 * eased)
        self._working.delete("all")
        self._working.create_rectangle(
            0, 0, width, height, fill=theme.resolve(BORDER), width=0
        )
        self._working.create_rectangle(
            x, 0, x + segment, height, fill=theme.resolve(FG), width=0
        )

    # ── Button handlers ──────────────────────────────────────────────────────

    def _on_record(self) -> None:
        self._clear_notice()
        try:
            self._recorder.start()
            self._apply_state(AppState.RECORDING)
        except Exception as exc:
            self._show_notice(
                f"Couldn't open the microphone — {exc}\n"
                "Check that it's connected and not in use by another app."
            )

    def _on_accept(self) -> None:
        try:
            audio_data = self._recorder.stop()
        except Exception as exc:
            self._show_notice(f"Recording failed — {exc}")
            self._apply_state(AppState.IDLE)
            return

        self._apply_state(AppState.TRANSCRIBING)

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        audio_data.to_wav_file(tmp.name)

        thread = threading.Thread(
            target=self._transcribe_worker, args=(tmp.name,), daemon=True
        )
        thread.start()
        self.after(100, self._poll_result)

    def _on_discard(self) -> None:
        self._recorder.discard()
        self._apply_state(AppState.IDLE)

    def _on_copy(self) -> None:
        text = self._output.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)

    def _on_clear(self) -> None:
        self._output.delete("1.0", "end")
        self._sync_placeholder()

    def _on_settings(self) -> None:
        from src.ui.settings_window import SettingsWindow

        win = SettingsWindow(self, self._settings_store)
        self.wait_window(win)

        # Reload engine if model changed
        new_model = self._settings_store.load().model_id
        if new_model != self._engine.model_id:
            self._hint_label.configure(text="Loading model…")
            self.update_idletasks()
            self._engine = TranscriptionEngine(new_model)
            self._apply_state(AppState.IDLE)

    # ── Background transcription ─────────────────────────────────────────────

    def _transcribe_worker(self, audio_path: str) -> None:
        try:
            result = self._engine.transcribe(audio_path)
            self._result_queue.put(("ok", result.text))
        except Exception as exc:
            self._result_queue.put(("error", str(exc)))
        finally:
            try:
                os.unlink(audio_path)
            except OSError:
                pass

    def _poll_result(self) -> None:
        try:
            status, payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_result)
            return
        if status == "ok" and payload:
            self._append_text(payload)
        elif status == "ok":
            self._show_notice("Didn't catch that — try again.")
        else:
            self._show_notice(f"Couldn't transcribe that — {payload}")
        # _apply_state refreshes the device hint, which reflects a lazy
        # CUDA→CPU fallback that happened mid-transcription.
        self._apply_state(AppState.IDLE)

    def _refresh_device_label(self) -> None:
        device_text = "GPU (CUDA)" if self._engine.device == "cuda" else "CPU"
        self._hint_label.configure(text=f"{self._engine.model_id} · {device_text}")

    def _sync_placeholder(self) -> None:
        if self._output.get("1.0", "end-1c"):
            self._placeholder.place_forget()
        else:
            self._placeholder.place(x=11, y=6)

    def _append_text(self, text: str) -> None:
        if not text:
            return
        current = self._output.get("1.0", "end-1c")
        if current:
            self._output.insert("end", "\n" + text)
        else:
            self._output.insert("end", text)
        self._sync_placeholder()
