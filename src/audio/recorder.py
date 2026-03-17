import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd

from src.exceptions import MicrophoneError, RecorderError

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"


class AudioData:
    """Captured audio returned by AudioRecorder.stop()."""

    def __init__(self, frames: list, sample_rate: int) -> None:
        self.frames = frames
        self.sample_rate = sample_rate

    def to_wav_file(self, path: str) -> None:
        """Write accumulated frames to a WAV file at *path*."""
        if self.frames:
            audio = np.concatenate(self.frames, axis=0)
        else:
            audio = np.array([], dtype=np.float32)
        wav.write(path, self.sample_rate, audio)


class AudioRecorder:
    """Captures microphone audio into an in-memory buffer."""

    def __init__(self) -> None:
        self._frames: list = []
        self._stream: sd.InputStream | None = None
        self._recording: bool = False

    def start(self) -> None:
        """Open an audio stream from the default microphone."""
        if self._recording:
            raise RecorderError("Already recording")
        self._frames = []
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=self._callback,
            )
            self._stream.start()
            self._recording = True
        except sd.PortAudioError as exc:
            raise MicrophoneError(str(exc)) from exc

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        self._frames.append(indata.copy())

    def stop(self) -> AudioData:
        """Stop recording and return the captured audio."""
        if not self._recording:
            raise RecorderError("Not currently recording")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._recording = False
        return AudioData(list(self._frames), SAMPLE_RATE)

    def discard(self) -> None:
        """Stop recording and throw away all captured audio."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._frames = []
        self._recording = False
