import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

import moveToTemp as Move

load_dotenv() #load CLIENT_ID, CLIENT_SECRET, REDIRECT_URI from .env file


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-library-read playlist-read-private playlist-modify-private"
))

if __name__ == "__main__":

    choice = input("1: move all saved tracks to temp playlist\n2: Sort temp playlist by musical key\n\n")

    match choice:
        case "1": Move.move(sp)
        case "2": pass
        case _: print("Invalid choice. Please select 1 or 2.\n\n")
