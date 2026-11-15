TEMP_PLAYLIST_NAME = "temp"
TRACK_FILE = "tracks.txt"
EXISTING_TRACK_FILE = "existingTracks.txt"

# create / find temp playlist and return its ID
def _getTempPlaylistID(sp):
    offset = 0
    while True:

        page = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in page["items"]:
            if playlist["name"] == TEMP_PLAYLIST_NAME:
                return playlist["id"]
            
        if not page["next"]:
            break

        offset += 50

    playlist = sp._post("me/playlists", payload={"name": TEMP_PLAYLIST_NAME, "public": False})
    return playlist["id"]

# dump all liked track URIs to a file
def _dumpTrackURIs(sp):
    offset = 0
    with open(TRACK_FILE, "w") as f:

        while True:
            
            result = sp.current_user_saved_tracks(limit=50, offset=offset)
            for item in result["items"]:
                track = item["track"]
                if track and track["id"]:
                    f.write(track["uri"] + "\n")

            # if there are no more tracks, break the loop        
            if not result["next"]:
                break

            offset += 50

# dump all track URIs from the temp playlist to a file
def _dumpExistingURIs(sp, playlistID):
    offset = 0
    with open(EXISTING_TRACK_FILE, "w") as f:

        while True:

            page = sp._get(f"playlists/{playlistID}/items", limit=50, offset=offset)

            for entry in page["items"]:
                track = entry.get("item") or entry.get("track")
                if track and track.get("uri"):
                    f.write(track["uri"] + "\n")

            if not page["next"]:
                break

            offset += 50

# add a batch of tracks to the temp playlist
def _addBatch(sp, playlistID, uris):
    sp._post(f"playlists/{playlistID}/items", payload={"uris": uris})


def move(sp):
    TempPlaylistID = _getTempPlaylistID(sp)

    _dumpTrackURIs(sp)
    _dumpExistingURIs(sp, TempPlaylistID)

    with open(EXISTING_TRACK_FILE) as f:
        existing = {line.strip() for line in f}

    added, toAddArr = 0, []
    with open(TRACK_FILE) as f:
        for line in f:
            uri = line.strip()
            if uri and uri not in existing:
                toAddArr.append(uri)
                if len(toAddArr) == 50:
                    _addBatch(sp, TempPlaylistID, toAddArr)
                    added += len(toAddArr)
                    toAddArr = []
                    print(f"Added {added} new tracks so far...")
    if toAddArr:
        _addBatch(sp, TempPlaylistID, toAddArr)
        added += len(toAddArr)

    print(f"DONE: Added {added} new tracks to '{TEMP_PLAYLIST_NAME}'.")


if __name__ == "__main__":
    print("Run main.py to execute the program.")