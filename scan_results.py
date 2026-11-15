"""The scanned keys: {track_uri: key or None}, saved to disk between runs."""
import json
from pathlib import Path

from screen_reading.key_palette import camelot_sort_key

SCAN_RESULTS_FILE = Path("results/scanned_keys.json")


class ScanResults:
    def __init__(self):
        self._key_by_uri: dict[str, str | None] = {}

    def load(self) -> None:
        try:
            self._key_by_uri = json.loads(SCAN_RESULTS_FILE.read_text())
        except (OSError, ValueError):
            self._key_by_uri = {}

    def save(self) -> None:
        SCAN_RESULTS_FILE.parent.mkdir(exist_ok=True)
        SCAN_RESULTS_FILE.write_text(json.dumps(self._key_by_uri))

    def record(self, uri: str, key: str | None) -> None:
        self._key_by_uri[uri] = key

    def unscanned(self, uris: list[str]) -> list[str]:
        return [uri for uri in uris if uri not in self._key_by_uri]

    def count_without_key(self) -> int:
        return sum(1 for key in self._key_by_uri.values() if not key)

    def __len__(self) -> int:
        return len(self._key_by_uri)

    def group_by_key(self) -> dict[str, list[str]]:
        """{'1A': [uri, ...], '1B': [...], ...} in Camelot order, skipping unkeyed tracks."""
        groups: dict[str, list[str]] = {}
        for uri, key in self._key_by_uri.items():
            if key:
                groups.setdefault(key, []).append(uri)
        return {key: groups[key] for key in sorted(groups, key=camelot_sort_key)}
