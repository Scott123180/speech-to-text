"""Unit tests for the recording-status helpers. Write FIRST — must FAIL first."""

import pytest

from src.ui.meter import LevelSmoother, format_elapsed, lit_bars


class TestLevelSmoother:
    def test_silence_reads_zero(self):
        assert LevelSmoother().update(0.0) == 0.0

    def test_full_scale_reads_one(self):
        assert LevelSmoother().update(1.0) == pytest.approx(1.0)

    def test_maps_through_decibels(self):
        # -30 dBFS sits halfway across a 60 dB range; linearly it would be ~0.03.
        assert LevelSmoother().update(10 ** (-30 / 20)) == pytest.approx(0.5)

    def test_below_floor_clamps_to_zero(self):
        assert LevelSmoother().update(10 ** (-80 / 20)) == 0.0

    def test_attack_is_instant(self):
        smoother = LevelSmoother()
        smoother.update(0.0)
        assert smoother.update(1.0) == pytest.approx(1.0)

    def test_release_is_gradual(self):
        smoother = LevelSmoother()
        smoother.update(1.0)
        after_drop = smoother.update(0.0)
        assert after_drop == pytest.approx(0.8)

    def test_reset_returns_to_zero(self):
        smoother = LevelSmoother()
        smoother.update(1.0)
        smoother.reset()
        assert smoother.update(0.0) == 0.0


class TestLitBars:
    def test_zero_level_lights_nothing(self):
        assert lit_bars(0.0, 12) == 0

    def test_full_level_lights_everything(self):
        assert lit_bars(1.0, 12) == 12

    def test_rounds_to_nearest_bar(self):
        assert lit_bars(0.5, 12) == 6
        assert lit_bars(0.46, 12) == 6


class TestFormatElapsed:
    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [(0, "0:00"), (9.9, "0:09"), (61, "1:01"), (600, "10:00")],
    )
    def test_minutes_and_padded_seconds(self, seconds, expected):
        assert format_elapsed(seconds) == expected
