"""Sort your Spotify Liked Songs into playlists by musical key.

Run this file. It scans the key of every liked song (resuming where it left off
if it was stopped), then shows which key playlists it would fill and asks first."""
from pathlib import Path

from key_playlists import KeyPlaylistBuilder
from key_scanner import KeyScanner, ScanError
from scan_results import ScanResults
from spotify_client import SpotifyClient

TRACKS_FILE = Path("results/tracks.txt")   # record of your liked songs' URIs
MAX_TRACKS = None                          # e.g. 30 for a short test run; None = all


def main() -> None:
    client = SpotifyClient()
    results = ScanResults()
    results.load()

    track_uris = client.liked_track_uris()
    TRACKS_FILE.parent.mkdir(exist_ok=True)
    TRACKS_FILE.write_text("\n".join(track_uris))

    try:
        finished = KeyScanner(client, results).run(track_uris, MAX_TRACKS)
    except ScanError as error:
        print(error)
        return
    if finished:
        KeyPlaylistBuilder(client, results).run()


if __name__ == "__main__":
    main()