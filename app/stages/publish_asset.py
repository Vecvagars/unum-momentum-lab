import json
import subprocess
from pathlib import Path


REPO_OWNER = "Vecvagars"
REPO_NAME = "unum-momentum-lab"
BRANCH = "main"


def safe_filename(text):
    return (
        text.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )


def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def publish_asset_stage(job):
    word = job.get("input_emotion") or job.get("emotion") or job.get("word")
    if not word:
        raise RuntimeError("Missing word for publish stage")

    image_path = Path(job.get("image_path", ""))
    if not image_path.exists():
        raise RuntimeError(f"Image file does not exist: {image_path}")

    public_dir = Path("public_assets")
    public_dir.mkdir(parents=True, exist_ok=True)

    public_name = f"{safe_filename(word)}.png"
    public_path = public_dir / public_name
    public_path.write_bytes(image_path.read_bytes())

    subprocess.run(["git", "add", str(public_path)], check=True)
    subprocess.run(["git", "commit", "-m", f"Publish {word} asset"], check=False)
    subprocess.run(["git", "push", "origin", BRANCH], check=True)

    sha = run(["git", "rev-parse", "HEAD"])

    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{sha}/public_assets/{public_name}"

    urls_path = Path("knowledge/luma_image_urls.json")
    urls_path.parent.mkdir(parents=True, exist_ok=True)

    if urls_path.exists():
        data = json.loads(urls_path.read_text(encoding="utf-8"))
    else:
        data = {}

    data[word] = url
    urls_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    job["public_image_url"] = url
    print(f"Published asset URL: {url}")

    return job
