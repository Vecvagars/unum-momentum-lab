from pathlib import Path

OUTPUT_DIR = Path("output/luma")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_motion_profile(word):
    w = word.strip().lower()

    profiles = {
        "taurenis": {
            "subject_motion": "The butterfly slowly opens and closes its wings with gentle natural fluttering. Its body subtly rises and drifts forward.",
            "environment_motion": "Flowers sway softly, pollen floats through the air, small light particles spiral around the wings.",
            "camera": "Very slow cinematic push-in with a slight upward drift toward the butterfly."
        },
        "kaķis": {
            "subject_motion": "The cat slowly turns its head, blinks gently, and its tail moves with a soft graceful motion.",
            "environment_motion": "Leaves move slightly, tiny glowing particles drift around the cat, warm light shifts softly.",
            "camera": "Very slow push-in toward the cat, keeping the composition stable."
        },
        "māja": {
            "subject_motion": "Warm light inside the house gently flickers, curtains move slightly, soft smoke rises slowly from the chimney.",
            "environment_motion": "Grass and flowers sway gently, clouds move slowly, glowing particles drift near the path.",
            "camera": "Slow forward movement along the path toward the house."
        },
        "durvis": {
            "subject_motion": "The open doorway emits a slow breathing light. The door opens just a little more, very subtly.",
            "environment_motion": "Mist flows gently toward the doorway, particles drift through the opening, warm light expands outward.",
            "camera": "Slow push forward toward the doorway, as if approaching the threshold."
        },
        "cerība": {
            "subject_motion": "The glowing sprout slowly grows upward, leaves unfold gently, light rises from the ground.",
            "environment_motion": "Small particles float upward, the surrounding field brightens slowly, clouds open softly.",
            "camera": "Very slow upward push following the rising light."
        }
    }

    return profiles.get(w, {
        "subject_motion": "The main subject gently moves in a natural poetic way, not just glowing.",
        "environment_motion": "Atmosphere, particles, light and surrounding elements move slowly and visibly.",
        "camera": "Very slow cinematic push-in."
    })


def build_luma_prompt(job):
    word = (
        job.get("input_emotion")
        or job.get("emotion")
        or job.get("word")
        or "emotion"
    )

    motion = get_motion_profile(word)

    prompt = f"""
Animate this painterly artwork as a living scene.

Preserve the original image, composition, subject and style.
Do not redesign the image.
Do not replace the subject.
Do not add new main objects.

Important:
The animation must move the actual subject, not only add glow effects.
Avoid simple light flicker only.
Avoid only camera zoom.
Avoid warping the entire image.

Subject motion:
{motion["subject_motion"]}

Environment motion:
{motion["environment_motion"]}

Camera:
{motion["camera"]}

Lighting:
Warm light gently breathes and shifts.
Highlights shimmer softly, but the image must not become only a glow effect.

Animation style:
Slow, poetic, painterly, elegant.
The painting should feel alive.
Motion should be visible but gentle.

Loop:
Create a seamless 5 second loop.

Input concept:
{word}
"""

    return " ".join(prompt.split())


def luma_prompt_stage(job):
    prompt = build_luma_prompt(job)

    word = (
        job.get("input_emotion")
        or job.get("emotion")
        or job.get("word")
        or "image"
    )

    path = OUTPUT_DIR / f"{word}.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write(prompt)

    job["luma_prompt"] = prompt
    job["luma_prompt_path"] = str(path)

    print(f"Saved Luma prompt: {path}")

    return job
