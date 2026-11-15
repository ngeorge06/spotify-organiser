"""Everything that talks to the Spotify Web API.

Spotify's February 2026 API changes renamed the playlist endpoints (/tracks ->
/items) and Spotipy's built-in helpers still call the old ones, so the playlist
methods below call the new endpoints directly through Spotipy's private
_get/_post/_put helpers."""
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_SCOPES = "user-library-read playlist-read-private playlist-modify-private"
API_PAGE_SIZE = 50          # max items per page for "get" endpoints
API_ADD_BATCH_SIZE = 100    # max tracks per "add/replace items" request


class SpotifyClient:
    def __init__(self):
        load_dotenv()   # SPOTIPY_CLIENT_ID / _SECRET / _REDIRECT_URI from .env
        self._api = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SPOTIFY_SCOPES))
        self._user_id: str | None = None

    # ------------------------------------------------------------- liked songs
    def liked_track_uris(self) -> list[str]:
        """URIs of all Liked Songs, in Spotify's order (local files are skipped)."""
        uris, offset = [], 0
        while True:
            page = self._api.current_user_saved_tracks(limit=API_PAGE_SIZE, offset=offset)
            for item in page["items"]:
                track = item["track"]
                if track and track.get("id"):
                    uris.append(track["uri"])
            if not page["next"]:
                return uris
            offset += API_PAGE_SIZE

    # --------------------------------------------------------------- playlists
    @property
    def user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self._api.current_user()["id"]
        return self._user_id

    def own_playlists(self) -> dict[str, str]:
        """{name: id} of playlists you own. Playlists inside folders are included;
        the API cannot see folders."""
        playlists, offset = {}, 0
        while True:
            page = self._api.current_user_playlists(limit=API_PAGE_SIZE, offset=offset)
            for playlist in page["items"]:
                if playlist and playlist["owner"]["id"] == self.user_id:
                    playlists.setdefault(playlist["name"].strip(), playlist["id"])
            if page["next"] is None:
                return playlists
            offset += API_PAGE_SIZE

    def create_playlist(self, name: str) -> str:
        created = self._api._post("me/playlists", payload={"name": name, "public": False})
        return created["id"]

    def get_or_create_playlist(self, name: str) -> str:
        existing = self.own_playlists().get(name)
        return existing if existing else self.create_playlist(name)

    def playlist_track_uris(self, playlist_id: str) -> set[str]:
        uris, offset = set(), 0
        while True:
            page = self._api._get(f"playlists/{playlist_id}/items",
                                  limit=API_PAGE_SIZE, offset=offset)
            for entry in page["items"]:
                track = entry.get("item") or entry.get("track")   # field was renamed
                if track and track.get("uri"):
                    uris.add(track["uri"])
            if not page.get("next"):
                return uris
            offset += API_PAGE_SIZE

    def add_tracks(self, playlist_id: str, uris: list[str]) -> None:
        for start in range(0, len(uris), API_ADD_BATCH_SIZE):
            batch = uris[start:start + API_ADD_BATCH_SIZE]
            self._api._post(f"playlists/{playlist_id}/items", payload={"uris": batch})

    def replace_tracks(self, playlist_id: str, uris: list[str]) -> None:
        """Make the playlist contain exactly these tracks (max 100)."""
        self._api._put(f"playlists/{playlist_id}/items", payload={"uris": uris})
