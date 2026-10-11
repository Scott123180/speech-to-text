"""Pure helpers behind the recording status line: level meter and elapsed clock."""

import math

FLOOR_DB = -60.0
RELEASE = 0.8


class LevelSmoother:
    """Turns raw RMS readings into a 0..1 meter level.

    Mapped through decibels rather than raw amplitude because speech sits low in
    linear terms — a linear meter barely twitches at conversational volume. Attack
    is instant and release is gradual, so a peak is legible rather than a flicker.
    """

    def __init__(self) -> None:
        self._smoothed = 0.0

    def update(self, rms: float) -> float:
        db = 20 * math.log10(rms + 1e-9)
        normalized = min(1.0, max(0.0, (db - FLOOR_DB) / -FLOOR_DB))
        if normalized > self._smoothed:
            self._smoothed = normalized
        else:
            self._smoothed = self._smoothed * RELEASE + normalized * (1 - RELEASE)
        return self._smoothed

    def reset(self) -> None:
        self._smoothed = 0.0


def lit_bars(level: float, bar_count: int) -> int:
    """Number of meter bars to light for *level* (0..1)."""
    return math.floor(level * bar_count + 0.5)


def format_elapsed(seconds: float) -> str:
    """Format a duration as m:ss."""
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"
