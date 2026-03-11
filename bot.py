import re
import json
import os
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import random

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
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--window-size=1280,800"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/Santiago"
        )

        page = context.new_page()
        stealth_sync(page)

        log(f"Opening {PROFILE_URL}")

        # retry loop por si Cloudflare aparece
        for attempt in range(3):

            page.goto(PROFILE_URL, timeout=60000, wait_until="domcontentloaded")

            # esperar render JS
            page.wait_for_timeout(random.randint(6000, 9000))

            html = page.content()

            with open("debug.html", "w") as f:
                f.write(html)

            log(f"HTML length: {len(html)}")

            if "Cloudflare" in html or "Just a moment" in html:
                log(f"Cloudflare detected (attempt {attempt+1})")
                page.wait_for_timeout(5000)
                continue

            if "b-profile__sections__count" not in html:
                log("Counts selector NOT in HTML")
                continue

            break

        try:
            page.wait_for_selector(".b-profile__sections__count", timeout=30000)
        except Exception as e:
            log(f"Selector timeout: {e}")

        counts = page.locator(".b-profile__sections__count").all_inner_texts()
        log(f"Raw counts: {counts}")

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
            f"<:ologo:1480256858844303582> <@{DISCORD_USER}>\n"
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



