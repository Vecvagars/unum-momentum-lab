import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

load_dotenv()

LUMA_API_KEY = os.getenv("LUMA_API_KEY")
BASE_URL = "https://api.lumalabs.ai/dream-machine/v1/generations"

OUTPUT_DIR = Path("output/luma_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_filename(text):
    return (
        text.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )


def submit_luma_generation(prompt, image_url):
    if not LUMA_API_KEY:
        raise RuntimeError("LUMA_API_KEY missing in .env")

    payload = {
        "prompt": prompt,
        "model": "ray-2",
        "resolution": "720p",
        "duration": "5s",
        "loop": True,
        "keyframes": {
            "frame0": {
                "type": "image",
                "url": image_url
            }
        }
    }

    response = requests.post(
        BASE_URL,
        headers={
            "accept": "application/json",
            "authorization": f"Bearer {LUMA_API_KEY}",
            "content-type": "application/json"
        },
        json=payload,
        timeout=60
    )

    response.raise_for_status()
    return response.json()


def get_generation(generation_id):
    response = requests.get(
        f"{BASE_URL}/{generation_id}",
        headers={
            "accept": "application/json",
            "authorization": f"Bearer {LUMA_API_KEY}"
        },
        timeout=60
    )

    response.raise_for_status()
    return response.json()


def download_video(url, output_path):
    response = requests.get(url, timeout=300)
    response.raise_for_status()

    with open(output_path, "wb") as file:
        file.write(response.content)


def run_luma_for_word(word):
    image_urls = load_json("knowledge/luma_image_urls.json")
    image_url = image_urls.get(word, "").strip()

    if not image_url:
        raise RuntimeError(
            f"No image URL set for '{word}' in knowledge/luma_image_urls.json"
        )

    prompt_path = Path("output/luma") / f"{word}.txt"

    if not prompt_path.exists():
        raise RuntimeError(f"Missing Luma prompt: {prompt_path}")

    prompt = prompt_path.read_text(encoding="utf-8")

    print(f"Submitting to Luma: {word}")
    generation = submit_luma_generation(prompt, image_url)

    generation_id = generation["id"]
    print(f"Luma generation ID: {generation_id}")

    while True:
        status_data = get_generation(generation_id)
        state = status_data.get("state") or status_data.get("status")

        print(f"Status: {state}")

        if state == "completed":
            assets = status_data.get("assets", {})
            video_url = assets.get("video")

            if not video_url:
                raise RuntimeError("Generation completed but no video URL found.")

            output_path = OUTPUT_DIR / f"{safe_filename(word)}.mp4"
            download_video(video_url, output_path)

            print(f"Saved video: {output_path}")
            return str(output_path)

        if state in ["failed", "error"]:
            raise RuntimeError(f"Luma generation failed: {status_data}")

        time.sleep(10)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m app.stages.luma_submit <word>")

    run_luma_for_word(sys.argv[1])
