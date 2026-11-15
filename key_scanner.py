"""Finds the musical key of every Liked Song by showing them in Spotify's own
Key column, a few at a time, and reading the screen.

Spotify no longer gives the key through its API, but its desktop app shows it
for tracks in a playlist. So: put the next batch of tracks into a 'temp'
playlist, wait for the app to redraw, read the coloured key pill of each row.
The row order is the order we sent, so no row numbers need reading."""
import time
from pathlib import Path

from PIL import Image

from scan_results import ScanResults
from screen_reading.calibration import Calibration
from screen_reading.key_palette import KeyPalette
from screen_reading.pill_finder import PillFinder
from screen_reading.track_list_view import TrackListView
from spotify_client import SpotifyClient

TEMP_PLAYLIST_NAME = "temp"
TRACKS_PER_BATCH = 10       # tracks shown in the temp playlist at once
PROGRESS_EVERY_N_BATCHES = 5
DEBUG_IMAGE_FILE = Path("results/debug_first_batch.png")


class ScanError(Exception):
    pass


class KeyScanner:
    def __init__(self, client: SpotifyClient, results: ScanResults):
        self._client = client
        self._results = results
        self._pill_finder = PillFinder(KeyPalette())

    def run(self, track_uris: list[str], max_tracks: int | None = None) -> bool:
        """Scan the tracks not scanned yet. Returns False if stopped with Ctrl+C."""
        pending = self._results.unscanned(track_uris)
        if max_tracks:
            pending = pending[:max_tracks]
        print(f"{len(track_uris)} liked tracks, {len(self._results)} already scanned, "
              f"{len(pending)} to scan this run.")
        if not pending:
            return True

        playlist_id = self._client.get_or_create_playlist(TEMP_PLAYLIST_NAME)
        self._client.replace_tracks(playlist_id, pending[:TRACKS_PER_BATCH])

        view = self._prepare_view()
        batch_size = min(TRACKS_PER_BATCH, view.rows_that_fit())
        print(f"{batch_size} tracks per batch")
        return self._scan_in_batches(view, playlist_id, pending, batch_size)

    # ------------------------------------------------------------------ setup
    def _prepare_view(self) -> TrackListView:
        """Calibrate, then check the first batch is readable."""
        view = TrackListView(Calibration.load_or_ask(), self._pill_finder)
        view.park_mouse()
        time.sleep(0.5)

        image, _ = view.wait_until_settled()
        DEBUG_IMAGE_FILE.parent.mkdir(exist_ok=True)
        self._save_debug_image(image)
        if view.measure_row_pitch(image) is None:
            raise ScanError(f"Could not measure the row spacing. Look at "
                            f"{DEBUG_IMAGE_FILE}: it should show the first batch's "
                            f"titles and key pills.")
        return view

    @staticmethod
    def _save_debug_image(image) -> None:
        Image.fromarray(image.astype("uint8")).save(DEBUG_IMAGE_FILE)

    # --------------------------------------------------------------- scanning
    def _scan_in_batches(self, view, playlist_id, pending, batch_size) -> bool:
        started = time.time()
        scanned = 0
        previous_titles = None
        finished = True
        try:
            for batch_number, start in enumerate(range(0, len(pending), batch_size)):
                batch = pending[start:start + batch_size]
                keys, previous_titles = self._read_batch(
                    view, playlist_id, batch, previous_titles)
                for uri, key in zip(batch, keys):
                    self._results.record(uri, key)
                scanned += len(batch)

                if batch_number % PROGRESS_EVERY_N_BATCHES == 0:
                    self._results.save()
                    self._print_progress(scanned, len(pending), time.time() - started)
        except KeyboardInterrupt:
            finished = False
            print("\nStopped by user (progress is saved; run again to resume).")

        self._results.save()
        print(f"\nDone in {time.time() - started:.0f}s: scanned {scanned} tracks "
              f"({self._results.count_without_key()} in total have no key: "
              f"hidden or dimmed tracks).")
        return finished

    def _read_batch(self, view, playlist_id, batch, previous_titles):
        """Show `batch` in the temp playlist and read its keys.
        Returns (keys, titles_of_this_batch)."""
        self._client.replace_tracks(playlist_id, batch)
        image, settled = view.wait_until_settled(previous_titles)
        if not settled:
            print("  warning: the screen never settled for this batch")
        keys = view.read_keys(image, len(batch))
        if not any(keys):
            # Key data can arrive a moment after the titles: look once more.
            time.sleep(1.0)
            image, _ = view.wait_until_settled()
            keys = view.read_keys(image, len(batch))
        return keys, view.titles(image)

    @staticmethod
    def _print_progress(scanned: int, total: int, elapsed: float) -> None:
        seconds_per_track = elapsed / scanned
        print(f"  {scanned}/{total}  {seconds_per_track * 10:.1f}s per 10, "
              f"~{seconds_per_track * (total - scanned):.0f}s left")
