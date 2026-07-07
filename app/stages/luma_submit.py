import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

LUMA_API_KEY = os.getenv("LUMA_API_KEY")
BASE_URL = "https://agents.lumalabs.ai/v1/generations"

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


def headers():
    if not LUMA_API_KEY:
        raise RuntimeError("LUMA_API_KEY missing in .env")

    return {
        "Authorization": f"Bearer {LUMA_API_KEY}",
        "Content-Type": "application/json",
    }


def submit_luma_generation(prompt, image_url):
    payload = {
        "model": "ray-3.2",
        "type": "video",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "video": {
            "resolution": "720p",
            "duration": "5s",
            "loop": True,
            "start_frame": {
                "url": image_url
            }
        }
    }

    response = requests.post(
        BASE_URL,
        headers=headers(),
        json=payload,
        timeout=60
    )

    if not response.ok:
        print("Luma Agents submit failed")
        print("Status:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()

    return response.json()


def get_generation(generation_id):
    response = requests.get(
        f"{BASE_URL}/{generation_id}",
        headers=headers(),
        timeout=60
    )

    if not response.ok:
        print("Luma Agents poll failed")
        print("Status:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()

    return response.json()


def download_video(url, output_path):
    response = requests.get(url, timeout=300)
    response.raise_for_status()

    with open(output_path, "wb") as file:
        file.write(response.content)


def extract_video_url(generation):
    output = generation.get("output", [])

    for item in output:
        if item.get("type") == "video" and item.get("url"):
            return item["url"]

    return None


def run_luma_for_word(word):
    image_urls = load_json("knowledge/luma_image_urls.json")
    image_url = image_urls.get(word, "").strip()

    if not image_url:
        raise RuntimeError(f"No image URL set for '{word}' in knowledge/luma_image_urls.json")

    prompt_path = Path("output/luma") / f"{word}.txt"

    if not prompt_path.exists():
        raise RuntimeError(f"Missing Luma prompt: {prompt_path}")

    prompt = prompt_path.read_text(encoding="utf-8")

    print(f"Submitting to Luma Agents: {word}")
    generation = submit_luma_generation(prompt, image_url)

    generation_id = generation["id"]
    print(f"Luma generation ID: {generation_id}")

    deadline = time.time() + 600
    time.sleep(10)

    while True:
        generation = get_generation(generation_id)
        state = generation.get("state")

        print(f"Status: {state}")

        if state == "completed":
            video_url = extract_video_url(generation)

            if not video_url:
                raise RuntimeError(f"Generation completed but no video URL found: {generation}")

            output_path = OUTPUT_DIR / f"{safe_filename(word)}.mp4"
            download_video(video_url, output_path)

            print(f"Saved video: {output_path}")
            return str(output_path)

        if state == "failed":
            raise RuntimeError(f"Luma generation failed: {generation}")

        if time.time() > deadline:
            raise TimeoutError(f"Luma generation {generation_id} did not complete in time")

        time.sleep(5)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m app.stages.luma_submit <word>")

    run_luma_for_word(sys.argv[1])
