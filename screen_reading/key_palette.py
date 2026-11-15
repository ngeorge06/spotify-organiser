"""The 24 Camelot key colours as Spotify draws them, and a colour -> key lookup."""
import numpy as np

# Measured from Spotify's key pills (median RGB of each pill, text excluded).
KEY_COLOURS: dict[str, tuple[int, int, int]] = {
    "1A": (85, 242, 216),   "2A": (127, 242, 169),  "3A": (175, 246, 142),
    "4A": (231, 217, 163),  "5A": (254, 192, 163),  "6A": (255, 173, 185),
    "7A": (255, 173, 207),  "8A": (241, 172, 231),  "9A": (221, 180, 251),
    "10A": (190, 206, 255), "11A": (137, 227, 249), "12A": (86, 239, 242),
    "1B": (5, 236, 203),    "2B": (61, 237, 130),   "3B": (134, 242, 78),
    "4B": (222, 202, 115),  "5B": (254, 161, 129),  "6B": (255, 136, 147),
    "7B": (255, 128, 180),  "8B": (238, 130, 217),  "9B": (203, 144, 255),
    "10B": (160, 182, 255), "11B": (86, 217, 248),  "12B": (4, 235, 235),
}

# The two closest colours (6A and 7A) are 22 apart, so 12 is a safe tolerance.
# Dimmed pills (unavailable tracks) are far from every colour and return None.
MAX_COLOUR_DISTANCE = 12


def camelot_sort_key(key: str) -> tuple[int, str]:
    """Sort '1A', '1B', '2A', ... '12B' in wheel order."""
    return int(key[:-1]), key[-1]


class KeyPalette:
    """Matches a measured pill colour to a Camelot key."""

    def __init__(self, colours=KEY_COLOURS, max_distance=MAX_COLOUR_DISTANCE):
        self._keys = list(colours)
        self._rgb = np.array([colours[k] for k in self._keys], dtype=float)
        self._max_distance = max_distance

    def identify(self, rgb) -> str | None:
        """The key whose colour is closest to rgb, or None if nothing is close."""
        distances = np.linalg.norm(self._rgb - np.array(rgb, dtype=float), axis=1)
        nearest = int(distances.argmin())
        if distances[nearest] <= self._max_distance:
            return self._keys[nearest]
        return None
