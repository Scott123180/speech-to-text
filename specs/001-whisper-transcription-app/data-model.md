# Data Model: Whisper Transcription App

**Date**: 2026-03-16
**Branch**: `001-whisper-transcription-app`

## App State Machine

The app is always in exactly one of three states. All UI controls are derived
from this state.

```
          ┌─────────┐
          │  IDLE   │◄────────────────────────────┐
          └────┬────┘                             │
               │ Record clicked                   │
               ▼                                  │
        ┌────────────┐   Discard clicked          │
        │ RECORDING  │───────────────────────────►│
        └─────┬──────┘                            │
              │ Accept clicked                    │
              ▼                                   │
       ┌─────────────┐  transcription done        │
       │TRANSCRIBING │───────────────────────────►┘
       └─────────────┘  (or error)
```

### State: IDLE
- Record button visible and enabled.
- Accept and Discard buttons hidden.
- Status label: "Idle".
- Output text area: editable.
- Copy and Clear buttons: enabled.

### State: RECORDING
- Record button hidden.
- Accept (✓) and Discard (✗) buttons visible and enabled.
- Status label: "Recording…".
- Output text area: editable.
- Copy and Clear buttons: enabled.
- Audio is accumulating in memory buffer.

### State: TRANSCRIBING
- Record, Accept, Discard buttons all disabled/hidden.
- Spinner/loading indicator visible.
- Status label: "Transcribing…".
- Output text area: editable.
- Copy and Clear buttons: enabled.
- Background thread is running `model.transcribe()`.

## Entities

### Recording (ephemeral, in-memory only)

Represents a captured audio session. Created when recording starts,
consumed when Accept is clicked, discarded when Discard is clicked.
Never written to a user-visible file.

| Field | Type | Description |
|-------|------|-------------|
| audio_frames | list[np.ndarray] | Accumulated audio chunks from mic stream |
| sample_rate | int | Always 16000 Hz |
| channels | int | Always 1 (mono) |

Lifecycle:
1. Created empty when Record is clicked.
2. Filled via sounddevice InputStream callback.
3. On Accept: written to a temp file → path passed to transcription engine →
   temp file deleted after transcription completes.
4. On Discard: dropped immediately.

---

### Transcript (ephemeral, session-only)

A single text result from one Accept→transcribe cycle.

| Field | Type | Description |
|-------|------|-------------|
| text | str | Raw text from faster-whisper |
| model_used | str | Model ID that produced this transcript (e.g., "base") |

Lifecycle:
- Created by TranscriptionEngine.
- Immediately appended to Output (in-memory).
- Not independently persisted.

---

### Output (session-only, in-memory)

The accumulated editable text visible in the main window's text area.

| Field | Type | Description |
|-------|------|-------------|
| content | str | Full current text, including user edits |

Rules:
- New Transcripts are appended with a `\n` separator.
- User may edit freely at any time.
- Cleared to empty string on Clear action.
- Copied to clipboard verbatim on Copy action.
- Not persisted across sessions (intentional v1 scope decision).

---

### ModelConfiguration (persisted to disk)

User's selected transcription model. Lives in the OS user config directory.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| model_id | str | `"base"` | faster-whisper model name |
| device | str | `"cuda"` | "cuda" or "cpu" (auto-detected at init) |
| compute_type | str | auto | Derived from device at runtime |

Validation:
- `model_id` MUST be one of: `tiny`, `base`, `small`, `medium`, `large-v3`,
  `distil-large-v3`.
- `device` is set at startup via GPU probe, not user-editable (user only picks
  the model name).

Persistence:
- Written as JSON: `~/.config/speech-to-text/settings.json` (Linux).
- Read at app startup; written on change.

---

## Derived UI Controls (from State)

| Control | IDLE | RECORDING | TRANSCRIBING |
|---------|------|-----------|--------------|
| Record button | visible + enabled | hidden | hidden |
| Accept (✓) | hidden | visible + enabled | hidden |
| Discard (✗) | hidden | visible + enabled | hidden |
| Spinner | hidden | hidden | visible |
| Status label | "Idle" | "Recording…" | "Transcribing…" |
| Output text area | editable | editable | editable |
| Copy button | enabled | enabled | enabled |
| Clear button | enabled | enabled | enabled |
