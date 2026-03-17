"""Pytest configuration: mock system-level dependencies for unit tests."""
import sys
from unittest.mock import MagicMock


class _FakePortAudioError(Exception):
    """Stand-in for sounddevice.PortAudioError in tests without PortAudio installed."""


# Mock sounddevice so tests run without a PortAudio system library.
# Individual tests that need specific behaviour still patch sd.InputStream etc.
if "sounddevice" not in sys.modules:
    _mock_sd = MagicMock()
    _mock_sd.PortAudioError = _FakePortAudioError
    sys.modules["sounddevice"] = _mock_sd
