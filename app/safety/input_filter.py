import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FilterResult:
    allowed: bool
    reason: str = ""
    cleaned_text: str = ""


MAX_INPUT_LENGTH = 80
BLOCKED_TERMS_PATH = Path("knowledge/blocked_terms.json")


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def load_blocked_terms():
    if not BLOCKED_TERMS_PATH.exists():
        return {"contains": [], "regex": []}

    with open(BLOCKED_TERMS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def check_input(text: str) -> FilterResult:
    cleaned = normalize_text(text)

    if not cleaned:
        return FilterResult(False, "Tukšs pieprasījums.", "")

    if len(cleaned) > MAX_INPUT_LENGTH:
        return FilterResult(False, "Pieprasījums ir pārāk garš.", cleaned)

    lowered = cleaned.lower()
    blocked = load_blocked_terms()

    for term in blocked.get("contains", []):
        if term.lower() in lowered:
            return FilterResult(
                False,
                "Pieprasījums tika noraidīts, jo tas satur neatbilstošu vai aizskarošu saturu.",
                cleaned
            )

    for pattern in blocked.get("regex", []):
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return FilterResult(
                False,
                "Pieprasījums tika noraidīts, jo tas satur neatbilstošu vai aizskarošu saturu.",
                cleaned
            )

    return FilterResult(True, "", cleaned)


def filter_inputs(inputs):
    accepted = []
    rejected = []

    for item in inputs:
        result = check_input(item)

        if result.allowed:
            accepted.append(result.cleaned_text)
        else:
            rejected.append({
                "input": item,
                "reason": result.reason
            })

    return accepted, rejected


if __name__ == "__main__":
    tests = [
        "taurenis",
        "cerība",
        "nahuj",
        "bļeģ",
        "māja"
    ]

    accepted, rejected = filter_inputs(tests)

    print("ACCEPTED:")
    print(accepted)

    print()
    print("REJECTED:")
    print(rejected)
