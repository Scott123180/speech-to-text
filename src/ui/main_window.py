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
NOTICE_SECONDS = 8

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
        # The class name is what GNOME matches against StartupWMClass in
        # speech-to-text.desktop to show the right icon in the app switcher.
        super().__init__(fg_color=BG, className="speech-to-text")
        theme.match_font_dpi(self)
        theme.set_window_icon(self)
        self._recorder = recorder
        self._engine = engine
        self._settings_store = settings_store
        self._result_queue: queue.Queue = queue.Queue()
        self._state = AppState.IDLE
        self._smoother = LevelSmoother()
        self._state_started = 0.0
        self._animating = False
        self._cleared_text: str | None = None
        self._notice_timer: str | None = None

        self.title("Speech to Text")
        self.geometry("640x520")
        self.minsize(420, 240)
        self.resizable(True, True)

        self._build_ui()
        self._apply_state(AppState.IDLE)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Clear lives up here, by the text it destroys and far from Copy.
        topbar = ctk.CTkFrame(self, fg_color="transparent", height=30)
        topbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0))
        topbar.pack_propagate(False)
        self._clear_btn = Pill(
            topbar, "Clear", self._on_clear, variant="link", danger=True
        )

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
        self._output.grid(row=1, column=0, sticky="nsew", padx=(4, 0))

        self._placeholder = ctk.CTkLabel(
            self._output,
            text="Press Record and start talking.",
            text_color=MUTED,
            fg_color=BG,
            font=theme.font(),
        )
        self._placeholder.bind("<Button-1>", lambda _e: self._output.focus_set())
        self._output.bind("<KeyRelease>", lambda _e: self._sync_text_state())

        self._build_footer()
        self._build_notice()
        self._sync_text_state()

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(8, 12))

        # Left slot: what's doing the transcribing (and where to change it) when
        # idle, the live status otherwise.
        self._info = ctk.CTkFrame(footer, fg_color="transparent")
        self._info.pack(side="left")
        small = theme.font(theme.SMALL_SIZE)
        self._model_label = ctk.CTkLabel(
            self._info, text="Model", text_color=MUTED, font=small
        )
        self._model_value = ctk.CTkLabel(self._info, text="", text_color=FG, font=small)
        separator = ctk.CTkLabel(self._info, text="·", text_color=MUTED, font=small)
        self._device_label = ctk.CTkLabel(
            self._info, text="Device", text_color=MUTED, font=small
        )
        self._device_value = ctk.CTkLabel(
            self._info, text="", text_color=FG, font=small
        )
        for widget, gap in (
            (self._model_label, 5),
            (self._model_value, 8),
            (separator, 8),
            (self._device_label, 5),
            (self._device_value, 10),
        ):
            widget.pack(side="left", padx=(0, gap))
        Pill(self._info, "Settings", self._on_settings, variant="link").pack(
            side="left"
        )

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

        # Right slot: Copy, then the primary action. Pairs share a height so the
        # row reads as one control group.
        primary = ctk.CTkFrame(footer, fg_color="transparent")
        primary.pack(side="right")
        self._copy_btn = Pill(
            primary, "Copy", self._on_copy, large=True, width_text="Copied"
        )
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
            font=theme.font(13),
            anchor="w",
            justify="left",
        )
        self._notice_label.grid(row=1, column=0, sticky="ew", padx=18, pady=8)
        self._notice_label.bind(
            "<Configure>",
            lambda e: self._notice_label.configure(wraplength=max(e.width - 8, 100)),
        )
        self._notice_actions = ctk.CTkFrame(self._notice, fg_color="transparent")
        self._notice_actions.grid(row=1, column=1, padx=(0, 18), pady=8)

    # ── Notice ───────────────────────────────────────────────────────────────

    def _show_notice(
        self, message: str, error: bool = True, action: tuple | None = None
    ) -> None:
        """Show *message* under the footer.

        Errors stay until dismissed. Info notices (e.g. "cleared — undo?") carry
        an *action* of (label, command) and fade on their own.
        """
        self._clear_notice()
        self._notice_label.configure(text=message, text_color=ERROR if error else FG)
        for child in self._notice_actions.winfo_children():
            child.destroy()
        if action:
            label, command = action
            Pill(self._notice_actions, label, command).pack(side="left", padx=(0, 6))
        Pill(
            self._notice_actions,
            "Dismiss",
            self._clear_notice,
            variant="outline" if error else "link",
            accent=error,
        ).pack(side="left")
        self._notice.grid(row=3, column=0, sticky="ew")
        if not error:
            self._notice_timer = self.after(NOTICE_SECONDS * 1000, self._clear_notice)

    def _clear_notice(self) -> None:
        if self._notice_timer is not None:
            self.after_cancel(self._notice_timer)
            self._notice_timer = None
        self._notice.grid_remove()

    # ── State machine ────────────────────────────────────────────────────────

    def _apply_state(self, state: AppState) -> None:
        self._state = state
        self._state_started = time.monotonic()

        for btn in (self._record_btn, self._discard_btn, self._accept_btn):
            btn.pack_forget()
        self._copy_btn.pack_forget()
        if state == AppState.IDLE:
            self._copy_btn.pack(side="left", padx=(0, 8))
            self._record_btn.pack(side="left")
        elif state == AppState.RECORDING:
            self._discard_btn.pack(side="left", padx=(0, 8))
            self._accept_btn.pack(side="left")
        self._sync_text_state()
        if state == AppState.IDLE:
            self._status.pack_forget()
            self._info.pack(side="left")
            self._refresh_device_label()
            return

        self._info.pack_forget()
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
        if text:
            self._copy_btn.configure(text="Copied")
            self.after(1500, lambda: self._copy_btn.configure(text="Copy"))

    def _on_clear(self) -> None:
        text = self._output.get("1.0", "end-1c")
        self._output.delete("1.0", "end")
        self._sync_text_state()
        if text:
            self._cleared_text = text
            self._show_notice(
                "Transcript cleared.",
                error=False,
                action=("Undo", self._on_undo_clear),
            )

    def _on_undo_clear(self) -> None:
        if self._cleared_text is None:
            return
        # Anything typed since the clear stays, after the restored text.
        if self._output.get("1.0", "end-1c"):
            self._output.insert("1.0", self._cleared_text + "\n")
        else:
            self._output.insert("1.0", self._cleared_text)
        self._cleared_text = None
        self._clear_notice()
        self._sync_text_state()

    def _on_settings(self) -> None:
        from src.ui.settings_window import SettingsWindow

        win = SettingsWindow(self, self._settings_store)
        self.wait_window(win)

        # Reload engine if model changed
        new_model = self._settings_store.load().model_id
        if new_model != self._engine.model_id:
            self._model_value.configure(text=f"{new_model} (loading…)")
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
        self._model_value.configure(text=self._engine.model_id)
        self._device_value.configure(text=device_text)

    def _sync_text_state(self) -> None:
        """Placeholder when empty; Clear only when there's text and we're idle."""
        has_text = bool(self._output.get("1.0", "end-1c"))
        if has_text:
            self._placeholder.place_forget()
        else:
            self._placeholder.place(x=11, y=6)
        if has_text and self._state == AppState.IDLE:
            self._clear_btn.pack(side="right")
        else:
            self._clear_btn.pack_forget()

    def _append_text(self, text: str) -> None:
        if not text:
            return
        current = self._output.get("1.0", "end-1c")
        if current:
            self._output.insert("end", "\n" + text)
        else:
            self._output.insert("end", text)
        self._sync_text_state()
