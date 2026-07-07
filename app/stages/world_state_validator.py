import json
from pathlib import Path


REQUIRED_FIELDS = [
    "shared_theme",
    "shared_story",
    "dominant_emotion",
    "visible_anchor_symbols",
    "must_preserve",
    "may_transform",
    "environment_symbols",
    "atmospheric_inputs",
    "input_mapping",
    "world_description",
    "composition",
    "lighting",
    "color_language",
    "motion_language",
    "image_prompt",
    "motion_prompt"
]


def load_world_state(path="output/collective/latest_world_state.json"):
    path = Path(path)

    if not path.exists():
        raise RuntimeError(f"World State file does not exist: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def validate_world_state(world):
    errors = []
    warnings = []

    for field in REQUIRED_FIELDS:
        if field not in world:
            errors.append(f"Missing required field: {field}")

    for field in [
        "shared_theme",
        "shared_story",
        "dominant_emotion",
        "world_description",
        "composition",
        "lighting",
        "color_language",
        "motion_language",
        "image_prompt",
        "motion_prompt"
    ]:
        value = world.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Field must be non-empty string: {field}")

    for field in [
        "visible_anchor_symbols",
        "must_preserve",
        "may_transform",
        "environment_symbols",
        "atmospheric_inputs"
    ]:
        value = world.get(field)
        if not isinstance(value, list):
            errors.append(f"Field must be list: {field}")

    if not isinstance(world.get("input_mapping"), dict):
        errors.append("Field must be object/dict: input_mapping")

    visible = world.get("visible_anchor_symbols", [])
    must = world.get("must_preserve", [])
    mapping = world.get("input_mapping", {})

    if isinstance(visible, list) and len(visible) > 7:
        warnings.append("Too many visible anchor symbols. Recommended maximum: 6–7.")

    if isinstance(must, list) and len(must) > 5:
        warnings.append("Too many must_preserve symbols. Recommended maximum: 3–5.")

    if isinstance(must, list) and not must:
        warnings.append("must_preserve is empty. Image may become too abstract.")

    if isinstance(visible, list) and isinstance(must, list):
        missing_from_visible = [item for item in must if item not in visible]
        if missing_from_visible:
            warnings.append(f"must_preserve contains symbols not in visible_anchor_symbols: {missing_from_visible}")

    if isinstance(mapping, dict) and isinstance(visible, list):
        for symbol in visible:
            if symbol not in mapping:
                warnings.append(f"Visible symbol missing from input_mapping: {symbol}")

    image_prompt = world.get("image_prompt", "")
    motion_prompt = world.get("motion_prompt", "")

    forbidden_text_terms = ["text", "letters", "captions", "logo"]
    if isinstance(image_prompt, str):
        lowered = image_prompt.lower()
        if "no text" not in lowered and "do not include text" not in lowered:
            warnings.append("image_prompt does not explicitly forbid text.")
        if len(image_prompt) < 120:
            warnings.append("image_prompt is quite short.")
        if len(image_prompt) > 2500:
            warnings.append("image_prompt is very long.")

    if isinstance(motion_prompt, str):
        lowered = motion_prompt.lower()
        if "do not redesign" not in lowered and "preserve" not in lowered:
            warnings.append("motion_prompt should explicitly preserve the original image.")
        if len(motion_prompt) < 80:
            warnings.append("motion_prompt is quite short.")
        if len(motion_prompt) > 1800:
            warnings.append("motion_prompt is very long.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_world_state_file(path="output/collective/latest_world_state.json"):
    world = load_world_state(path)
    result = validate_world_state(world)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    validate_world_state_file()
