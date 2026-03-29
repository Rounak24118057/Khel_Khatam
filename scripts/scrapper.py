"""
scrapper.py
Scrapes top 100 trending songs from Amazon Music and saves to data/data.json
"""

import json
import time
import os

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver


URL = "https://music.amazon.com/popular/songs"


def scrape_top_100():
    driver = get_driver()
    print("Opening Amazon Music page...")
    driver.get(URL)
    time.sleep(6)

    song_title, artist_name, image_url = [], [], []
    target = 100
    start = time.time()

    while len(song_title) < target:
        if time.time() - start > 300:
            print("Hit 5-minute safety limit, stopping.")
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.find_all("music-horizontal-item")
        print(f"  Found {len(items)} items, collected {len(song_title)} so far")

        for item in items:
            primary = item.get("primary-text", "Unknown Title")
            title = primary.split(".", 1)[1].strip() if "." in primary else primary.strip()
            artist = item.get("secondary-text", "Unknown Artist")
            img = item.get("image-src", "")

            song_title.append(title)
            artist_name.append(artist)
            image_url.append(img)

            if len(song_title) >= target:
                break

        if len(song_title) >= target:
            break

        driver.execute_script("window.scrollBy(0, 2000);")
        time.sleep(2.5)

    driver.quit()
    print(f"Scraped {len(song_title)} songs total.")

    df = pd.DataFrame({
        "Track": song_title[:target],
        "Artists": artist_name[:target],
        "Image Url": image_url[:target],
    })
    return df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = scrape_top_100()
    records = df.to_dict(orient="records")
    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(records)} songs → data/data.json")
