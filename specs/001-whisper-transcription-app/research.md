# Research: Whisper Transcription App

**Date**: 2026-03-16
**Branch**: `001-whisper-transcription-app`

## Decision Log

---

### Decision 1: GUI Framework → CustomTkinter

**Decision**: Use **CustomTkinter** (wraps Tkinter, MIT license).

**Rationale**:
- Ships as a pure Python package (~5 MB overhead on top of Tkinter, which is
  bundled with CPython). This is the lightest option after plain Tkinter.
- Provides modern-looking widgets (rounded buttons, dark mode, high-DPI) with
  zero external C dependencies beyond what Tkinter already ships.
- API is nearly identical to Tkinter — simplest learning curve.
- Actively maintained (v5.2+, MIT license).
- Handles all required UI: buttons, editable text widget, status label, second
  settings window.

**Alternatives considered**:
- **Dear PyGui**: GPU-accelerated UI — impressive but overkill for 3 buttons
  and a text area. Adds unnecessary complexity.
- **wxPython**: Native look, but 6× slower startup and requires a separate
  install. Not worth it.
- **PySimpleGUI**: Simplest API, but v5 moved to a commercial license.
  FreeSimpleGUI fork exists but adds maintenance risk.
- **Electron/Tauri**: Cross-platform web-based — the user explicitly wants
  simple and lightweight; both are far heavier than a Python GUI.

---

### Decision 2: Audio Recording → sounddevice

**Decision**: Use **sounddevice** for microphone capture.

**Rationale**:
- Installs via pip with pre-built wheels on all platforms (no PortAudio
  compilation step like PyAudio requires).
- Records directly to NumPy float32 arrays — native integration with
  faster-whisper.
- `InputStream` class supports a callback-based non-blocking pattern that
  accumulates audio in a buffer while the GUI remains responsive.

**faster-whisper input format**:
- Save the accumulated NumPy array to a temporary WAV file at 16 kHz mono
  float32 using `scipy.io.wavfile.write()`.
- Pass the file path to `model.transcribe(path)` — this is more reliable than
  passing a raw array directly (documented stability issues with array path).
- Temp file is deleted after transcription completes.

**Alternatives considered**:
- **PyAudio**: Lower-level, requires compiling PortAudio on Linux/macOS.
  Common install failures. No advantage for this use case.

---

### Decision 3: GPU Support (CUDA) with CPU Fallback

**Decision**: Explicit device selection — try `"cuda"`, fall back to `"cpu"`.

**Rationale**:
- faster-whisper does NOT automatically fall back; a RuntimeError is raised
  if CUDA is unavailable or the ctranslate2 package was not compiled with
  CUDA support.
- The app must handle this gracefully at model initialization time and surface
  a clear status message (e.g., "GPU not available — using CPU").

**Compute type by device**:
- `device="cuda"` → `compute_type="float16"` (fastest; requires GPU FP16).
  If FP16 fails, fall back to `compute_type="int8_float16"`.
- `device="cpu"` → `compute_type="int8"` (best speed/accuracy tradeoff on CPU).

**CUDA runtime requirements** (user's responsibility to install):
- CUDA 12.3+ + cuDNN v9 → `ctranslate2 >= 4.5.0` (pip default)
- CUDA 11.x + cuDNN 8.x → `ctranslate2 == 3.24.0`
- CUDA 12.x + cuDNN 8.x → `ctranslate2 == 4.4.0`

**device="auto"**: Not reliably supported in faster-whisper; avoided.

---

### Decision 4: Threading Model → threading.Thread + queue.Queue

**Decision**: Background threads with a `queue.Queue` for GUI communication.

**Rationale**:
- Tkinter's event loop is single-threaded and blocking. Recording audio and
  running transcription MUST happen in daemon threads.
- `queue.Queue` is thread-safe; background threads push results into it.
- The main thread polls the queue with `root.after(100, poll_fn)` — the
  standard Tkinter-safe pattern for updating widgets from worker threads.
- Keeps the design simple (no asyncio event loop, no thread pools) in line
  with Principle III (Simplicity & YAGNI).

**Alternatives considered**:
- **concurrent.futures.ThreadPoolExecutor**: Adds abstraction without benefit
  for 1–2 concurrent operations.
- **asyncio**: Not compatible with Tkinter's event loop without bridge
  libraries. Rejected (complexity, YAGNI).

---

### Decision 5: Project Language & Tooling

| Aspect | Decision |
|--------|---------|
| Language | Python 3.11+ |
| GUI | customtkinter |
| Audio | sounddevice + scipy |
| Transcription | faster-whisper |
| Testing | pytest |
| Packaging | pyproject.toml (setuptools) |
| Linting | ruff |
| Type checking | mypy (optional, for service modules) |
| Config persistence | JSON file in user config dir (`platformdirs`) |

---

### Decision 6: Settings Persistence

**Decision**: JSON file stored in the OS user config directory via `platformdirs`.

**Rationale**:
- `platformdirs` (MIT) gives the correct OS-specific config path:
  - Linux: `~/.config/speech-to-text/settings.json`
  - macOS: `~/Library/Application Support/speech-to-text/settings.json`
  - Windows: `%APPDATA%\speech-to-text\settings.json`
- Simple key/value JSON — no database needed.
- Persists model selection across sessions.
