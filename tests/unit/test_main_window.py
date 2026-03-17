"""Unit tests for MainWindow copy and clear actions."""
from unittest.mock import MagicMock

import pytest


def _make_window():
    """Instantiate MainWindow with fully mocked dependencies."""
    recorder = MagicMock()
    engine = MagicMock()
    engine.device = "cpu"
    engine.model_id = "base"
    settings_store = MagicMock()
    settings_store.load.return_value = MagicMock(model_id="base")

    from src.ui.main_window import MainWindow

    return MainWindow(recorder, engine, settings_store)


@pytest.fixture
def window():
    try:
        win = _make_window()
        yield win
        win.destroy()
    except Exception:
        pytest.skip("No display available for GUI tests")


class TestCopyAndClear:
    def test_clear_empties_output(self, window):
        window._output.insert("end", "some transcribed text")
        window._on_clear()
        assert window._output.get("1.0", "end-1c") == ""

    def test_copy_puts_text_in_clipboard(self, window):
        window._output.insert("end", "hello world")
        window._on_copy()
        clipboard = window.clipboard_get()
        assert clipboard == "hello world"

    def test_copy_empty_output_does_not_raise(self, window):
        window._on_clear()
        window._on_copy()  # must not raise

    def test_append_text_adds_newline_separator(self, window):
        window._append_text("first")
        window._append_text("second")
        content = window._output.get("1.0", "end-1c")
        assert "first" in content
        assert "second" in content
        assert "\n" in content

    def test_append_empty_string_does_nothing(self, window):
        window._append_text("existing")
        window._append_text("")
        content = window._output.get("1.0", "end-1c")
        assert content == "existing"
