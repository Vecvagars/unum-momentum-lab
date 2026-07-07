import json
from pathlib import Path

from app.config import get_openai_client
from app.safety.input_filter import filter_inputs

OUTPUT_DIR = Path("output/collective")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fallback_world_state(accepted, rejected=None):
    visible = accepted[:6]
    environment = accepted[6:10]
    atmosphere = accepted[10:15]

    image_prompt = (
        "Create one unified painterly symbolic artwork, not a collage. "
        f"Visible anchor symbols: {', '.join(visible)}. "
        f"Environment symbols: {', '.join(environment)}. "
        f"Atmospheric inputs: {', '.join(atmosphere)}. "
        "The scene is warm, luminous, poetic, emotionally inviting, cinematic, painterly, "
        "with no text, no letters, no logo, no captions. Preserve several recognizable symbols "
        "inside one shared living world."
    )

    motion_prompt = (
        "Animate this shared painterly world with slow cinematic camera movement. "
        "Move the actual visible symbols gently where appropriate. "
        "Let light breathe, particles drift, atmosphere flow, water shimmer, leaves move, "
        "and the whole scene feel alive. Do not redesign the image."
    )

    return {
        "shared_theme": "Shared luminous world",
        "shared_story": "A collective symbolic scene formed from multiple visitor inputs.",
        "dominant_emotion": "hopeful calm",
        "visible_anchor_symbols": visible,
        "must_preserve": visible[:4],
        "may_transform": environment + atmosphere,
        "environment_symbols": environment,
        "atmospheric_inputs": atmosphere,
        "input_mapping": {item: "included in the shared world as a visible, environmental or atmospheric element" for item in accepted},
        "rejected_inputs": rejected or [],
        "world_description": "A warm collective painterly world where several visitor symbols coexist in one coherent scene.",
        "composition": "cinematic wide composition with foreground, middle ground and background",
        "lighting": "warm amber light, soft teal shadows, luminous depth",
        "color_language": "warm amber, soft gold, muted teal, deep green, gentle indigo",
        "motion_language": "slow poetic movement, drifting particles, breathing light",
        "image_prompt": image_prompt,
        "motion_prompt": motion_prompt
    }



def postprocess_world_state(world_state, accepted):
    visible = world_state.get("visible_anchor_symbols", [])
    must = world_state.get("must_preserve", [])
    mapping = world_state.get("input_mapping", {})

    if not isinstance(visible, list):
        visible = []

    if not isinstance(must, list):
        must = []

    if not isinstance(mapping, dict):
        mapping = {}

    # Ensure must_preserve symbols are also visible anchors.
    for item in must:
        if item not in visible:
            visible.insert(0, item)

    # If visible is empty, use first accepted inputs.
    if not visible:
        visible = accepted[:6]

    # Keep visible list controlled.
    visible = visible[:7]

    # If must_preserve is empty, preserve first concrete visible symbols.
    if not must:
        must = visible[:4]

    # Keep must_preserve controlled.
    must = must[:5]

    # Ensure mapping includes all accepted + visible + must.
    for item in accepted:
        mapping.setdefault(item, "included in the shared world")
    for item in visible:
        mapping.setdefault(item, "visible anchor symbol in the shared world")
    for item in must:
        mapping.setdefault(item, "must remain clearly recognizable in the image")

    world_state["visible_anchor_symbols"] = visible
    world_state["must_preserve"] = must
    world_state["input_mapping"] = mapping

    image_prompt = world_state.get("image_prompt", "")
    if "no text" not in image_prompt.lower():
        image_prompt += " No text, no letters, no captions, no logo, no watermark."

    motion_prompt = world_state.get("motion_prompt", "")
    if "preserve" not in motion_prompt.lower() and "do not redesign" not in motion_prompt.lower():
        motion_prompt += " Preserve the original image, composition, symbols and painterly style. Do not redesign the scene."

    world_state["image_prompt"] = image_prompt.strip()
    world_state["motion_prompt"] = motion_prompt.strip()

    return world_state

def save_world_state(world_state):
    output_path = OUTPUT_DIR / "latest_world_state.json"
    output_path.write_text(
        json.dumps(world_state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print("Saved:", output_path)
    print(json.dumps(world_state, ensure_ascii=False, indent=2))
    return world_state


def build_collective_world(inputs, use_ai=True):
    accepted, rejected = filter_inputs(inputs)

    if not accepted:
        accepted = ["cerība", "gaisma", "miers"]

    accepted = accepted[:15]

    if not use_ai:
        return save_world_state(postprocess_world_state(fallback_world_state(accepted, rejected), accepted))

    try:
        client = get_openai_client()

        visitor_inputs = "\n".join(f"- {item}" for item in accepted)

        prompt = f"""
You are the Collective Semantic Engine for an interactive AI light-art installation.

Festival theme:
"unum momentum" — one moment that changes an inner or outer world.

Visitor inputs:
{visitor_inputs}

Task:
Create ONE coherent shared symbolic world from these inputs.

Important principles:
- This must be one unified painting, not a collage.
- Preserve recognizable contributions from multiple visitors whenever artistically possible.
- Use 3 to 6 visible anchor symbols maximum.
- Concrete nouns such as animals, objects, places and natural elements should usually be preserved as visible recognizable symbols.
- Abstract emotions or concepts may become light, atmosphere, weather, color, movement or mood.
- Include a must_preserve list for symbols that must remain visually recognizable.
- Include a may_transform list for inputs that may be transformed symbolically.
- Additional inputs may become environment, light, weather, color, texture, atmosphere or motion.
- Do not include text, letters, captions, names, logos or typography in the artwork.
- Avoid horror, violence, vulgarity, hateful content, explicit sexual content, political propaganda and grim darkness.
- The result should feel poetic, warm, luminous, painterly, emotionally inviting and suitable for animation.

Return JSON only with exactly this structure:
{{
  "shared_theme": "...",
  "shared_story": "...",
  "dominant_emotion": "...",
  "visible_anchor_symbols": ["...", "..."],
  "must_preserve": ["concrete nouns that must remain visibly recognizable"],
  "may_transform": ["abstract inputs that may become light, atmosphere, color, weather or emotion"],
  "environment_symbols": ["...", "..."],
  "atmospheric_inputs": ["...", "..."],
  "input_mapping": {{
    "original input": "how it appears or is transformed in the world"
  }},
  "world_description": "...",
  "composition": "...",
  "lighting": "...",
  "color_language": "...",
  "motion_language": "...",
  "image_prompt": "...",
  "motion_prompt": "..."
}}
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only. You design collective symbolic worlds for AI projection art."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.75
        )

        raw = response.choices[0].message.content.strip()
        world_state = json.loads(raw)
        world_state["rejected_inputs"] = rejected
        world_state = postprocess_world_state(world_state, accepted)

        return save_world_state(world_state)

    except Exception as error:
        print("AI semantic merge failed, using fallback.")
        print("Reason:", error)
        return save_world_state(postprocess_world_state(fallback_world_state(accepted, rejected), accepted))


if __name__ == "__main__":
    test_inputs = [
        "lapsa",
        "upe",
        "māja",
        "durvis",
        "cerība",
        "kaija",
        "mežs",
        "bērnība",
        "saule",
        "miers",
        "mīlestība",
        "taurenis"
    ]

    build_collective_world(test_inputs)
