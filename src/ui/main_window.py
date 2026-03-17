import os
import queue
import tempfile
import threading
from tkinter import messagebox

import customtkinter as ctk

from src.app_state import AppState
from src.audio.recorder import AudioRecorder
from src.config.settings import SettingsStore
from src.transcription.engine import TranscriptionEngine


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(
        self,
        recorder: AudioRecorder,
        engine: TranscriptionEngine,
        settings_store: SettingsStore,
    ) -> None:
        super().__init__()
        self._recorder = recorder
        self._engine = engine
        self._settings_store = settings_store
        self._result_queue: queue.Queue = queue.Queue()

        self.title("Speech to Text")
        self.geometry("640x520")
        self.resizable(True, True)

        self._build_ui()
        self._apply_state(AppState.IDLE)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Top info bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))

        self._status_label = ctk.CTkLabel(top, text="Idle", anchor="w")
        self._status_label.pack(side="left")

        device_text = (
            "GPU (CUDA)" if self._engine.device == "cuda" else "CPU"
        )
        self._device_label = ctk.CTkLabel(
            top,
            text=f"Using {device_text}",
            anchor="e",
            text_color="gray60",
            font=ctk.CTkFont(size=12),
        )
        self._device_label.pack(side="right")

        # Centre button area
        btn_area = ctk.CTkFrame(self, fg_color="transparent")
        btn_area.pack(pady=14)

        self._record_btn = ctk.CTkButton(
            btn_area,
            text="⏺  Record",
            width=160,
            height=52,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_record,
        )
        self._record_btn.grid(row=0, column=0, padx=6)

        self._accept_btn = ctk.CTkButton(
            btn_area,
            text="✓  Accept",
            width=160,
            height=52,
            fg_color="#2d8a4e",
            hover_color="#236b3d",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_accept,
        )
        self._accept_btn.grid(row=0, column=0, padx=6)

        self._discard_btn = ctk.CTkButton(
            btn_area,
            text="✗  Discard",
            width=160,
            height=52,
            fg_color="#b03030",
            hover_color="#8a2424",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_discard,
        )
        self._discard_btn.grid(row=0, column=1, padx=6)

        self._spinner_label = ctk.CTkLabel(
            btn_area,
            text="Transcribing…",
            font=ctk.CTkFont(size=15),
            text_color="gray60",
        )
        self._spinner_label.grid(row=0, column=0, columnspan=2)

        # Output text area
        self._output = ctk.CTkTextbox(self, width=600, height=300, wrap="word")
        self._output.pack(padx=16, pady=(0, 10))

        # Action buttons
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(pady=(0, 14))

        ctk.CTkButton(
            actions, text="Copy", width=110, command=self._on_copy
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            actions, text="Clear", width=110, command=self._on_clear
        ).grid(row=0, column=1, padx=6)
        ctk.CTkButton(
            actions, text="⚙  Settings", width=110, command=self._on_settings
        ).grid(row=0, column=2, padx=6)

    # ── State machine ────────────────────────────────────────────────────────

    def _apply_state(self, state: AppState) -> None:
        self._record_btn.grid_remove()
        self._accept_btn.grid_remove()
        self._discard_btn.grid_remove()
        self._spinner_label.grid_remove()

        if state == AppState.IDLE:
            self._record_btn.grid()
            self._status_label.configure(text="Idle")
        elif state == AppState.RECORDING:
            self._accept_btn.grid()
            self._discard_btn.grid()
            self._status_label.configure(text="Recording…")
        elif state == AppState.TRANSCRIBING:
            self._spinner_label.grid()
            self._status_label.configure(text="Transcribing…")

    # ── Button handlers ──────────────────────────────────────────────────────

    def _on_record(self) -> None:
        try:
            self._recorder.start()
            self._apply_state(AppState.RECORDING)
        except Exception as exc:
            messagebox.showerror(
                "Microphone Error",
                f"Could not access microphone:\n{exc}\n\n"
                "Please check your microphone and permissions.",
            )

    def _on_accept(self) -> None:
        try:
            audio_data = self._recorder.stop()
        except Exception as exc:
            messagebox.showerror("Recording Error", str(exc))
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

    def _on_settings(self) -> None:
        from src.ui.settings_window import SettingsWindow

        win = SettingsWindow(self, self._settings_store)
        self.wait_window(win)

        # Reload engine if model changed
        new_model = self._settings_store.load().model_id
        if new_model != self._engine.model_id:
            self._status_label.configure(text="Loading model…")
            self.update_idletasks()
            self._engine = TranscriptionEngine(new_model)
            self._refresh_device_label()
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
            if status == "ok":
                self._append_text(payload)
            else:
                messagebox.showerror(
                    "Transcription Failed",
                    f"Could not transcribe audio:\n{payload}",
                )
            # Reflect device if a lazy CUDA→CPU fallback happened mid-transcription
            self._refresh_device_label()
            self._apply_state(AppState.IDLE)
        except queue.Empty:
            self.after(100, self._poll_result)

    def _refresh_device_label(self) -> None:
        device_text = "GPU (CUDA)" if self._engine.device == "cuda" else "CPU"
        self._device_label.configure(text=f"Using {device_text}")

    def _append_text(self, text: str) -> None:
        if not text:
            return
        current = self._output.get("1.0", "end-1c")
        if current:
            self._output.insert("end", "\n" + text)
        else:
            self._output.insert("end", text)
