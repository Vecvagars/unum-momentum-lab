import json
import sys
from pathlib import Path

from app.stages.semantic_merge import build_collective_world

BATCH_DIR = Path("output/batches")


def latest_batch_path():
    batches = sorted(BATCH_DIR.glob("batch_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not batches:
        raise RuntimeError("No batch files found.")

    return batches[0]


def build_world_from_batch(batch_path=None):
    if batch_path is None:
        batch_path = latest_batch_path()
    else:
        batch_path = Path(batch_path)

    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    inputs = [item["text"] for item in batch["inputs"]]

    world_state = build_collective_world(inputs)

    batch["status"] = "world_created"
    batch["world_state_path"] = "output/collective/latest_world_state.json"

    batch_path.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Updated batch:", batch_path)
    return world_state


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    build_world_from_batch(path)
