import os
import time
import json
import requests

USERNAME = os.getenv("RG_USERNAME")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "state.json"

# =========================
# Estado
# =========================
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"last_id": None}

# =========================
# Token
# =========================
def get_token():
    r = requests.get("https://api.redgifs.com/v2/auth/temporary")
    return r.json()["token"]

# =========================
# Obtener gifs
# =========================
def get_latest_gifs(token):
    url = f"https://api.redgifs.com/v2/users/{USERNAME}/search?order=latest"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    return r.json().get("gifs", [])

# =========================
# URL gif
# =========================
def get_gif_url(gif_id, token):
    url = f"https://api.redgifs.com/v2/gifs/{gif_id}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    return r.json()["gif"]["urls"]["hd"]

# =========================
# Descargar
# =========================
def download_gif(gif_id, url, token):
    filename = f"{gif_id}.mp4"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }
    
    with requests.get(url, headers=headers, stream=True) as r:
        with open(filename, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    
    return filename

# =========================
# Discord
# =========================
def send_to_discord(file_path):
    with open(file_path, "rb") as f:
        requests.post(WEBHOOK, files={"file": f})

# =========================
# MAIN
# =========================
token = get_token()
gifs = get_latest_gifs(token)

new_ids = []

for gif in gifs:
    if gif["id"] == state["last_id"]:
        break
    new_ids.append(gif["id"])

if state["last_id"] is None and gifs:
    new_ids = [gifs[0]["id"]]

for gif_id in reversed(new_ids):
    try:
        url = get_gif_url(gif_id, token)
        file_path = download_gif(gif_id, url, token)
        send_to_discord(file_path)
        time.sleep(2)
    except:
        pass

if gifs:
    state["last_id"] = gifs[0]["id"]

with open(STATE_FILE, "w") as f:
    json.dump(state, f)
