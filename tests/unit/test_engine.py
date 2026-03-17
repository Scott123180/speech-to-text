"""Unit tests for TranscriptionEngine. Write FIRST — must FAIL before implementation."""
import pytest

from src.exceptions import ModelNotFoundError, TranscriptionError


class TestTranscriptionEngine:
    def _make_mock_model(self, text="hello world"):
        from unittest.mock import MagicMock

        mock_segment = MagicMock()
        mock_segment.text = text
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())
        return mock_model

    def test_init_tries_cuda_first(self):
        from unittest.mock import patch

        from src.transcription.engine import TranscriptionEngine

        mock_model = self._make_mock_model()
        target = "src.transcription.engine.WhisperModel"
        with patch(target, return_value=mock_model) as mock_cls:
            TranscriptionEngine("base")

        first_call_device = mock_cls.call_args_list[0][1]["device"]
        assert first_call_device == "cuda"

    def test_falls_back_to_cpu_when_cuda_unavailable(self):
        from unittest.mock import patch

        from src.transcription.engine import TranscriptionEngine

        mock_model = self._make_mock_model()

        def side_effect(*args, **kwargs):
            if kwargs.get("device") == "cuda":
                raise RuntimeError("CUDA not available")
            return mock_model

        with patch("src.transcription.engine.WhisperModel", side_effect=side_effect):
            engine = TranscriptionEngine("base")

        assert engine.device == "cpu"

    def test_transcribe_returns_result(self):
        from unittest.mock import patch

        from src.transcription.engine import TranscriptionEngine, TranscriptionResult

        mock_model = self._make_mock_model("hello world")
        with patch("src.transcription.engine.WhisperModel", return_value=mock_model):
            engine = TranscriptionEngine("base")
            result = engine.transcribe("/tmp/test.wav")

        assert isinstance(result, TranscriptionResult)
        assert "hello" in result.text
        assert result.model_id == "base"

    def test_invalid_model_raises_model_not_found(self):
        from src.transcription.engine import TranscriptionEngine

        with pytest.raises(ModelNotFoundError):
            TranscriptionEngine("nonexistent-model")

    def test_transcription_error_on_runtime_failure(self):
        from unittest.mock import MagicMock, patch

        from src.transcription.engine import TranscriptionEngine

        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("OOM")
        with patch("src.transcription.engine.WhisperModel", return_value=mock_model):
            engine = TranscriptionEngine("base")
            with pytest.raises(TranscriptionError):
                engine.transcribe("/tmp/bad.wav")

    def test_lazy_cuda_failure_falls_back_to_cpu(self):
        """CTranslate2 loads CUDA libs on first inference; engine must retry on CPU."""
        from unittest.mock import MagicMock, patch

        from src.transcription.engine import TranscriptionEngine, TranscriptionResult

        cuda_model = MagicMock()
        cuda_model.transcribe.side_effect = RuntimeError(
            "Library libcublas.so.12 is not found or cannot be loaded"
        )

        cpu_segment = MagicMock()
        cpu_segment.text = "hello from cpu"
        cpu_model = MagicMock()
        cpu_model.transcribe.return_value = ([cpu_segment], MagicMock())

        def model_factory(*args, **kwargs):
            return cuda_model if kwargs.get("device") == "cuda" else cpu_model

        with patch("src.transcription.engine.WhisperModel", side_effect=model_factory):
            engine = TranscriptionEngine("base")
            # First call should hit CUDA, detect the lazy failure, retry on CPU
            result = engine.transcribe("/tmp/test.wav")

        assert isinstance(result, TranscriptionResult)
        assert result.text == "hello from cpu"
        assert engine.device == "cpu"

    def test_device_property_reflects_selected_device(self):
        from unittest.mock import patch

        from src.transcription.engine import TranscriptionEngine

        mock_model = self._make_mock_model()
        with patch("src.transcription.engine.WhisperModel", return_value=mock_model):
            engine = TranscriptionEngine("base")

        assert engine.device in ("cuda", "cpu")

    def test_model_id_property(self):
        from unittest.mock import patch

        from src.transcription.engine import TranscriptionEngine

        mock_model = self._make_mock_model()
        with patch("src.transcription.engine.WhisperModel", return_value=mock_model):
            engine = TranscriptionEngine("small")

        assert engine.model_id == "small"
