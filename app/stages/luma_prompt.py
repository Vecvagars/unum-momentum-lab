from pathlib import Path

OUTPUT_DIR = Path("output/luma")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_luma_prompt(job):

    word = (
        job.get("input_emotion")
        or job.get("emotion")
        or job.get("word")
        or "emotion"
    )

    prompt = f"""
Animate this painterly artwork.

The artwork itself must remain unchanged.

Do not redesign the composition.
Do not replace the subject.
Do not invent new objects.
Do not alter the symbolic meaning.

Camera:
Very slow cinematic push-in.

Motion:
Gentle breathing movement.
Soft drifting particles.
Slow moving atmosphere.
Subtle environmental motion.
Tiny shimmering highlights.

Lighting:
Warm volumetric light.
Very soft fluctuations.
Natural glow.

Mood:
Hopeful.
Dreamlike.
Poetic.
Emotionally inviting.

Animation speed:
Very slow.

Loop:
Create a perfect seamless loop.

Style preservation:
Maintain the same painterly brushwork.
Maintain the same color palette.
Maintain the same composition.
Maintain the same symbolic subject.
Maintain the same emotional atmosphere.

The animation should feel like the painting has quietly come alive.

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
