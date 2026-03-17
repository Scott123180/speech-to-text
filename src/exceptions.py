class MicrophoneError(Exception):
    """Raised when the microphone is unavailable or permission is denied."""


class RecorderError(Exception):
    """Raised on protocol violations (e.g. stop() before start())."""


class ModelNotFoundError(Exception):
    """Raised when a requested faster-whisper model is invalid or missing."""


class TranscriptionError(Exception):
    """Raised when transcription fails at runtime."""


class SettingsError(Exception):
    """Raised on settings I/O failure."""
