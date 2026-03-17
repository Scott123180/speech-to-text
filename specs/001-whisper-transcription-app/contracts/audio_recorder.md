# Contract: AudioRecorder

**Module**: `src/audio/recorder.py`
**Type**: Internal service interface

## Responsibility

Capture audio from the default system microphone into an in-memory buffer.
Provide start/stop control. Has no knowledge of transcription or the UI.

## Interface

```
AudioRecorder
│
├── start() → None
│     Begins streaming audio from the default mic into an internal buffer.
│     Raises: MicrophoneError if microphone is unavailable or permission denied.
│
├── stop() → AudioData
│     Stops the stream and returns the accumulated audio.
│     Returns: AudioData(frames: list[np.ndarray], sample_rate: int)
│     Raises: RecorderError if called without a prior start().
│
└── discard() → None
      Stops the stream and discards accumulated audio.
      Safe to call even if not currently recording (no-op).
```

## AudioData (return type of stop())

```
AudioData
├── frames: list[np.ndarray]   # Raw audio chunks (float32, mono)
├── sample_rate: int            # Always 16000
└── to_wav_file(path: str) → None
      Writes audio to a WAV file at the given path.
      16 kHz, mono, float32.
```

## Error Types

| Error | Condition |
|-------|-----------|
| `MicrophoneError` | Device not found, permission denied, or device busy |
| `RecorderError` | Protocol violation (e.g., stop() before start()) |

## Constraints

- MUST use sample rate 16000 Hz (required by faster-whisper).
- MUST record mono (1 channel).
- MUST NOT block the calling thread during recording (uses streaming callback).
- MUST NOT have any knowledge of the transcription engine or UI.
