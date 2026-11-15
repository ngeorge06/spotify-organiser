# Spotify Key Organiser

Sorts your Spotify **Liked Songs** into playlists by musical key (Camelot notation: `1A`, `7B`, `12B`, ...), which is handy for DJ-style mixing.

## Why it reads the screen

Spotify's Web API no longer returns audio features (key, BPM) to new apps, so the key can't be fetched directly. The Spotify desktop app does show a **Key** column (via the playlist *Mix* view), so this tool reads it from there:

1. It puts the next 10 liked songs into a private playlist called `temp` (one API call).
2. It waits for the desktop app to redraw, then takes a small screenshot of the title and Key columns.
3. Each key shows as a coloured pill. The colour identifies the key, and the row order identifies the song, so no text recognition is needed.
4. It repeats for every liked song (about 4 minutes for 2,000 songs) and saves `{track: key}` to `results/scanned_keys.json`.
5. A second step adds each song to the playlist named after its key, creating playlists that don't exist and skipping songs already in them.

Songs that are unavailable on Spotify (shown with a dimmed pill) or have no key are skipped.

## Key colours

Spotify draws each key as a coloured label. These are the colours the scanner matches against, measured from the desktop app (`screen_reading/key_palette.py`). A labels are minor keys; B labels are major keys and use a deeper shade of the same hue.

![Spotify's Camelot key labels](docs/key_palette.png)

| Key | RGB | Hex | Key | RGB | Hex |
|---|---|---|---|---|---|
| 1A | 85, 242, 216 | `#55F2D8` | 1B | 5, 236, 203 | `#05ECCB` |
| 2A | 127, 242, 169 | `#7FF2A9` | 2B | 61, 237, 130 | `#3DED82` |
| 3A | 175, 246, 142 | `#AFF68E` | 3B | 134, 242, 78 | `#86F24E` |
| 4A | 231, 217, 163 | `#E7D9A3` | 4B | 222, 202, 115 | `#DECA73` |
| 5A | 254, 192, 163 | `#FEC0A3` | 5B | 254, 161, 129 | `#FEA181` |
| 6A | 255, 173, 185 | `#FFADB9` | 6B | 255, 136, 147 | `#FF8893` |
| 7A | 255, 173, 207 | `#FFADCF` | 7B | 255, 128, 180 | `#FF80B4` |
| 8A | 241, 172, 231 | `#F1ACE7` | 8B | 238, 130, 217 | `#EE82D9` |
| 9A | 221, 180, 251 | `#DDB4FB` | 9B | 203, 144, 255 | `#CB90FF` |
| 10A | 190, 206, 255 | `#BECEFF` | 10B | 160, 182, 255 | `#A0B6FF` |
| 11A | 137, 227, 249 | `#89E3F9` | 11B | 86, 217, 248 | `#56D9F8` |
| 12A | 86, 239, 242 | `#56EFF2` | 12B | 4, 235, 235 | `#04EBEB` |

A label is matched to the nearest colour if it is within a distance of 12. The closest two keys (6A and 7A) are 22 apart, so keys can't be confused, and dimmed labels on unavailable tracks match nothing and are skipped.

## Setup

1. Create an app at the [Spotify developer dashboard](https://developer.spotify.com/dashboard) and add the redirect URI `http://127.0.0.1:8888/callback`. (Apps in Development Mode need the owner to have Spotify Premium.)
2. Copy `.env.example` to `.env` and fill in your client ID and secret.
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. In the Spotify **desktop app**, open any playlist, turn on **Mix**, and make sure the **Key** column is visible. Pause playback so the playing row doesn't change its look.

## Usage

```
python main.py
```

That's the whole interface. It scans the key of every liked song (stop with Ctrl+C and run again to resume), then shows a plan of which key playlists exist, which are new and how many tracks go into each, and asks `Go ahead? (y/n)` before changing anything.

For a short test, set `MAX_TRACKS = 30` at the top of `main.py`.

### Calibration (first scan only)

Open the `temp` playlist in Spotify, scrolled to the top, then hover the mouse over four things when prompted (you get 5 seconds each):

1. the title of the first track
2. the word **Key** in the column header
3. the key pill of the first track
4. the bottom edge of the list, just above the player bar

The positions are saved to `results/calibration.json`. Calibrate again if you move or resize the Spotify window or change its zoom.

## Notes and limits

- The Spotify window must stay visible and un-obscured while scanning. Move the mouse to a screen corner to abort (pyautogui failsafe) or press Ctrl+C.
- The Web API can't see or create folders. New key playlists appear at the top of your library: drag them into your folder yourself. Existing playlists are found by name even when they're inside a folder.
- Spotify's playlist endpoints changed in February 2026 (`/tracks` became `/items`), so `spotify_client.py` calls the new endpoints directly through Spotipy's private helpers. A Spotipy update may make that unnecessary.
- The key colours were measured from Spotify's current look. If Spotify restyles the pills, update `screen_reading/key_palette.py`.

## Project layout

```
main.py             run this
spotify_client.py   SpotifyClient: everything that talks to the API
key_scanner.py      KeyScanner: batches tracks through temp and records their keys
key_playlists.py    KeyPlaylistBuilder: plans and fills the key playlists
scan_results.py     ScanResults: the saved {track: key} data
screen_reading/     reading Spotify's window
  key_palette.py      KeyPalette: the 24 key colours, colour -> key
  pill_finder.py      PillFinder: finds key pills in a screenshot strip
  calibration.py      Calibration: where things are on screen
  track_list_view.py  TrackListView: captures and reads the playlist on screen
docs/key_palette.png  key colour image used in this README
results/            generated files (git-ignored): scanned_keys.json,
                    calibration.json, tracks.txt, debug_first_batch.png
```