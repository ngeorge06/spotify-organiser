"""Looks at the playlist in Spotify's window and reads the key of each row."""
import time

import mss
import numpy as np
import pyautogui

from screen_reading.calibration import Calibration
from screen_reading.pill_finder import PillFinder

HEADER_MARGIN = 15          # list area starts this far below the "Key" header
TITLE_LEFT_MARGIN = 5       # capture starts this far left of the first title
TITLE_WIDTH = 250           # title columns used to tell when a new batch is showing
KEY_STRIP_LEFT_OFFSET = 30  # key strip starts this far left of the "Key" header
KEY_STRIP_WIDTH = 90        # wide enough for the whole key pill

STABLE_FRAMES = 3           # identical frames in a row before a read is trusted
FRAME_INTERVAL = 0.12       # seconds between frames while waiting
SETTLE_TIMEOUT = 8.0        # give up waiting after this many seconds


class TrackListView:
    """The visible part of the playlist: title column + key column."""

    def __init__(self, calibration: Calibration, pill_finder: PillFinder):
        self._calibration = calibration
        self._pill_finder = pill_finder
        self._screen = mss.mss()
        self._row_pitch: float | None = None

        top = calibration.header_y + HEADER_MARGIN
        left = calibration.title_x - TITLE_LEFT_MARGIN
        key_left = calibration.key_x - KEY_STRIP_LEFT_OFFSET
        self._region = {
            "left": left,
            "top": top,
            "width": key_left + KEY_STRIP_WIDTH - left,
            "height": calibration.list_bottom_y - top,
        }
        self._title_columns = slice(0, TITLE_WIDTH)
        self._key_columns = slice(key_left - left, key_left - left + KEY_STRIP_WIDTH)
        self._first_row_y = calibration.first_pill_y - top

    # ---------------------------------------------------------------- capture
    def capture(self) -> np.ndarray:
        shot = self._screen.grab(self._region)
        return np.array(shot)[:, :, :3][:, :, ::-1]   # BGRA -> RGB

    def titles(self, image: np.ndarray) -> np.ndarray:
        return image[:, self._title_columns].copy()

    def _key_strip(self, image: np.ndarray) -> np.ndarray:
        return image[:, self._key_columns]

    def park_mouse(self) -> None:
        """Rest the mouse on the header so no row gets a hover highlight."""
        pyautogui.moveTo(self._calibration.key_x, self._calibration.header_y)

    # ---------------------------------------------------------------- waiting
    def wait_until_settled(self, previous_titles: np.ndarray | None = None):
        """Wait until Spotify shows a NEW batch (titles differ from previous_titles)
        and the picture has stopped changing. Returns (image, settled_ok)."""
        started = time.time()
        last_frame, identical_frames = None, 0
        while time.time() - started < SETTLE_TIMEOUT:
            image = self.capture()
            titles, keys = self.titles(image), self._key_strip(image)
            if previous_titles is not None and np.array_equal(titles, previous_titles):
                time.sleep(0.05)       # still the old batch
                continue
            if last_frame and np.array_equal(titles, last_frame[0]) \
                    and np.array_equal(keys, last_frame[1]):
                identical_frames += 1
                if identical_frames >= STABLE_FRAMES:
                    return image, True
            else:
                identical_frames = 0
            last_frame = (titles, keys.copy())
            time.sleep(FRAME_INTERVAL)
        return self.capture(), False

    # ---------------------------------------------------------------- reading
    def measure_row_pitch(self, image: np.ndarray) -> float | None:
        """Learn the row spacing from a screen full of tracks."""
        pills = self._pill_finder.find(self._key_strip(image))
        self._row_pitch = self._pill_finder.estimate_row_pitch(pills)
        return self._row_pitch

    def rows_that_fit(self) -> int:
        """How many whole rows fit between the first row and the bottom edge."""
        room = self._region["height"] - self._first_row_y - 10
        return int(room // self._row_pitch) + 1

    def read_keys(self, image: np.ndarray, count: int) -> list[str | None]:
        """The key of each of the first `count` rows (None = no readable key)."""
        keys: list[str | None] = [None] * count
        for pill in self._pill_finder.find(self._key_strip(image)):
            row = round((pill.centre_y - self._first_row_y) / self._row_pitch)
            if 0 <= row < count:
                keys[row] = pill.key
        return keys
