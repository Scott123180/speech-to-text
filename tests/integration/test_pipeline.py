"""Integration test: AudioData → WAV → TranscriptionEngine → TranscriptionResult."""
import numpy as np


class TestTranscriptionPipeline:
    def test_audio_data_to_wav_to_transcription(self, tmp_path):
        from unittest.mock import MagicMock, patch

        from src.audio.recorder import AudioData
        from src.transcription.engine import TranscriptionEngine, TranscriptionResult

        # Build a 1-second silent audio clip
        audio = AudioData(
            frames=[np.zeros((16000, 1), dtype=np.float32)],
            sample_rate=16000,
        )
        wav_path = str(tmp_path / "clip.wav")
        audio.to_wav_file(wav_path)

        # Mock faster-whisper so no GPU/model download is required
        mock_segment = MagicMock()
        mock_segment.text = "test transcription"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())

        with patch("src.transcription.engine.WhisperModel", return_value=mock_model):
            engine = TranscriptionEngine("base")
            result = engine.transcribe(wav_path)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "test transcription"
        assert result.model_id == "base"

        import os
        assert os.path.exists(wav_path)  # Caller is responsible for cleanup
