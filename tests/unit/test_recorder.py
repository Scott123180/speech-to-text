"""Unit tests for AudioRecorder. Write FIRST — must FAIL before implementation."""

import numpy as np
import pytest

from src.exceptions import MicrophoneError, RecorderError


class TestAudioRecorder:
    def test_start_stop_returns_audio_data(self):
        from unittest.mock import MagicMock, patch

        from src.audio.recorder import AudioData, AudioRecorder

        recorder = AudioRecorder()
        mock_stream = MagicMock()
        with patch("sounddevice.InputStream", return_value=mock_stream):
            recorder.start()
            recorder._frames = [np.zeros((1024, 1), dtype=np.float32)]
            result = recorder.stop()

        assert isinstance(result, AudioData)
        assert result.sample_rate == 16000

    def test_start_raises_microphone_error_on_device_failure(self):
        from unittest.mock import patch

        import sounddevice as sd

        from src.audio.recorder import AudioRecorder

        recorder = AudioRecorder()
        # sd.PortAudioError is mocked via conftest to a real Exception subclass
        err = sd.PortAudioError("no device")
        with patch("sounddevice.InputStream", side_effect=err):
            with pytest.raises(MicrophoneError):
                recorder.start()

    def test_stop_raises_recorder_error_when_not_recording(self):
        from src.audio.recorder import AudioRecorder

        recorder = AudioRecorder()
        with pytest.raises(RecorderError):
            recorder.stop()

    def test_audio_data_to_wav_file_creates_file(self, tmp_path):
        from src.audio.recorder import AudioData

        frames = [np.zeros((1024, 1), dtype=np.float32)]
        audio = AudioData(frames=frames, sample_rate=16000)
        path = str(tmp_path / "out.wav")
        audio.to_wav_file(path)

        import os

        assert os.path.exists(path)

    def test_discard_stops_and_clears(self):
        from unittest.mock import MagicMock, patch

        from src.audio.recorder import AudioRecorder

        recorder = AudioRecorder()
        mock_stream = MagicMock()
        with patch("sounddevice.InputStream", return_value=mock_stream):
            recorder.start()
            recorder._frames = [np.zeros((512, 1), dtype=np.float32)]
            recorder.discard()

        assert recorder._frames == []
        assert not recorder._recording

    def test_discard_is_noop_when_not_recording(self):
        from src.audio.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.discard()  # Must not raise


class TestRecorderLevel:
    """The live input level that drives the main window's meter."""

    def _started(self):
        from unittest.mock import MagicMock, patch

        from src.audio.recorder import AudioRecorder

        recorder = AudioRecorder()
        with patch("sounddevice.InputStream", return_value=MagicMock()):
            recorder.start()
        return recorder

    def test_level_is_zero_before_recording(self):
        from src.audio.recorder import AudioRecorder

        assert AudioRecorder().level == 0.0

    def test_level_is_rms_of_latest_block(self):
        recorder = self._started()
        recorder._callback(np.full((256, 1), 0.5, dtype=np.float32), 256, None, None)

        assert recorder.level == pytest.approx(0.5)

    def test_level_tracks_only_the_latest_block(self):
        recorder = self._started()
        recorder._callback(np.full((256, 1), 0.5, dtype=np.float32), 256, None, None)
        recorder._callback(np.zeros((256, 1), dtype=np.float32), 256, None, None)

        assert recorder.level == 0.0

    def test_level_resets_on_stop(self):
        recorder = self._started()
        recorder._callback(np.full((256, 1), 0.5, dtype=np.float32), 256, None, None)
        recorder.stop()

        assert recorder.level == 0.0

    def test_level_resets_on_discard(self):
        recorder = self._started()
        recorder._callback(np.full((256, 1), 0.5, dtype=np.float32), 256, None, None)
        recorder.discard()

        assert recorder.level == 0.0
