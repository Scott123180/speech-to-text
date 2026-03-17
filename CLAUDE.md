# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local desktop speech-to-text app using faster-whisper (CTranslate2-based). The user records
audio, then accepts or discards it. Accepted audio is transcribed and appended to an editable
text area. Supports NVIDIA GPU (CUDA) with automatic CPU fallback.

## Development Workflow (Speckit)

This project uses **Speckit 0.3.0** for specification-driven development. The standard workflow is:

1. `/speckit.constitution` — Define project principles and constraints
2. `/speckit.specify` — Write feature specification
3. `/speckit.clarify` — Resolve ambiguities in the spec
4. `/speckit.plan` — Generate implementation plan
5. `/speckit.tasks` — Break plan into actionable tasks
6. `/speckit.implement` — Execute tasks
7. `/speckit.checklist` — Run quality gates

Speckit artifacts live in `.specify/`, Claude commands in `.claude/commands/`.
Feature specs live in `specs/<NNN>-feature-name/`.

## Build/Test Commands

```bash
# Install (from repo root, venv activated)
pip install -e ".[dev]"

# Also install CUDA runtime libs for GPU acceleration (NVIDIA only, optional)
pip install -e ".[cuda]"

# Run the app
python -m src.app

# Run all tests
pytest

# Single test file
pytest tests/unit/test_recorder.py

# Integration tests only
pytest tests/integration/

# Lint / format
ruff check src/ tests/
ruff format src/ tests/
```

## Architecture

**Stack**: Python 3.11+, customtkinter (GUI), sounddevice (mic capture), faster-whisper (transcription),
platformdirs (config path), ruff (linting), pytest (testing).

**Source layout**:
```
src/
├── app.py                 # Entry point — wires services + starts GUI event loop
├── audio/recorder.py      # AudioRecorder: mic capture via sounddevice
├── transcription/engine.py # TranscriptionEngine: faster-whisper wrapper
├── config/settings.py     # SettingsStore: JSON config in OS user config dir
└── ui/
    ├── main_window.py     # Main screen (Record/Accept/Discard, output text area)
    └── settings_window.py # Settings screen (model selector)
```

**Key design decisions** (see `specs/001-whisper-transcription-app/research.md` for full rationale):
- Services (AudioRecorder, TranscriptionEngine, SettingsStore) are independent and know nothing about the UI.
- Recording and transcription run in background `threading.Thread`s; results returned to the GUI via `queue.Queue`.
- faster-whisper is initialized with `device="cuda"` first; falls back to `device="cpu"` on `RuntimeError`.
- CTranslate2 loads CUDA libs lazily on first inference (not at init). `app.py` preloads the pip-installed `nvidia-*-cu12` `.so` files via `ctypes` before any import, so `dlopen` finds them. No `LD_LIBRARY_PATH` needed.
- Audio is captured at 16 kHz mono float32, written to a temp WAV, passed by path to faster-whisper, then deleted.
- App state machine has three states: IDLE → RECORDING → TRANSCRIBING → IDLE.

**Constitution**: `specs/001-whisper-transcription-app/contracts/` for service interface specs.
TDD is mandatory (Red-Green-Refactor, tests committed before implementation).
