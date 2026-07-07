import json
from pathlib import Path
from flask import Flask, jsonify, redirect, send_file, url_for

from app.stages.input_queue import queue_status, get_pending_inputs
from app.stages.batch_trigger import create_batch
from app.stages.batch_to_world import build_world_from_batch
from app.stages.world_state_validator import validate_world_state_file

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = PROJECT_ROOT / "output/queue/input_queue.json"
BATCH_DIR = PROJECT_ROOT / "output/batches"
WORLD_STATE_PATH = PROJECT_ROOT / "output/collective/latest_world_state.json"
VIDEO_DIR = PROJECT_ROOT / "output/luma_videos"
CONFIG_PATH = PROJECT_ROOT / "knowledge/batch_config.json"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path, fallback):
    path = Path(path)
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def batch_config():
    return read_json(CONFIG_PATH, {
        "batch_target_size": 15,
        "batch_min_size": 5,
        "batch_max_wait_seconds": 120,
        "enable_time_trigger": False
    })


def latest_batch():
    batches = sorted(BATCH_DIR.glob("batch_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not batches:
        return None
    path = batches[0]
    data = read_json(path, {})
    data["_path"] = str(path)
    return data


def latest_videos(limit=6):
    videos = sorted(VIDEO_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return videos[:limit]


@app.route("/")
def index():
    status = queue_status()
    pending = get_pending_inputs(limit=30)
    batch = latest_batch()
    world = read_json(WORLD_STATE_PATH, None)
    config = batch_config()
    videos = latest_videos()

    time_trigger_state = "ON" if config.get("enable_time_trigger") else "OFF"
    time_trigger_color = "#aef5c4" if config.get("enable_time_trigger") else "#ffcc88"

    batch_html = "<p>No batch yet.</p>"
    if batch:
        batch_html = f"""
        <p><b>ID:</b> {batch.get('batch_id')}</p>
        <p><b>Status:</b> {batch.get('status')}</p>
        <p><b>Inputs:</b> {batch.get('input_count')}</p>
        <p><b>Path:</b> {batch.get('_path')}</p>
        """

    world_html = "<p>No World State yet.</p>"
    if world:
        world_html = f"""
        <p><b>Theme:</b> {world.get('shared_theme')}</p>
        <p><b>Emotion:</b> {world.get('dominant_emotion')}</p>
        <p><b>Must preserve:</b> {', '.join(world.get('must_preserve', []))}</p>
        <p><b>May transform:</b> {', '.join(world.get('may_transform', []))}</p>
        <details>
          <summary>Open full World State JSON</summary>
          <pre>{json.dumps(world, ensure_ascii=False, indent=2)}</pre>
        </details>
        """

    pending_rows = ""
    for item in pending:
        pending_rows += f"""
        <tr>
          <td>{item.get('text')}</td>
          <td>{item.get('created_at')}</td>
          <td>{item.get('status')}</td>
        </tr>
        """

    video_html = "<p>No videos yet.</p>"
    if videos:
        video_html = ""
        for video in videos:
            video_url = url_for("video_file", filename=video.name)
            video_html += f"""
            <div class="video-card">
              <p><b>{video.name}</b></p>
              <video autoplay muted loop playsinline controls preload="metadata">
                <source src="{video_url}" type="video/mp4">
              </video>
              <p><a href="{video_url}" target="_blank">Open MP4</a></p>
            </div>
            """

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Unum Momentum Admin</title>
      <style>
        body {{ background:#0b0b0b; color:#fff; font-family:Arial,sans-serif; margin:0; padding:32px; }}
        h1 {{ margin-top:0; }}
        .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }}
        .card {{ background:#171717; border-radius:16px; padding:22px; }}
        button, a.button {{ display:inline-block; background:#fff; color:#000; padding:12px 18px; border-radius:999px; text-decoration:none; margin:6px 6px 6px 0; }}
        table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
        td, th {{ border-bottom:1px solid #333; padding:8px; text-align:left; }}
        pre {{ white-space:pre-wrap; background:#050505; padding:16px; border-radius:12px; max-height:460px; overflow:auto; }}
        .muted {{ opacity:.65; }}
        .state {{ color:{time_trigger_color}; font-weight:bold; }}
        video {{ width:100%; border-radius:12px; background:#000; }}
        .video-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
        .video-card {{ background:#0c0c0c; padding:14px; border-radius:14px; }}
        a {{ color:white; opacity:.85; }}
      </style>
    </head>
    <body>
      <h1>Unum Momentum Admin</h1>
      <p class="muted">Safe admin panel: queue, batch, world state, config and output preview.</p>

      <div class="grid">
        <div class="card">
          <h2>Queue</h2>
          <p><b>Total:</b> {status["total"]}</p>
          <p><b>Queued:</b> {status["queued"]}</p>
          <p><b>Batched:</b> {status["batched"]}</p>
          <a class="button" href="/refresh">Refresh</a>
          <a class="button" href="/create-batch">Create Batch Force</a>
        </div>

        <div class="card">
          <h2>Batch Config</h2>
          <p><b>Target size:</b> {config.get("batch_target_size")}</p>
          <p><b>Min size:</b> {config.get("batch_min_size")}</p>
          <p><b>Max wait:</b> {config.get("batch_max_wait_seconds")} sec</p>
          <p><b>Time trigger:</b> <span class="state">{time_trigger_state}</span></p>
          <a class="button" href="/toggle-time-trigger">Toggle Time Trigger</a>
        </div>

        <div class="card">
          <h2>Latest Batch</h2>
          {batch_html}
          <a class="button" href="/build-world">Build World State</a>
          <a class="button" href="/validate-world">Validate World State</a>
        </div>

        <div class="card">
          <h2>Latest World State</h2>
          {world_html}
        </div>

        <div class="card">
          <h2>Pending Inputs</h2>
          <table>
            <tr><th>Input</th><th>Created</th><th>Status</th></tr>
            {pending_rows}
          </table>
        </div>

        <div class="card">
          <h2>Output Preview</h2>
          <p class="muted">Latest generated videos. Autoplay muted loop for quick preview.</p>
          <div class="video-grid">
            {video_html}
          </div>
        </div>
      </div>
    </body>
    </html>
    """


@app.route("/refresh")
def refresh():
    return redirect("/")


@app.route("/toggle-time-trigger")
def toggle_time_trigger():
    config = batch_config()
    config["enable_time_trigger"] = not bool(config.get("enable_time_trigger", False))
    write_json(CONFIG_PATH, config)
    return redirect("/")


@app.route("/create-batch")
def create_batch_route():
    create_batch(force=True)
    return redirect("/")


@app.route("/build-world")
def build_world_route():
    build_world_from_batch()
    return redirect("/")


@app.route("/validate-world")
def validate_world_route():
    result = validate_world_state_file()
    return jsonify(result)


@app.route("/videos/<filename>")
def video_file(filename):
    path = VIDEO_DIR / filename
    if not path.exists():
        return f"Video not found: {path}", 404

    return send_file(
        path,
        mimetype="video/mp4",
        as_attachment=False,
        conditional=True
    )


if __name__ == "__main__":
    app.run(debug=True, port=5052)
