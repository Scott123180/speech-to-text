import os
import sys

import customtkinter as ctk

from src.config.settings import VALID_SCALES, Settings, SettingsStore

MODELS = ["tiny", "base", "small", "medium", "large-v3", "distil-large-v3"]
SCALE_LABELS = {1.0: "100%", 1.25: "125%", 1.5: "150%", 1.75: "175%", 2.0: "200%"}
LABEL_TO_SCALE = {v: k for k, v in SCALE_LABELS.items()}


class SettingsWindow(ctk.CTkToplevel):
    """Modal settings screen for choosing the transcription model and UI scale."""

    def __init__(self, parent: ctk.CTk, settings_store: SettingsStore) -> None:
        super().__init__(parent)
        self._settings_store = settings_store
        self._current = settings_store.load()
        self._scale_changed = False

        self.title("Settings")
        self.geometry("320x240")
        self.resizable(False, False)
        self.after(10, self.grab_set)

        ctk.CTkLabel(self, text="Transcription Model", font=ctk.CTkFont(size=14)).pack(
            pady=(24, 8)
        )
        ctk.CTkOptionMenu(
            self,
            values=MODELS,
            variable=ctk.StringVar(value=self._current.model_id),
            command=self._on_model_change,
        ).pack()

        ctk.CTkLabel(self, text="UI Scale", font=ctk.CTkFont(size=14)).pack(pady=(20, 8))
        current_label = SCALE_LABELS.get(self._current.ui_scale, "100%")
        ctk.CTkOptionMenu(
            self,
            values=list(SCALE_LABELS.values()),
            variable=ctk.StringVar(value=current_label),
            command=self._on_scale_change,
        ).pack()

        self._restart_btn = ctk.CTkButton(
            self,
            text="Restart to Apply Scale",
            width=200,
            fg_color="#555",
            hover_color="#444",
            command=self._restart_app,
        )
        # shown only after a scale change

    def _on_model_change(self, model_id: str) -> None:
        settings = self._settings_store.load()
        self._settings_store.save(Settings(model_id=model_id, ui_scale=settings.ui_scale))

    def _on_scale_change(self, label: str) -> None:
        scale = LABEL_TO_SCALE[label]
        settings = self._settings_store.load()
        self._settings_store.save(Settings(model_id=settings.model_id, ui_scale=scale))
        self._restart_btn.pack(pady=(8, 0))

    def _restart_app(self) -> None:
        os.execv(sys.executable, [sys.executable, "-m", "src.app"])
