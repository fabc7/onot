import os
import time
import json
import requests
import subprocess

USERNAME = os.getenv("RG_USERNAME")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "state.json"

print("=== START ===")

# =========================
# Estado
# =========================
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"last_id": None}

print("Last ID:", state["last_id"])

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
# Comprimir
# =========================
def compress_video(input_file, output_file):
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-vcodec", "libx264",
        "-crf", "28",
        "-preset", "fast",
        "-acodec", "aac",
        "-b:a", "96k",
        output_file
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# =========================
# Discord
# =========================
def send_to_discord(file_path, gif_id):
    size = os.path.getsize(file_path)
    print(f"Size: {size/1024/1024:.2f} MB")

    # enviar directo si cabe
    if size < 8 * 1024 * 1024:
        print("Sending original...")
        with open(file_path, "rb") as f:
            requests.post(WEBHOOK, files={"file": f})
        return

    # comprimir
    compressed = f"compressed_{gif_id}.mp4"
    print("Compressing...")
    compress_video(file_path, compressed)

    new_size = os.path.getsize(compressed)
    print(f"Compressed: {new_size/1024/1024:.2f} MB")

    if new_size < 8 * 1024 * 1024:
        print("Sending compressed...")
        with open(compressed, "rb") as f:
            requests.post(WEBHOOK, files={"file": f})
    else:
        print("Sending link fallback...")
        requests.post(WEBHOOK, json={
            "content": f"🚨 Nuevo contenido 🚨\nhttps://www.redgifs.com/watch/{gif_id}"
        })

# =========================
# MAIN
# =========================
try:
    token = get_token()
    gifs = get_latest_gifs(token)

    if not gifs:
        print("No gifs found")
        exit()

    latest_id = gifs[0]["id"]
    print("Latest:", latest_id)

    new_ids = []

    for gif in gifs:
        if gif["id"] == state["last_id"]:
            break
        new_ids.append(gif["id"])

    # primera ejecución
    if state["last_id"] is None:
        new_ids = [latest_id]

    print("New:", new_ids)

    for gif_id in reversed(new_ids):
        try:
            url = get_gif_url(gif_id, token)
            file_path = download_gif(gif_id, url, token)
            send_to_discord(file_path, gif_id)
            time.sleep(2)
        except Exception as e:
            print("Error:", e)

    state["last_id"] = latest_id

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    print("State updated")

except Exception as e:
    print("Fatal error:", e)

print("=== END ===")
