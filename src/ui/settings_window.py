import customtkinter as ctk

from src.config.settings import Settings, SettingsStore

MODELS = ["tiny", "base", "small", "medium", "large-v3", "distil-large-v3"]


class SettingsWindow(ctk.CTkToplevel):
    """Modal settings screen for choosing the transcription model."""

    def __init__(self, parent: ctk.CTk, settings_store: SettingsStore) -> None:
        super().__init__(parent)
        self._settings_store = settings_store
        self._current = settings_store.load()

        self.title("Settings")
        self.geometry("320x160")
        self.resizable(False, False)
        self.after(10, self.grab_set)  # wait for window to be viewable before grabbing

        ctk.CTkLabel(self, text="Transcription Model", font=ctk.CTkFont(size=14)).pack(
            pady=(24, 8)
        )
        ctk.CTkOptionMenu(
            self,
            values=MODELS,
            variable=ctk.StringVar(value=self._current.model_id),
            command=self._on_model_change,
        ).pack()

    def _on_model_change(self, model_id: str) -> None:
        self._settings_store.save(Settings(model_id=model_id))
