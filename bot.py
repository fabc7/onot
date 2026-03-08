import re
import json
import os
import requests
from playwright.sync_api import sync_playwright

PROFILE_URL = os.environ.get("PROFILE_URL")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
DISCORD_USER = os.environ.get("DISCORD_USER")

def log(msg):
    print(f"[BOT] {msg}", flush=True)

def send_discord(msg):
    r = requests.post(WEBHOOK, json={"content": msg})

    log(f"Discord status: {r.status_code}")
    if r.status_code != 204 and r.status_code != 200:
        log(f"Discord response: {r.text}")

def get_counts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(PROFILE_URL, timeout=60000)
        page.wait_for_selector(".b-profile__sections__count")
        counts = page.locator(".b-profile__sections__count").all_inner_texts()

        browser.close()
        
        photos = int(counts[0].strip()) if len(counts) > 0 else 0
        videos = int(counts[1].strip()) if len(counts) > 1 else 0
        likes  = int(counts[2].strip()) if len(counts) > 2 else 0

        return photos, videos, likes

def load_previous():
    try:
        with open("count.json") as f:
            data = json.load(f)
            return data
    except Exception as e:
        log(f"count.json not found ({e})")
        return {"total": 0}

def save_current(total):
    with open("count.json", "w") as f:
        json.dump({"total": total}, f)

def main():
    photos, videos, likes = get_counts()
    total = photos + videos

    prev = load_previous()
    old_total = prev["total"]

    if total > old_total:
        msg = (
            f":ologo: @{DISCORD_USER}\n"
            f"📸 {photos}\n"
            f"🎬 {videos}\n"
            f"❤️ {likes}"
        )
        send_discord(msg)

    else:
        print("No updates")

    save_current(total)


if __name__ == "__main__":
    main()
