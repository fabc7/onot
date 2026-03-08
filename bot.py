import re
import json
import os
import requests
from playwright.sync_api import sync_playwright

PROFILE_URL = os.environ.get("PROFILE_URL")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

def send_discord(msg):
    requests.post(WEBHOOK, json={"content": msg})

def get_counts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(PROFILE_URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        text = page.inner_text("body")

        photos = re.search(r"(\d+)\s+photos", text)
        videos = re.search(r"(\d+)\s+videos", text)

        browser.close()

        photos = int(photos.group(1)) if photos else 0
        videos = int(videos.group(1)) if videos else 0

        return photos, videos

def load_previous():
    try:
        with open("count.json") as f:
            return json.load(f)
    except:
        return {"total": 0}

def save_current(total):
    with open("count.json","w") as f:
        json.dump({"total": total}, f)

def main():
    if not PROFILE_URL or not WEBHOOK:
        raise Exception("Faltan variables de entorno")

    photos, videos = get_counts()
    total = photos + videos

    prev = load_previous()
    old_total = prev["total"]

    if total > old_total:
        msg = f"📢 Nuevo contenido detectado\nFotos: {photos}\nVideos: {videos}"
        send_discord(msg)

    save_current(total)

if __name__ == "__main__":
    main()
