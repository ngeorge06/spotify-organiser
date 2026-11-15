import csv
import json
import os
import re
import time
import requests
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

GSB_KEY = os.getenv("GETSONGBPM_API_KEY")
GSB = "https://api.getsong.co"
CACHE_FILE = "keys_cache.json"
OUT_FILE = "liked_keys.csv"

CAMELOT = {
    "C": "8B", "G": "9B", "D": "10B", "A": "11B", "E": "12B", "B": "1B",
    "F#": "2B", "C#": "3B", "G#": "4B", "D#": "5B", "A#": "6B", "F": "7B",
    "Am": "8A", "Em": "9A", "Bm": "10A", "F#m": "11A", "C#m": "12A",
    "G#m": "1A", "D#m": "2A", "A#m": "3A", "Fm": "4A", "Cm": "5A",
    "Gm": "6A", "Dm": "7A",
}
FLATS = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}

def to_camelot(key_of):
    k = key_of.replace("♯", "#").replace("♭", "b").strip()
    m = re.match(r"[A-G][#b]?", k)
    if not m:
        return None
    root = m.group(0)
    minor = k[len(root):].startswith("m")
    root = FLATS.get(root, root)
    return CAMELOT.get(root + ("m" if minor else ""))

def clean_title(t):
    return re.split(r" - | \(| \[", t)[0].strip()

def gsb_get(path, params):
    params = {**params, "api_key": GSB_KEY}
    for _ in range(3):
        r = requests.get(f"{GSB}{path}", params=params, timeout=15)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10)))
            continue
        r.raise_for_status()
        return r.json()
    return {}

def lookup_key(title, artist):
    data = gsb_get("/search/", {
        "type": "both",
        "lookup": f"song:{clean_title(title)} artist:{artist}",
    })
    results = data.get("search")
    if not results or not isinstance(results, list):
        return None
    hit = results[0]
    if "key_of" not in hit:
        hit = gsb_get("/song/", {"id": hit["id"]}).get("song", {})
    return hit

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)

def all_liked(sp):
    offset = 0
    while True:
        page = sp.current_user_saved_tracks(limit=50, offset=offset)
        for item in page["items"]:
            yield item["track"]
        if not page["next"]:
            break
        offset += 50

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-library-read playlist-modify-private"))
cache = load_cache()
rows = []

for i, t in enumerate(all_liked(sp), 1):
    tid, name, artist = t["id"], t["name"], t["artists"][0]["name"]
    if tid not in cache:
        try:
            hit = lookup_key(name, artist)
        except requests.RequestException as e:
            print(f"{i}. ERROR {artist} - {name}: {e}")
            continue  # not cached, so it retries next run
        cache[tid] = {
            "key_of": (hit or {}).get("key_of"),
            "matched": (f'{hit.get("title")} / {hit.get("artist", {}).get("name")}'
                        if hit else None),
        }
        time.sleep(0.3)
        if i % 25 == 0:
            save_cache(cache)
    c = cache[tid]
    camelot = to_camelot(c["key_of"]) if c["key_of"] else None
    rows.append([tid, artist, name, c["key_of"], camelot, c["matched"]])
    print(f"{i}. {artist} - {name}: {c['key_of']} -> {camelot}")

save_cache(cache)
with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["track_id", "artist", "title", "key", "camelot", "matched_as"])
    w.writerows(rows)

found = sum(1 for r in rows if r[4])
print(f"\nDone: {found}/{len(rows)} have a Camelot key. Wrote {OUT_FILE}")