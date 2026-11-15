"""Finds the coloured key pills in a screenshot strip of Spotify's Key column."""
from dataclasses import dataclass

import numpy as np

from screen_reading.key_palette import KeyPalette

MIN_SATURATION = 40    # pill pixels are coloured: max(rgb) - min(rgb) > this
MIN_HEIGHT = 8
MIN_ROW_PIXELS = 12    # a screen row needs this many pill pixels to count


@dataclass(frozen=True)
class Pill:
    centre_y: int
    key: str | None   # None = coloured, but not one of the 24 key colours (dimmed)


def _contiguous_runs(indices: np.ndarray) -> list[tuple[int, int]]:
    """[2,3,4,9,10] -> [(2, 4), (9, 10)]"""
    runs, start = [], indices[0]
    for previous, current in zip(indices, indices[1:]):
        if current != previous + 1:
            runs.append((start, previous))
            start = current
    runs.append((start, indices[-1]))
    return runs


class PillFinder:
    def __init__(self, palette: KeyPalette):
        self._palette = palette

    def find(self, strip: np.ndarray) -> list[Pill]:
        """Every fully visible pill in the strip, top to bottom.
        Pills cut off by the top or bottom edge are ignored."""
        pixels = strip.astype(int)
        coloured = (pixels.max(axis=2) - pixels.min(axis=2)) > MIN_SATURATION
        busy_rows = np.where(coloured.sum(axis=1) >= MIN_ROW_PIXELS)[0]
        if len(busy_rows) == 0:
            return []

        pills = []
        for top, bottom in _contiguous_runs(busy_rows):
            too_small = bottom - top < MIN_HEIGHT
            cut_off = top <= 1 or bottom >= len(pixels) - 2
            if too_small or cut_off:
                continue
            band = pixels[top:bottom + 1]
            rgb = np.median(band[coloured[top:bottom + 1]], axis=0)
            pills.append(Pill((top + bottom) // 2, self._palette.identify(rgb)))
        return pills

    @staticmethod
    def estimate_row_pitch(pills: list[Pill]) -> float | None:
        """Distance in pixels between two neighbouring rows (needs 3+ pills).
        Pills can be missing for tracks without a key, so gaps are whole multiples."""
        ys = [p.centre_y for p in pills]
        if len(ys) < 3:
            return None
        gaps = [b - a for a, b in zip(ys, ys[1:])]
        smallest = min(gaps)
        if smallest < 10:
            return None
        return float(np.median([g / round(g / smallest) for g in gaps]))
