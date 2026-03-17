---

description: "Task list for Whisper Transcription App implementation"
---

# Tasks: Whisper Transcription App

**Input**: Design documents from `specs/001-whisper-transcription-app/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/

**Tests**: Included in every user story phase — TDD is NON-NEGOTIABLE per constitution Principle I.
Write tests first, confirm they FAIL, then implement.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

---

## Phase 1: Setup

**Purpose**: Project scaffolding and tooling configuration

- [X] T001 Create pyproject.toml with all dependencies (customtkinter, sounddevice, scipy, faster-whisper, platformdirs) and dev extras (pytest, ruff) at repo root
- [X] T002 [P] Create src/ package structure: src/__init__.py, src/audio/__init__.py, src/transcription/__init__.py, src/config/__init__.py, src/ui/__init__.py
- [X] T003 [P] Create tests/ package structure: tests/__init__.py, tests/unit/__init__.py, tests/integration/__init__.py
- [X] T004 [P] Configure ruff in pyproject.toml (line-length = 88, select = ["E", "F", "I"])
- [X] T005 [P] Configure pytest in pyproject.toml (testpaths = ["tests"], python_files = "test_*.py")

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared code required by ALL user stories — no story can begin until this phase is done.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Create AppState enum (IDLE, RECORDING, TRANSCRIBING) in src/app_state.py
- [X] T007 [P] Create custom exceptions in src/exceptions.py: MicrophoneError, RecorderError, ModelNotFoundError, TranscriptionError, SettingsError

**Checkpoint**: Foundation ready — user story work can begin.

---

## Phase 3: User Story 1 — Record and Transcribe Speech (Priority: P1) 🎯 MVP

**Goal**: User can click Record, speak, click Accept, and see transcribed text in the output area.

**Independent Test**: Launch `python -m src.app`, click Record, speak, click Accept. Transcribed text appears. App returns to Idle.

### Tests for User Story 1 — Write FIRST, Confirm FAILING ⚠️

- [X] T008 [P] [US1] Write failing unit tests for AudioRecorder (start, stop returning AudioData, MicrophoneError on missing device) in tests/unit/test_recorder.py
- [X] T009 [P] [US1] Write failing unit tests for TranscriptionEngine (transcribe returns TranscriptionResult, CUDA→CPU fallback, TranscriptionError on failure) in tests/unit/test_engine.py
- [X] T010 [US1] Write failing integration test: record dummy audio → write WAV → transcribe → assert non-empty text returned in tests/integration/test_pipeline.py

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement AudioRecorder in src/audio/recorder.py: start() opens sounddevice.InputStream at 16 kHz mono float32, stop() returns AudioData(frames, sample_rate=16000) with to_wav_file(path) method; raises MicrophoneError on device failure
- [X] T012 [P] [US1] Implement TranscriptionEngine in src/transcription/engine.py: __init__ tries device="cuda" compute_type="float16" → "int8_float16" → falls back to device="cpu" compute_type="int8"; transcribe(path) returns TranscriptionResult(text, model_id); exposes device property
- [X] T013 [US1] Implement MainWindow in src/ui/main_window.py: IDLE state shows Record button + editable output CTkTextbox + status label; RECORDING state swaps to Accept (✓) / Discard (✗) buttons; TRANSCRIBING state shows spinner + disables record controls; state transitions driven by AppState enum
- [X] T014 [US1] Implement src/app.py entry point: instantiate AudioRecorder + TranscriptionEngine, wire Record button → start(), Accept button → stop() + background Thread(transcribe) + queue.Queue poll via root.after(100) → append result to output area; handle MicrophoneError and TranscriptionError with CTkMessageBox

**Checkpoint**: US1 fully functional and independently testable. `pytest tests/unit/test_recorder.py tests/unit/test_engine.py tests/integration/` should pass.

---

## Phase 4: User Story 2 — Discard a Recording (Priority: P2)

**Goal**: User can click Discard during recording to cancel and return to Idle with no text added.

**Independent Test**: Click Record, wait, click Discard. No text appended; app returns to Idle state.

### Tests for User Story 2 — Write FIRST, Confirm FAILING ⚠️

- [X] T015 [US2] Write failing unit test for AudioRecorder.discard(): verify no AudioData returned, no WAV written, recorder resets to clean state in tests/unit/test_recorder.py

### Implementation for User Story 2

- [X] T016 [US2] Implement AudioRecorder.discard() in src/audio/recorder.py: stops InputStream and discards all buffered frames; no-op if not recording
- [X] T017 [US2] Wire Discard button in src/ui/main_window.py and src/app.py: calls recorder.discard(), transitions app state back to IDLE, no queue message sent

**Checkpoint**: US1 and US2 both independently functional. Discard returns to Idle cleanly.

---

## Phase 5: User Story 3 — Edit and Copy Transcribed Text (Priority: P2)

**Goal**: User can edit transcribed text inline, copy it to clipboard, and clear the output area.

**Independent Test**: After transcription, edit a word in the text area. Click Copy → paste elsewhere and confirm text matches (with edit). Click Clear → text area is empty.

### Tests for User Story 3 — Write FIRST, Confirm FAILING ⚠️

- [X] T018 [P] [US3] Write failing unit tests for copy and clear actions in tests/unit/test_main_window.py: mock CTkTextbox, assert clipboard content equals text area content; assert clear empties widget

### Implementation for User Story 3

- [X] T019 [US3] Implement Copy to Clipboard button in src/ui/main_window.py: reads full CTkTextbox content and calls root.clipboard_clear() + root.clipboard_append(text)
- [X] T020 [US3] Implement Clear button in src/ui/main_window.py: deletes all text from CTkTextbox (CTkTextbox.delete("1.0", "end")); confirm empty string on next Copy

**Checkpoint**: US1, US2, and US3 all independently functional.

---

## Phase 6: User Story 4 — Switch Transcription Model (Priority: P3)

**Goal**: User opens Settings, selects a different model, returns to main screen, and the next transcription uses the new model.

**Independent Test**: Open Settings, change model to `small`, close. Record and Accept. App loads and uses `small` model for transcription.

### Tests for User Story 4 — Write FIRST, Confirm FAILING ⚠️

- [X] T021 [P] [US4] Write failing unit tests for SettingsStore in tests/unit/test_settings.py: load() returns default Settings(model_id="base") on missing file; save() writes JSON; load() after save() returns saved model_id; invalid model_id resets to "base"

### Implementation for User Story 4

- [X] T022 [P] [US4] Implement SettingsStore and Settings in src/config/settings.py: load() reads JSON from platformdirs.user_config_dir("speech-to-text")/settings.json (returns defaults if missing/corrupt); save(Settings) writes atomically; validates model_id against allowed list
- [X] T023 [US4] Implement SettingsWindow in src/ui/settings_window.py: CTkToplevel window opened from main screen gear icon; contains CTkOptionMenu with model choices (tiny, base, small, medium, large-v3, distil-large-v3); on selection change calls SettingsStore.save()
- [X] T024 [US4] Wire gear icon / Settings button in src/ui/main_window.py: opens SettingsWindow; on window close, app.py reads updated SettingsStore and re-initializes TranscriptionEngine with new model_id for the next transcription

**Checkpoint**: All 4 user stories fully functional and independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality and UX improvements that span multiple user stories

- [X] T025 [P] Add status bar message showing active device ("Using GPU (CUDA)" or "Using CPU") after TranscriptionEngine initializes in src/ui/main_window.py
- [X] T026 [P] Ensure all error paths (MicrophoneError, TranscriptionError, ModelNotFoundError) show CTkMessageBox with human-readable message and return to IDLE in src/app.py
- [ ] T027 Run quickstart.md validation manually: launch app, complete all 10 steps, confirm each succeeds
- [X] T028 [P] Run `ruff check src/ tests/` and fix any violations
- [X] T029 Run full test suite `pytest` and confirm all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — MVP, implement first
- **US2 (Phase 4)**: Depends on US1 (AudioRecorder.start/stop already exist)
- **US3 (Phase 5)**: Depends on US1 (output text area exists)
- **US4 (Phase 6)**: Depends on US1 (TranscriptionEngine exists)
- **Polish (Phase 7)**: Depends on all desired stories complete

### Within Each User Story

1. Write tests → confirm FAIL (TDD mandatory, per constitution Principle I)
2. Implement services (recorder, engine, settings)
3. Implement UI components
4. Wire in app.py
5. Run tests → confirm PASS → refactor if needed

### Parallel Opportunities

**Phase 1**: T002, T003, T004, T005 can all run in parallel after T001.

**Phase 3**:
- T008, T009 (test writing) can run in parallel
- T011, T012 (service implementation) can run in parallel after T008/T009 confirm failing

**Phase 7**: T025, T026, T028 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Write tests in parallel (different files, no deps):
Task: "T008 — Write failing tests for AudioRecorder in tests/unit/test_recorder.py"
Task: "T009 — Write failing tests for TranscriptionEngine in tests/unit/test_engine.py"

# Implement services in parallel after tests confirmed failing:
Task: "T011 — Implement AudioRecorder in src/audio/recorder.py"
Task: "T012 — Implement TranscriptionEngine in src/transcription/engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (T008–T014)
4. **STOP and VALIDATE**: Test US1 independently (record → accept → text appears)
5. Demo if ready

### Incremental Delivery

1. Setup + Foundational → scaffolding ready
2. US1 (P1) → Working record + transcribe → **MVP**
3. US2 (P2) → Add discard path
4. US3 (P2) → Add copy + clear
5. US4 (P3) → Add model switching
6. Polish → UX + error handling + tests pass

---

## Notes

- TDD cycle MUST be visible in commit history (failing test commit → implementation commit)
- `[P]` tasks = different files, no dependency on incomplete tasks
- `[Story]` label maps each task to its user story for traceability
- Temp WAV files written by AudioRecorder.stop() MUST be deleted in app.py after TranscriptionEngine.transcribe() completes
- TranscriptionEngine initialization (model loading) is slow — do it once at startup, not per transcription
- Model switch (US4) requires re-initializing TranscriptionEngine with the new model_id
