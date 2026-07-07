import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.safety.input_filter import check_input

QUEUE_PATH = Path("output/queue/input_queue.json")
QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_queue():
    if not QUEUE_PATH.exists():
        return []

    with open(QUEUE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_queue(queue):
    with open(QUEUE_PATH, "w", encoding="utf-8") as file:
        json.dump(queue, file, ensure_ascii=False, indent=2)


def add_input(text, source="web", ip_address=None):
    result = check_input(text)

    if not result.allowed:
        return {
            "accepted": False,
            "reason": result.reason
        }

    queue = load_queue()

    item = {
        "id": str(uuid.uuid4()),
        "text": result.cleaned_text,
        "source": source,
        "ip_address": ip_address,
        "created_at": now_iso(),
        "status": "queued"
    }

    queue.append(item)
    save_queue(queue)

    return {
        "accepted": True,
        "item": item
    }


def get_pending_inputs(limit=15):
    queue = load_queue()
    pending = [item for item in queue if item.get("status") == "queued"]
    return pending[:limit]


def mark_as_batched(items, batch_id):
    queue = load_queue()
    ids = {item["id"] for item in items}

    for item in queue:
        if item["id"] in ids:
            item["status"] = "batched"
            item["batch_id"] = batch_id
            item["batched_at"] = now_iso()

    save_queue(queue)


def queue_status():
    queue = load_queue()

    return {
        "total": len(queue),
        "queued": len([i for i in queue if i.get("status") == "queued"]),
        "batched": len([i for i in queue if i.get("status") == "batched"])
    }


if __name__ == "__main__":
    tests = ["lapsa", "upe", "māja", "nahuj", "cerība"]

    for item in tests:
        print(item, "=>", add_input(item))

    print()
    print("Pending:")
    print(get_pending_inputs())

    print()
    print("Status:")
    print(queue_status())
