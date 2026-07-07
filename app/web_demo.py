from pathlib import Path
from html import escape
from flask import Flask, request, send_file, url_for

from app.stages.image import image_stage
from app.stages.luma_prompt import luma_prompt_stage
from app.stages.publish_asset import publish_asset_stage
from app.stages.luma_submit import run_luma_for_word

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = PROJECT_ROOT / "output" / "luma_videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Unum Momentum Demo</title>
  <style>
    body { margin:0; background:#080808; color:white; font-family:Arial,sans-serif; min-height:100vh; display:flex; align-items:center; justify-content:center; }
    .box { width:min(760px,90vw); text-align:center; }
    h1 { font-size:52px; margin-bottom:12px; }
    p { opacity:.8; font-size:18px; }
    input { width:100%; padding:18px; font-size:24px; border-radius:14px; border:0; margin:28px 0 18px; box-sizing:border-box; text-align:center; }
    button { padding:16px 30px; font-size:18px; border:0; border-radius:999px; cursor:pointer; }
    .note { margin-top:24px; font-size:14px; opacity:.55; }
  </style>
</head>
<body>
  <div class="box">
    <h1>Unum Momentum</h1>
    <p>Ievadi vienu emociju, simbolu vai vārdu.</p>
    <form method="post">
      <input name="word" placeholder="piemēram: cerība, māja, lapsa" required autofocus>
      <button type="submit">Izveidot dzīvo mākslas darbu</button>
    </form>
    <div class="note">Demo v1: image → public asset → Luma → video</div>
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return HTML_FORM

    word = request.form["word"].strip()

    job = {
        "input_emotion": word,
        "emotion": word,
        "word": word
    }

    job = image_stage(job, 1)
    job = luma_prompt_stage(job)
    job = publish_asset_stage(job)

    video_path = Path(run_luma_for_word(word))

    if not video_path.is_absolute():
        video_path = PROJECT_ROOT / video_path

    video_path = video_path.resolve()

    if not video_path.exists():
        return f"""
        <h1>Video file not found</h1>
        <p>{escape(str(video_path))}</p>
        <p><a href="/">Back</a></p>
        """, 500

    filename = video_path.name
    video_url = url_for("video_file", filename=filename)
    safe_word = escape(word)

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{safe_word}</title>
      <style>
        body {{ margin:0; background:#050505; color:white; font-family:Arial,sans-serif; min-height:100vh; }}
        .wrap {{ min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:28px; box-sizing:border-box; }}
        h1 {{ font-size:42px; margin:0 0 22px; }}
        video {{ width:min(1200px,96vw); max-height:78vh; border-radius:18px; background:#000; display:block; }}
        .links {{ margin-top:22px; display:flex; gap:20px; justify-content:center; flex-wrap:wrap; }}
        a {{ color:white; opacity:.85; }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <h1>{safe_word}</h1>
        <video autoplay loop muted playsinline controls preload="auto">
          <source src="{video_url}" type="video/mp4">
        </video>
        <div class="links">
          <a href="{video_url}" target="_blank">Atvērt MP4 tieši</a>
          <a href="/">Izveidot nākamo</a>
        </div>
      </div>
    </body>
    </html>
    """


@app.route("/videos/<filename>")
def video_file(filename):
    path = (VIDEO_DIR / filename).resolve()

    if not path.exists():
        return f"Video not found: {escape(str(path))}", 404

    return send_file(
        path,
        mimetype="video/mp4",
        as_attachment=False,
        conditional=True
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050)
