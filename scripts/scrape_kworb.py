"""
scrape_kworb.py
1. Scrapes all ~2000 artists from kworb.net/ww/artisttotals.html
2. Loads Indian artists list from data/indian_artists.json
3. Fuzzy-matches Indian artists against kworb list
4. Ranks matched artists by their kworb "Today" score (descending)
5. Saves ranked list to data/Top_Indian_Artist.json (images added later by fetch_images.py)
"""

import json
import os
import requests
from bs4 import BeautifulSoup
from rapidfuzz import process, fuzz

KWORB_URL = "https://kworb.net/ww/artisttotals.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# Fuzzy match threshold — 0-100. 82 catches "A. R. Rahman" vs "AR Rahman"
# but avoids false positives like "Mano" matching "Manos"
MATCH_THRESHOLD = 82


def scrape_kworb():
    print("Scraping kworb.net...")
    resp = requests.get(KWORB_URL, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find("table")
    rows = table.find_all("tr")[1:]   # skip header

    kworb = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        name = cols[0].text.strip()
        today_raw = cols[2].text.strip().replace(",", "")
        try:
            today = int(today_raw)
        except ValueError:
            today = 0
        kworb.append({"name": name, "today": today})

    print(f"Found {len(kworb)} artists on kworb.net")
    return kworb


def match_artists(indian_artists, kworb_list):
    kworb_names = [a["name"] for a in kworb_list]
    kworb_lookup = {a["name"]: a["today"] for a in kworb_list}

    matched = []
    unmatched = []

    for indian_name in indian_artists:
        result = process.extractOne(
            indian_name,
            kworb_names,
            scorer=fuzz.token_sort_ratio
        )
        if result and result[1] >= MATCH_THRESHOLD:
            kworb_name = result[0]
            today_score = kworb_lookup[kworb_name]
            matched.append({
                "indian_name": indian_name,
                "kworb_name": kworb_name,
                "today": today_score,
                "match_score": result[1]
            })
        else:
            unmatched.append(indian_name)

    print(f"Matched {len(matched)} Indian artists on kworb")
    print(f"No kworb entry found for {len(unmatched)} artists")

    # Sort by Today score descending
    matched.sort(key=lambda x: x["today"], reverse=True)
    return matched


def build_output(matched):
    """
    Build Top_Indian_Artist.json in the format the HTML expects:
    [ {header}, {A: name, B: score, C: image_url}, ... ]
    Images are placeholder for now — fetch_images.py fills them in.
    """
    output = [{"A": "Artist_Name", "B": "Today_Score", "C": "Image_Url"}]

    for entry in matched:
        output.append({
            "A": entry["indian_name"],
            "B": str(entry["today"]),
            "C": ""           # fetch_images.py will fill this
        })

    return output


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    # Load Indian artists from MusicBrainz scrape
    with open("data/indian_artists.json", encoding="utf-8") as f:
        indian_artists = json.load(f)
    print(f"Loaded {len(indian_artists)} Indian artists from MusicBrainz")

    kworb_list = scrape_kworb()
    matched = match_artists(indian_artists, kworb_list)
    output = build_output(matched)

    with open("data/Top_Indian_Artist.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(output)-1} ranked artists → data/Top_Indian_Artist.json")
    print("\nTop 10 preview:")
    for entry in output[1:11]:
        print(f"  {entry['A']:30s}  Today score: {entry['B']}")
