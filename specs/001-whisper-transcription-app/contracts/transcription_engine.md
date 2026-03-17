# Contract: TranscriptionEngine

**Module**: `src/transcription/engine.py`
**Type**: Internal service interface

## Responsibility

Wrap faster-whisper to transcribe a WAV file to text. Handle GPU/CPU device
selection transparently. Has no knowledge of the UI or audio recording.

## Interface

```
TranscriptionEngine
│
├── __init__(model_id: str) → None
│     Initializes the faster-whisper model.
│     Attempts CUDA first; falls back to CPU on RuntimeError.
│     Raises: ModelNotFoundError if model_id is invalid or files missing.
│
├── transcribe(audio_path: str) → TranscriptionResult
│     Transcribes the WAV file at audio_path.
│     Blocking call — MUST be run from a background thread.
│     Returns: TranscriptionResult
│     Raises: TranscriptionError on failure.
│
├── device: str          (read-only)
│     "cuda" or "cpu" — set at initialization.
│
└── model_id: str        (read-only)
      The model currently loaded (e.g., "base").
```

## TranscriptionResult (return type of transcribe())

```
TranscriptionResult
├── text: str        # Full transcribed text, stripped of leading/trailing whitespace
└── model_id: str    # Model that produced this result
```

## Error Types

| Error | Condition |
|-------|-----------|
| `ModelNotFoundError` | model_id not valid or model files not present locally |
| `TranscriptionError` | Runtime failure during transcription (OOM, corrupt audio, etc.) |

## Device Selection Logic

```
1. Try: WhisperModel(model_id, device="cuda", compute_type="float16")
2. On RuntimeError → Try: WhisperModel(model_id, device="cuda", compute_type="int8_float16")
3. On RuntimeError → Fall back: WhisperModel(model_id, device="cpu", compute_type="int8")
4. Log/surface which device was selected (surfaced via device property)
```

## Constraints

- MUST NOT block the GUI thread (called from background thread only).
- MUST delete the temporary audio file after transcription (caller's
  responsibility via AudioData.to_wav_file + cleanup).
- MUST expose which device is in use via the `device` property.
- MUST NOT have any knowledge of the UI or audio recording.
