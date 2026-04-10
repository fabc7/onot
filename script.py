import os
import time
import json
import requests
import subprocess

USERNAME = os.getenv("RG_USERNAME")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "state.json"

print("==== DEBUG START ====")
print("USERNAME:", USERNAME)
print("WEBHOOK SET:", WEBHOOK is not None)

# =========================
# Estado
# =========================
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"last_id": None}

print("STATE:", state)

# =========================
# Token
# =========================
def get_token():
    print("Getting token...")
    r = requests.get("https://api.redgifs.com/v2/auth/temporary")
    print("Token status:", r.status_code)
    data = r.json()
    print("Token response keys:", data.keys())
    return data["token"]

def compress_video(input_file, output_file):
    print("Compressing video...")
    
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-vcodec", "libx264",
        "-crf", "28",          # 🔥 clave (menor = más calidad)
        "-preset", "fast",
        "-acodec", "aac",
        "-b:a", "96k",
        output_file
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
# =========================
# Obtener gifs
# =========================
def get_latest_gifs(token):
    print("Fetching gifs...")
    url = f"https://api.redgifs.com/v2/users/{USERNAME}/search?order=latest"
    headers = {"Authorization": f"Bearer {token}"}
    
    r = requests.get(url, headers=headers)
    print("Search status:", r.status_code)
    
    data = r.json()
    print("Response keys:", data.keys())
    
    gifs = data.get("gifs", [])
    print("GIF COUNT:", len(gifs))
    
    if gifs:
        print("FIRST GIF ID:", gifs[0]["id"])
    
    return gifs

# =========================
# Obtener URL gif
# =========================
def get_gif_url(gif_id, token):
    print(f"Getting URL for {gif_id}")
    
    url = f"https://api.redgifs.com/v2/gifs/{gif_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    r = requests.get(url, headers=headers)
    print("GIF status:", r.status_code)
    
    data = r.json()
    return data["gif"]["urls"]["hd"]

# =========================
# Descargar
# =========================
def download_gif(gif_id, url, token):
    print(f"Downloading {gif_id}")
    
    filename = f"{gif_id}.mp4"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }
    
    r = requests.get(url, headers=headers, stream=True)
    print("Download status:", r.status_code)
    
    size = 0
    with open(filename, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
                size += len(chunk)
    
    print(f"Downloaded {size/1024/1024:.2f} MB")
    return filename

# =========================
# Discord
# =========================
def send_to_discord(file_path, gif_id):
    size = os.path.getsize(file_path)
    
    if size < 8 * 1024 * 1024:
        print("Sending original...")
        with open(file_path, "rb") as f:
            requests.post(WEBHOOK, files={"file": f})
        return
    
    # intentar comprimir
    compressed = f"compressed_{gif_id}.mp4"
    compress_video(file_path, compressed)
    
    new_size = os.path.getsize(compressed)
    print(f"Compressed size: {new_size/1024/1024:.2f} MB")
    
    if new_size < 8 * 1024 * 1024:
        print("Sending compressed...")
        with open(compressed, "rb") as f:
            requests.post(WEBHOOK, files={"file": f})
    else:
        print("Still too big → sending link")
        requests.post(WEBHOOK, json={
            "content": f"https://www.redgifs.com/watch/{gif_id}"
        })

# =========================
# MAIN
# =========================
try:
    token = get_token()
    gifs = get_latest_gifs(token)

    if not gifs:
        print("❌ NO GIFS FOUND")
        exit()

    new_ids = []

    for gif in gifs:
        if gif["id"] == state["last_id"]:
            break
        new_ids.append(gif["id"])

    print("NEW IDS:", new_ids)

    if state["last_id"] is None:
        print("First run → forcing 1 download")
        new_ids = [gifs[0]["id"]]

    for gif_id in reversed(new_ids):
        try:
            url = get_gif_url(gif_id, token)
            file_path = download_gif(gif_id, url, token)
            send_to_discord(file_path, gif_id)
            time.sleep(2)
        except Exception as e:
            print("ERROR PROCESSING GIF:", e)

    state["last_id"] = gifs[0]["id"]

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    print("STATE UPDATED:", state)

except Exception as e:
    print("FATAL ERROR:", e)

print("==== DEBUG END ====")
