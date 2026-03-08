import re
import json
import os
import requests
from playwright.sync_api import sync_playwright

PROFILE_URL = os.environ.get("PROFILE_URL")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK")


def log(msg):
    print(f"[BOT] {msg}", flush=True)


def send_discord(msg):
    log("Enviando mensaje a Discord...")
    r = requests.post(WEBHOOK, json={"content": msg})

    log(f"Discord status: {r.status_code}")
    if r.status_code != 204 and r.status_code != 200:
        log(f"Discord response: {r.text}")


def get_counts():
    print("[BOT] Iniciando Playwright")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[BOT] Abriendo perfil: {PROFILE_URL}")
        page.goto(PROFILE_URL, timeout=60000)

        page.wait_for_selector(".b-profile__sections__count")

        print("[BOT] Extrayendo contadores...")

        counts = page.locator(".b-profile__sections__count").all_inner_texts()

        browser.close()

        print(f"[BOT] Contadores detectados: {counts}")

        photos = int(counts[0]) if len(counts) > 0 else 0
        videos = int(counts[1]) if len(counts) > 1 else 0

        return photos, videos


def load_previous():
    log("Cargando contador previo")

    try:
        with open("count.json") as f:
            data = json.load(f)
            log(f"Total previo: {data['total']}")
            return data
    except Exception as e:
        log(f"No existe count.json ({e})")
        return {"total": 0}


def save_current(total):
    log(f"Guardando nuevo total: {total}")

    with open("count.json", "w") as f:
        json.dump({"total": total}, f)


def main():
    log("Bot iniciado")

    if not PROFILE_URL:
        log("ERROR: PROFILE_URL no definido")
        return

    if not WEBHOOK:
        log("ERROR: DISCORD_WEBHOOK no definido")
        return

    photos, videos = get_counts()

    total = photos + videos
    log(f"Total actual: {total}")

    prev = load_previous()
    old_total = prev["total"]

    log(f"Total previo: {old_total}")

    if total > old_total:
        log("Nuevo contenido detectado!")

        msg = f"📢 Nuevo contenido detectado\nFotos: {photos}\nVideos: {videos}"
        send_discord(msg)
    else:
        log("No hay contenido nuevo")

    save_current(total)

    log("Bot terminado")


if __name__ == "__main__":
    main()

