"""Where things are on screen. You point at them with the mouse once; the
positions are saved so later runs can reuse them."""
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import pyautogui

CALIBRATION_FILE = Path("results/calibration.json")


@dataclass
class Calibration:
    title_x: int          # x of the first track's title
    key_x: int            # x of the word "Key" in the column header
    header_y: int         # y of the column header
    first_pill_y: int     # y of the first track's key pill
    list_bottom_y: int    # bottom edge of the visible list (above the player bar)

    def save(self) -> None:
        CALIBRATION_FILE.parent.mkdir(exist_ok=True)
        CALIBRATION_FILE.write_text(json.dumps(asdict(self)))

    @classmethod
    def load(cls) -> "Calibration | None":
        try:
            return cls(**json.loads(CALIBRATION_FILE.read_text()))
        except (OSError, ValueError, TypeError):
            return None

    @classmethod
    def load_or_ask(cls) -> "Calibration":
        saved = cls.load()
        if saved and input("Use saved calibration? (y/n): ").strip().lower() == "y":
            return saved
        calibration = cls._ask_user()
        calibration.save()
        return calibration

    @classmethod
    def _ask_user(cls) -> "Calibration":
        print("Open the 'temp' playlist in Spotify, scrolled to the top.")
        input("Press Enter here, then follow the 5-second hover prompts... ")
        title_x, _ = _hover("the TITLE of the FIRST track")
        key_x, header_y = _hover("the word 'Key' in the column header")
        _, first_pill_y = _hover("the KEY PILL of the FIRST track")
        _, list_bottom_y = _hover("the bottom edge of the list, just ABOVE the player bar")
        return cls(title_x, key_x, header_y, first_pill_y, list_bottom_y)


def _hover(description: str, seconds: int = 5) -> tuple[int, int]:
    """Give the user a few seconds to put the mouse somewhere, then read it."""
    print(f"Hover the mouse over {description} ({seconds}s)")
    for remaining in range(seconds, 0, -1):
        print(f"  {remaining}...", end="", flush=True)
        time.sleep(1)
    position = pyautogui.position()
    print(f"  got ({position.x}, {position.y})")
    return position.x, position.y
