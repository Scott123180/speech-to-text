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


def _click(button):
    """Deliver the events a real mouse click produces on a CTkButton."""
    button.update()
    canvas = button._canvas
    canvas.event_generate("<Enter>")
    canvas.event_generate("<Button-1>")
    canvas.event_generate("<ButtonRelease-1>")
    button.update()


class TestButtonsRespondToClicks:
    def test_clicking_record_starts_recording(self, window):
        _click(window._record_btn)
        window._recorder.start.assert_called_once()

    def test_clicking_discard_while_recording_discards(self, window):
        _click(window._record_btn)
        _click(window._discard_btn)
        window._recorder.discard.assert_called_once()


class TestWindowIdentity:
    def test_window_class_matches_desktop_entry(self, window):
        # GNOME pairs the window with speech-to-text.desktop via StartupWMClass.
        assert window.winfo_class() == "Speech-to-text"

    def test_window_sets_its_own_icon(self, window):
        # Tk can't read an icon back; check every shipped size was loaded.
        sizes = {(img.width(), img.height()) for img in window._icon_images}
        assert sizes == {(n, n) for n in (16, 32, 48, 64, 128, 256)}


class TestEngineInfo:
    def test_model_and_device_are_labelled(self, window):
        assert window._model_label.cget("text") == "Model"
        assert window._model_value.cget("text") == "base"
        assert window._device_label.cget("text") == "Device"
        assert window._device_value.cget("text") == "CPU"


class TestCopyFeedback:
    def test_copy_confirms_on_the_button(self, window):
        window._append_text("hello")
        window._on_copy()
        assert window._copy_btn.cget("text") == "Copied"


class TestUndoClear:
    def test_clear_offers_undo(self, window):
        window._append_text("keep me")
        window._on_clear()
        window.update()
        assert window._notice.winfo_ismapped()

    def test_undo_restores_cleared_text(self, window):
        window._append_text("keep me")
        window._on_clear()
        window._on_undo_clear()
        assert window._output.get("1.0", "end-1c") == "keep me"

    def test_clearing_nothing_offers_no_undo(self, window):
        window._on_clear()
        window.update()
        assert not window._notice.winfo_ismapped()
