"""Entry point: wire services and start the GUI event loop."""

# Preload pip-installed CUDA libraries before ctranslate2 imports them.
# Must run before any faster-whisper / ctranslate2 import.
import ctypes
import os


def _preload_nvidia_libs() -> None:
    """Load CUDA .so files from pip-installed nvidia-* packages into the process.

    When ctranslate2 later calls dlopen("libcublas.so.12"), the dynamic linker
    finds the library already loaded and reuses it — no LD_LIBRARY_PATH needed.
    Silently skips if the nvidia packages are not installed (CPU-only machines).
    """
    try:
        import nvidia  # noqa: PLC0415
    except ImportError:
        return

    # nvidia is a namespace package; __file__ is None, use __path__ instead
    nvidia_root = next(iter(nvidia.__path__), None)
    if not nvidia_root:
        return
    for pkg in os.listdir(nvidia_root):
        lib_dir = os.path.join(nvidia_root, pkg, "lib")
        if not os.path.isdir(lib_dir):
            continue
        for fname in os.listdir(lib_dir):
            if fname.endswith(".so") or ".so." in fname:
                try:
                    ctypes.cdll.LoadLibrary(os.path.join(lib_dir, fname))
                except OSError:
                    pass


_preload_nvidia_libs()

import customtkinter as ctk  # noqa: E402

from src.audio.recorder import AudioRecorder  # noqa: E402
from src.config.settings import SettingsStore  # noqa: E402
from src.transcription.engine import TranscriptionEngine  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    settings_store = SettingsStore()
    settings = settings_store.load()

    ctk.set_widget_scaling(settings.ui_scale)
    ctk.set_window_scaling(settings.ui_scale)

    recorder = AudioRecorder()
    engine = TranscriptionEngine(settings.model_id)

    app = MainWindow(recorder, engine, settings_store)
    app.mainloop()


if __name__ == "__main__":
    main()
