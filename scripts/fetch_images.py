"""
fetch_images.py
Reads data/Top_Indian_Artist.json, fetches a fresh artist image
from the iTunes Search API (free, no key needed) for each artist,
then writes the image URL back into the file.
"""

import json
import time
import requests

ITUNES_URL = "https://itunes.apple.com/search"
PLACEHOLDER = "https://placehold.co/300x300/1d4436/69e091?text={}"


def get_itunes_image(artist_name):
    try:
        resp = requests.get(
            ITUNES_URL,
            params={"term": artist_name, "entity": "musicArtist", "limit": 1},
            timeout=8,
        )
        data = resp.json()
        if data.get("results"):
            url = data["results"][0].get("artworkUrl100", "")
            if url:
                # Upgrade to 600x600 resolution
                return url.replace("100x100bb", "600x600bb")
    except Exception as e:
        print(f"  iTunes error for '{artist_name}': {e}")

    # Fallback: nice placeholder with artist initials
    initials = "+".join(w[0].upper() for w in artist_name.split()[:2] if w)
    return PLACEHOLDER.format(initials or "?")


if __name__ == "__main__":
    with open("data/Top_Indian_Artist.json", encoding="utf-8") as f:
        data = json.load(f)

    header = data[0]
    artists = data[1:]

    print(f"Fetching images for {len(artists)} artists...")

    for i, entry in enumerate(artists):
        name = entry["A"]
        print(f"  [{i+1}/{len(artists)}] {name}")
        entry["C"] = get_itunes_image(name)
        time.sleep(0.35)   # polite rate limit for iTunes API

    final = [header] + artists

    with open("data/Top_Indian_Artist.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("Done — images saved → data/Top_Indian_Artist.json")
