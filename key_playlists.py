"""Puts scanned tracks into one playlist per key ('1A', '7B', ...)."""
from dataclasses import dataclass

from scan_results import ScanResults
from spotify_client import SpotifyClient


@dataclass
class PlaylistPlan:
    key: str
    playlist_id: str | None        # None = the playlist does not exist yet
    tracks_to_add: list[str]
    already_present: int


class KeyPlaylistBuilder:
    def __init__(self, client: SpotifyClient, results: ScanResults):
        self._client = client
        self._results = results

    def run(self) -> None:
        plans = self._make_plans()
        self._print_plans(plans)

        total_to_add = sum(len(p.tracks_to_add) for p in plans)
        if total_to_add == 0:
            print("Nothing to do.")
            return
        if input("Go ahead? (y/n): ").strip().lower() != "y":
            print("Cancelled - nothing changed.")
            return

        created_any = self._apply(plans)
        if created_any:
            print("\nNew playlists were created in your main library - "
                  "drag them into your folder in Spotify (the API can't do that).")
        print("Done.")

    # ----------------------------------------------------------------- planning
    def _make_plans(self) -> list[PlaylistPlan]:
        """Read-only: work out what each key playlist is missing."""
        existing = self._client.own_playlists()
        plans = []
        for key, uris in self._results.group_by_key().items():
            playlist_id = existing.get(key)
            in_playlist = (self._client.playlist_track_uris(playlist_id)
                           if playlist_id else set())
            missing = [uri for uri in uris if uri not in in_playlist]
            plans.append(PlaylistPlan(key, playlist_id, missing, len(uris) - len(missing)))
        return plans

    def _print_plans(self, plans: list[PlaylistPlan]) -> None:
        print(f"{sum(len(p.tracks_to_add) + p.already_present for p in plans)} tracks "
              f"have a key, {self._results.count_without_key()} skipped (no key)\n")
        for plan in plans:
            state = "exists" if plan.playlist_id else "NEW playlist"
            print(f"  {plan.key:>3}: {state:<13} add {len(plan.tracks_to_add):>4}   "
                  f"already in it {plan.already_present:>4}")
        creating = sum(1 for p in plans if not p.playlist_id and p.tracks_to_add)
        print(f"\n{sum(len(p.tracks_to_add) for p in plans)} tracks to add, "
              f"{creating} new playlists to create.")

    # ----------------------------------------------------------------- applying
    def _apply(self, plans: list[PlaylistPlan]) -> bool:
        """Returns True if any playlist had to be created."""
        created_any = False
        for plan in plans:
            if not plan.tracks_to_add:
                continue
            playlist_id = plan.playlist_id
            if playlist_id is None:
                playlist_id = self._client.create_playlist(plan.key)
                created_any = True
            self._client.add_tracks(playlist_id, plan.tracks_to_add)
            print(f"{plan.key}: added {len(plan.tracks_to_add)}")
        return created_any
