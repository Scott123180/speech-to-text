import os
import sys

import customtkinter as ctk

from src.config.settings import Settings, SettingsStore
from src.ui import theme
from src.ui.theme import BG, BORDER, FG, MUTED, Pill

MODELS = ["tiny", "base", "small", "medium", "large-v3", "distil-large-v3"]
SCALE_LABELS = {1.0: "100%", 1.25: "125%", 1.5: "150%", 1.75: "175%", 2.0: "200%"}
LABEL_TO_SCALE = {v: k for k, v in SCALE_LABELS.items()}


class SettingsWindow(ctk.CTkToplevel):
    """Modal settings screen for choosing the transcription model and UI scale."""

    def __init__(self, parent: ctk.CTk, settings_store: SettingsStore) -> None:
        super().__init__(parent, fg_color=BG)
        self._settings_store = settings_store
        self._current = settings_store.load()

        self.title("Settings")
        self.geometry("340x290")
        self.resizable(False, False)
        self.after(10, self.grab_set)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            body,
            text="Settings",
            text_color=FG,
            font=theme.font(theme.HEADING_SIZE, "bold"),
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            body,
            text="Changes save as you make them.",
            text_color=MUTED,
            font=theme.font(13),
            anchor="w",
        ).pack(fill="x", pady=(0, 14))

        self._field(
            body,
            "Transcription model",
            MODELS,
            self._current.model_id,
            self._on_model_change,
        )
        self._field(
            body,
            "UI scale",
            list(SCALE_LABELS.values()),
            SCALE_LABELS.get(self._current.ui_scale, "100%"),
            self._on_scale_change,
        )

        # Shown only after a scale change.
        self._restart_row = ctk.CTkFrame(body, fg_color="transparent")
        ctk.CTkLabel(
            self._restart_row,
            text="Scale applies after a restart.",
            text_color=MUTED,
            font=theme.font(13),
        ).pack(side="left")
        Pill(self._restart_row, "Restart now", self._restart_app).pack(side="right")

    def _field(self, master, label: str, values: list[str], current: str, command):
        ctk.CTkLabel(
            master,
            text=label,
            text_color=MUTED,
            font=theme.font(13),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))
        ctk.CTkComboBox(
            master,
            values=values,
            variable=ctk.StringVar(value=current),
            command=command,
            state="readonly",
            height=30,
            corner_radius=4,
            border_width=1,
            fg_color=BG,
            border_color=BORDER,
            button_color=BORDER,
            button_hover_color=MUTED,
            text_color=FG,
            dropdown_fg_color=BG,
            dropdown_hover_color=BORDER,
            dropdown_text_color=FG,
            font=theme.font(14),
            dropdown_font=theme.font(14),
        ).pack(fill="x", pady=(0, 14))

    def _on_model_change(self, model_id: str) -> None:
        settings = self._settings_store.load()
        self._settings_store.save(
            Settings(model_id=model_id, ui_scale=settings.ui_scale)
        )

    def _on_scale_change(self, label: str) -> None:
        scale = LABEL_TO_SCALE[label]
        settings = self._settings_store.load()
        self._settings_store.save(Settings(model_id=settings.model_id, ui_scale=scale))
        self._restart_row.pack(fill="x", pady=(4, 0))

    def _restart_app(self) -> None:
        os.execv(sys.executable, [sys.executable, "-m", "src.app"])
