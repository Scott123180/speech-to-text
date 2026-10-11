"""Unit tests for theme helpers. Write FIRST — must FAIL before implementation."""

from unittest.mock import patch

import pytest

from src.ui.theme import blend, parse_xft_dpi


class TestParseXftDpi:
    def test_reads_dpi_from_xrdb_output(self):
        output = "Xcursor.size:\t48\nXft.antialias:\t1\nXft.dpi:\t192\n"
        assert parse_xft_dpi(output) == 192.0

    def test_accepts_fractional_dpi(self):
        assert parse_xft_dpi("Xft.dpi:\t144.5\n") == 144.5

    def test_missing_entry_returns_none(self):
        assert parse_xft_dpi("Xcursor.size:\t48\n") is None

    def test_garbage_value_returns_none(self):
        assert parse_xft_dpi("Xft.dpi:\tlots\n") is None


class TestDisplayScale:
    def test_is_xft_dpi_over_96(self):
        from src.ui import theme

        with patch.object(theme, "xft_dpi", return_value=192.0):
            assert theme.display_scale() == 2.0

    def test_defaults_to_one_without_xft_dpi(self):
        from src.ui import theme

        with patch.object(theme, "xft_dpi", return_value=None):
            assert theme.display_scale() == 1.0


class TestBlend:
    def test_zero_keeps_the_colour(self):
        with patch("customtkinter.get_appearance_mode", return_value="Light"):
            assert blend(("#a4262c", "#ff9a9a"), ("#ffffff", "#1e1e1e"), 0) == "#a4262c"

    def test_one_reaches_the_target(self):
        with patch("customtkinter.get_appearance_mode", return_value="Dark"):
            assert blend(("#a4262c", "#ff9a9a"), ("#ffffff", "#1e1e1e"), 1) == "#1e1e1e"

    def test_halfway_mixes_channels(self):
        with patch("customtkinter.get_appearance_mode", return_value="Light"):
            assert (
                blend(("#000000", "#000000"), ("#ffffff", "#ffffff"), 0.5) == "#808080"
            )


@pytest.fixture(autouse=True)
def _clear_dpi_cache():
    from src.ui import theme

    if hasattr(theme.xft_dpi, "cache_clear"):
        theme.xft_dpi.cache_clear()
