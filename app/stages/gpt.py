import json
from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

client = OpenAI(api_key=OPENAI_API_KEY)


def clean_json_block(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1).strip()

    if text.startswith("```"):
        text = text.replace("```", "", 1).strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def gpt_stage(job: dict) -> dict:
    emotion = job["emotion"]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(emotion=emotion),
            },
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content
    cleaned = clean_json_block(content)

    job["gpt_raw"] = content

    try:
        job["art_direction"] = json.loads(cleaned)
    except json.JSONDecodeError:
        job["art_direction"] = {"error": "Invalid JSON", "raw": content}

    return job
