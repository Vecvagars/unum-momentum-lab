import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.stages.input_queue import get_pending_inputs, mark_as_batched

BATCH_DIR = Path("output/batches")
BATCH_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = Path("knowledge/batch_config.json")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_config():
    if not CONFIG_PATH.exists():
        return {
            "batch_target_size": 15,
            "batch_min_size": 5,
            "batch_max_wait_seconds": 120,
            "enable_time_trigger": False
        }

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def seconds_since_oldest(items):
    if not items:
        return 0

    oldest = min(datetime.fromisoformat(item["created_at"]) for item in items)
    return (datetime.now(timezone.utc) - oldest).total_seconds()


def create_batch(force=False):
    config = load_config()

    target_size = int(config.get("batch_target_size", 15))
    min_size = int(config.get("batch_min_size", 5))
    max_wait = int(config.get("batch_max_wait_seconds", 120))
    enable_time_trigger = bool(config.get("enable_time_trigger", False))

    pending = get_pending_inputs(limit=target_size)
    pending_count = len(pending)
    oldest_wait = seconds_since_oldest(pending)

    if force and pending_count > 0:
        reason = "Forced batch creation."

    elif pending_count >= target_size:
        reason = f"Target batch size reached: {pending_count}/{target_size}."

    elif enable_time_trigger and pending_count >= min_size and oldest_wait >= max_wait:
        reason = f"Time trigger enabled: minimum batch size reached and max wait exceeded: {pending_count}/{min_size}, {int(oldest_wait)}s/{max_wait}s."

    else:
        return {
            "created": False,
            "reason": f"Waiting. Pending: {pending_count}, target: {target_size}, min: {min_size}, oldest_wait_seconds: {int(oldest_wait)}, max_wait_seconds: {max_wait}, enable_time_trigger: {enable_time_trigger}.",
            "pending_count": pending_count
        }

    batch_id = f"batch_{uuid.uuid4().hex[:10]}"

    batch = {
        "batch_id": batch_id,
        "created_at": now_iso(),
        "status": "created",
        "reason": reason,
        "input_count": pending_count,
        "inputs": pending,
        "config": {
            "batch_target_size": target_size,
            "batch_min_size": min_size,
            "batch_max_wait_seconds": max_wait,
            "enable_time_trigger": enable_time_trigger
        }
    }

    batch_path = BATCH_DIR / f"{batch_id}.json"
    batch_path.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    mark_as_batched(pending, batch_id)

    print("Created batch:", batch_path)
    print(json.dumps(batch, ensure_ascii=False, indent=2))

    return {
        "created": True,
        "batch": batch,
        "batch_path": str(batch_path)
    }


if __name__ == "__main__":
    create_batch(force=False)
