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
    log("Iniciando Playwright")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        log(f"Abriendo perfil: {PROFILE_URL}")

        page.goto(PROFILE_URL, timeout=60000)

        log("Esperando network idle...")
        page.wait_for_load_state("networkidle")

        text = page.inner_text("body")

        log("Página cargada, buscando contadores...")

        photos = re.search(r"(\d+)\s+photos", text, re.IGNORECASE)
        videos = re.search(r"(\d+)\s+videos", text, re.IGNORECASE)

        if photos:
            log(f"Fotos detectadas: {photos.group(1)}")
        else:
            log("No se detectaron fotos")

        if videos:
            log(f"Videos detectados: {videos.group(1)}")
        else:
            log("No se detectaron videos")

        browser.close()

        photos = int(photos.group(1)) if photos else 0
        videos = int(videos.group(1)) if videos else 0

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
