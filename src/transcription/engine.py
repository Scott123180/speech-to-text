from dataclasses import dataclass

from faster_whisper import WhisperModel

from src.exceptions import ModelNotFoundError, TranscriptionError

VALID_MODELS = frozenset(
    {"tiny", "base", "small", "medium", "large-v3", "distil-large-v3"}
)

_CUDA_CANDIDATES = [
    ("cuda", "float16"),
    ("cuda", "int8_float16"),
]
_CPU_FALLBACK = ("cpu", "int8")

# Keywords that indicate a lazy CUDA runtime-loading failure.
# CTranslate2 loads GPU libraries on first inference, not on model init,
# so these errors surface during transcribe() rather than __init__().
_CUDA_ERROR_KEYWORDS = ("cuda", "cublas", "libcuda", "cufft", "cudnn")


def _is_cuda_runtime_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in _CUDA_ERROR_KEYWORDS)


@dataclass
class TranscriptionResult:
    text: str
    model_id: str


class TranscriptionEngine:
    """Wraps faster-whisper; selects GPU automatically, falls back to CPU."""

    def __init__(self, model_id: str) -> None:
        if model_id not in VALID_MODELS:
            raise ModelNotFoundError(f"Unknown model: '{model_id}'")
        self._model_id = model_id
        self._device, self._model = self._load_model(model_id)

    def _load_model(self, model_id: str) -> tuple[str, WhisperModel]:
        for device, compute_type in _CUDA_CANDIDATES:
            try:
                model = WhisperModel(model_id, device=device, compute_type=compute_type)
                return device, model
            except (RuntimeError, ValueError):
                continue
        return self._load_cpu_model(model_id)

    def _load_cpu_model(self, model_id: str | None = None) -> tuple[str, WhisperModel]:
        target = model_id or self._model_id
        device, compute_type = _CPU_FALLBACK
        try:
            model = WhisperModel(target, device=device, compute_type=compute_type)
            return device, model
        except Exception as exc:
            msg = f"Failed to load model '{target}': {exc}"
            raise TranscriptionError(msg) from exc

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe the WAV file at *audio_path*. Run from a background thread."""
        try:
            segments, _ = self._model.transcribe(audio_path)
            text = " ".join(seg.text for seg in segments).strip()
            return TranscriptionResult(text=text, model_id=self._model_id)
        except TranscriptionError:
            raise
        except Exception as exc:
            # CTranslate2 loads CUDA libs lazily on first inference, not at init.
            # If that fails, transparently switch to CPU and retry once.
            if self._device != "cpu" and _is_cuda_runtime_error(exc):
                self._device, self._model = self._load_cpu_model()
                try:
                    segments, _ = self._model.transcribe(audio_path)
                    text = " ".join(seg.text for seg in segments).strip()
                    return TranscriptionResult(text=text, model_id=self._model_id)
                except Exception as retry_exc:
                    raise TranscriptionError(str(retry_exc)) from retry_exc
            raise TranscriptionError(str(exc)) from exc

    @property
    def device(self) -> str:
        return self._device

    @property
    def model_id(self) -> str:
        return self._model_id
