from pathlib import Path

from app.config import get_openai_client

OUTPUT_DIR = Path("output/batches")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


BLOCKED_WORDS = [
    "fuck", "shit", "bitch",
    "pimpis", "dirsā", "nahuj", "bļeģ",
    "nazi", "hitler"
]


def clean_inputs(inputs):
    cleaned = []

    for item in inputs:
        word = item.strip()

        if not word:
            continue

        lower = word.lower()

        if any(blocked in lower for blocked in BLOCKED_WORDS):
            continue

        if len(word) > 80:
            continue

        cleaned.append(word)

    return cleaned[:15]


def build_batch_prompt(inputs):
    client = get_openai_client()

    safe_inputs = clean_inputs(inputs)

    if not safe_inputs:
        safe_inputs = ["cerība", "gaisma", "miers"]

    joined = "\n".join(f"- {item}" for item in safe_inputs)

    prompt = f"""
You are creating one collective symbolic artwork from multiple visitor inputs.

Festival theme:
"unum momentum" — one moment that changes an inner or outer world.

Visitor inputs:
{joined}

Create one unified painterly scene, not separate objects placed randomly.

Rules:
- Combine all inputs into one coherent symbolic world.
- Preserve several recognizable symbols where possible.
- Do not create a collage.
- Do not create a poster.
- Do not include text, letters, captions, names or logos.
- The scene must feel poetic, warm, luminous, hopeful and emotionally inviting.
- The artwork should feel like many people contributed to one shared living world.
- If some inputs conflict, reinterpret them symbolically and gently.
- Avoid horror, violence, vulgarity, politics, hateful content, sexual content, grim darkness.

Return only one final image prompt in English.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You create concise high-quality image prompts for symbolic projection art."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    final_prompt = response.choices[0].message.content.strip()

    path = OUTPUT_DIR / "latest_batch_prompt.txt"
    path.write_text(final_prompt, encoding="utf-8")

    print("Saved batch prompt:", path)
    print()
    print(final_prompt)

    return final_prompt


if __name__ == "__main__":
    test_inputs = [
        "taurenis",
        "māja",
        "cerība",
        "kaķis",
        "durvis",
        "upe",
        "saule",
        "bērnība",
        "miers",
        "mīlestība"
    ]

    build_batch_prompt(test_inputs)
