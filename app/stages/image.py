import json
import base64
from pathlib import Path
from openai import OpenAI

OUTPUT_DIR = Path("output/images")
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


def build_symbol_instruction(word):
    w = word.strip().lower()

    known_symbols = {
        "taurenis": {
            "subject": "a clearly recognizable butterfly with delicate wings and antennae",
            "avoid": "Do not depict a bull, horns, cattle, skull, moth-human hybrid, or monster."
        },
        "butterfly": {
            "subject": "a clearly recognizable butterfly with delicate wings and antennae",
            "avoid": "Do not depict a bull, horns, cattle, skull, moth-human hybrid, or monster."
        },
        "kaķis": {
            "subject": "a graceful symbolic cat, recognizable, painterly, not photorealistic",
            "avoid": "Do not make it cartoonish, cute mascot-like, photorealistic, realistic animal portrait, or scary."
        },
        "cat": {
            "subject": "a graceful symbolic cat, recognizable, painterly, not photorealistic",
            "avoid": "Do not make it cartoonish, cute mascot-like, photorealistic, realistic animal portrait, or scary."
        },
        "māja": {
            "subject": "a small welcoming house glowing from within, a symbol of belonging and safety",
            "avoid": "Do not make it realistic architecture, abandoned, horror-like, gloomy, or placed on a building facade."
        },
        "home": {
            "subject": "a small welcoming house glowing from within, a symbol of belonging and safety",
            "avoid": "Do not make it realistic architecture, abandoned, horror-like, gloomy, or placed on a building facade."
        },
        "durvis": {
            "subject": "a luminous open doorway, clearly recognizable as a door, leading into warm light",
            "avoid": "Do not turn it into a mountain, portal logo, monument, building facade, projection mockup, or abstract arch only."
        },
        "door": {
            "subject": "a luminous open doorway, clearly recognizable as a door, leading into warm light",
            "avoid": "Do not turn it into a mountain, portal logo, monument, building facade, projection mockup, or abstract arch only."
        },
        "cerība": {
            "subject": "a rising warm light, opening forms, young leaves, and a sense of new beginning",
            "avoid": "Do not make it sad, empty, dark, apocalyptic, overly abstract, or placed on a building facade."
        },
        "hope": {
            "subject": "a rising warm light, opening forms, young leaves, and a sense of new beginning",
            "avoid": "Do not make it sad, empty, dark, apocalyptic, overly abstract, or placed on a building facade."
        }
    }

    return known_symbols.get(w, {
        "subject": f"a poetic but still recognizable symbolic interpretation of '{word}'",
        "avoid": "Do not make it too literal, photorealistic, scary, grotesque, unreadably abstract, or placed on a building facade."
    })


def build_prompt(job):
    style = load_json("knowledge/style_profile.json")

    word = job.get("input_emotion") or job.get("emotion") or job.get("word") or "cerība"
    symbol = build_symbol_instruction(word)

    palette = ", ".join(style["visual_dna"]["color_palette"])
    mood = ", ".join(style["visual_dna"]["mood"])
    brush = ", ".join(style["visual_dna"]["brush_language"])
    avoid = ", ".join(style["visual_dna"]["avoid"])

    prompt = f"""
Create one standalone painterly artwork image.

Input word / emotion:
{word}

Main symbolic subject:
{symbol["subject"]}

Recognition:
The main subject must remain clearly recognizable.
It may be poetic, luminous and stylized, but it must not disappear into abstraction.

Scene:
Create an immersive inner dream-world around the subject.
This is a complete artwork, not a photo of an artwork, not a mural, not a projection mockup.
The image must fill the full frame as its own world.

Emotional direction:
The image must feel {mood}.
Warm, hopeful, generous, poetic, emotionally inviting.
Calm but alive.
Avoid horror, sadness, grim mysticism, heaviness and empty darkness.

Painterly style:
{brush}.
Refined oil-painting / luminous glaze feeling.
Visible artistic brushwork.
Rich pigment.
Soft atmospheric depth.
Not cartoon.
Not children-book illustration.
Not photorealistic.
Not realistic animal portrait.
Not flat poster.
Not graphic design.

Color palette:
{palette}.
Use warm amber light, golden ochre, burnt sienna, muted teal shadows, deep forest greens, soft indigo atmosphere.
Avoid washed-out pastel blue.
Avoid pale white haze.
Maintain depth and contrast while preserving a calm, dreamlike feeling.

Composition:
A cinematic wide artwork composition.
No physical building.
No facade.
No architecture around the image unless the input itself is house or door.
No projection screen.
No mural mockup.
No street.
No windows around the artwork.
No audience.
No frame border.
No photograph of an artwork.
Only the imagined painterly world itself.

Motion potential:
The still image should imply slow poetic animation:
light breathing, particles drifting, leaves moving, clouds flowing, wings shimmering, paths glowing.

Hard restrictions:
{symbol["avoid"]}
Avoid: {avoid}.
No readable text.
No letters.
No typography.
No captions.
No logo.
No watermark.
"""

    return " ".join(prompt.split())


def image_stage(job, index):
    client = OpenAI()
    prompt = build_prompt(job)

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024"
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    word = job.get("input_emotion") or job.get("emotion") or job.get("word") or "image"
    filename = f"{index:03d}_{safe_filename(word)}.png"
    output_path = OUTPUT_DIR / filename

    with open(output_path, "wb") as file:
        file.write(image_bytes)

    job["image_prompt"] = prompt
    job["image_path"] = str(output_path)

    print(f"Saved image: {output_path}")
    return job
