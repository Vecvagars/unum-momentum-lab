import base64
import json
from pathlib import Path

from app.config import get_openai_client

OUTPUT_DIR = Path("output/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(text):
    return (
        text.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )


def build_world_image(world_state_path="output/collective/latest_world_state.json"):
    client = get_openai_client()

    path = Path(world_state_path)
    world = json.loads(path.read_text(encoding="utf-8"))

    base_prompt = world.get("image_prompt", "").strip()

    if not base_prompt:
        raise RuntimeError("World State has no image_prompt.")

    must_preserve = world.get("must_preserve", [])
    may_transform = world.get("may_transform", [])

    must_preserve_text = ", ".join(must_preserve) if must_preserve else "none"
    may_transform_text = ", ".join(may_transform) if may_transform else "none"

    prompt = f"""
Create one standalone cinematic painterly artwork.

Use this collective world prompt:
{base_prompt}

Must preserve as clearly recognizable visible elements:
{must_preserve_text}

May transform symbolically into light, atmosphere, color, weather, texture or mood:
{may_transform_text}

Important:
This must be one coherent scene, not a collage.
Do not replace must-preserve symbols with unrelated symbols.
If "lapsa" / fox is in must_preserve, show a recognizable fox, not a bird.
If "kaija" / seagull is in must_preserve, show a recognizable seagull, not a generic bird.
If "māja" / house is in must_preserve, show a small welcoming house.
If "upe" / river is in must_preserve, show a visible flowing river.
Preserve several recognizable symbols from the collective inputs.
No text, no letters, no numbers, no captions, no logo, no watermark.
No building facade, no projection mockup, no wall, no frame.
The image itself is the artwork.
Warm, luminous, poetic, emotionally inviting.
Cinematic wide composition.
"""

    result = client.images.generate(
        model="gpt-image-1",
        prompt=" ".join(prompt.split()),
        size="1536x1024"
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    name = safe_filename(world.get("shared_theme", "collective_world"))
    output_path = OUTPUT_DIR / f"batch_{name}.png"

    output_path.write_bytes(image_bytes)

    print("Saved batch image:", output_path)
    return str(output_path)


if __name__ == "__main__":
    build_world_image()
