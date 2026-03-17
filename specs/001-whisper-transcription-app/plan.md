# Implementation Plan: Whisper Transcription App

**Branch**: `001-whisper-transcription-app` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-whisper-transcription-app/spec.md`

## Summary

Build a local Python desktop application that records microphone audio and
transcribes it using faster-whisper. The user clicks Record, then Accept or
Discard. Accepted audio is transcribed and appended to an editable text area.
The app supports NVIDIA GPU (CUDA) with automatic CPU fallback, and allows
model selection via a Settings screen.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: customtkinter, sounddevice, scipy, faster-whisper, platformdirs, ruff (dev)
**Storage**: JSON config file in OS user config dir (platformdirs); no database
**Testing**: pytest
**Target Platform**: Linux desktop (primary); Windows/macOS supported by all chosen libraries
**Project Type**: desktop-app (single-window GUI)
**Performance Goals**: UI response to button click < 200ms; transcription speed
dictated by faster-whisper model + hardware (no app-introduced delay)
**Constraints**: Offline-capable (all processing local); lightweight install
**Scale/Scope**: Single user, single machine; session-only output (no persistence)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Test-First | All code has tests written first (unit + integration) | ✅ Planned: TDD cycle per task |
| II. Clean Code & SOLID | Each module has one responsibility; services depend on abstractions | ✅ AudioRecorder, TranscriptionEngine, SettingsStore are each independent |
| III. Simplicity & YAGNI | No database, no server, no abstractions beyond what's needed | ✅ Pure Python + 4 libraries |
| IV. UX First | Error messages actionable; spinner during transcription; status label always reflects state | ✅ Defined in data-model state machine |
| V. Integration Testing | Full pipeline test: mic → WAV → transcription → output text | ✅ Planned in tests/integration/ |

**Post-design re-check**: All gates pass. No violations to log.

## Project Structure

### Documentation (this feature)

```text
specs/001-whisper-transcription-app/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # State machine + entities
├── quickstart.md        # Developer setup + validation steps
├── contracts/
│   ├── audio_recorder.md
│   ├── transcription_engine.md
│   └── settings_store.md
└── tasks.md             # Created by /speckit.tasks
```

### Source Code (repository root)

```text
src/
├── app.py                    # Entry point — wires UI + services, starts event loop
├── audio/
│   ├── __init__.py
│   └── recorder.py           # AudioRecorder service
├── transcription/
│   ├── __init__.py
│   └── engine.py             # TranscriptionEngine service (faster-whisper wrapper)
├── config/
│   ├── __init__.py
│   └── settings.py           # SettingsStore + Settings value object
└── ui/
    ├── __init__.py
    ├── main_window.py         # Main screen (Record, Accept, Discard, output area)
    └── settings_window.py     # Settings screen (model selector)

tests/
├── unit/
│   ├── test_recorder.py       # AudioRecorder unit tests (mock sounddevice)
│   ├── test_engine.py         # TranscriptionEngine unit tests (mock faster-whisper)
│   └── test_settings.py       # SettingsStore unit tests (tmp dir)
└── integration/
    └── test_pipeline.py       # Record → transcribe → output integration test
```

**Structure Decision**: Single project (Option 1). No frontend/backend split
needed — this is a self-contained desktop app.

## Complexity Tracking

> No constitution violations to justify.
