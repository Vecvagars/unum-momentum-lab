from html import escape
from flask import Flask, request, jsonify

from app.stages.input_queue import add_input, queue_status, get_pending_inputs
from app.stages.batch_trigger import create_batch

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Unum Momentum Collective</title>
  <style>
    body { margin:0; background:#080808; color:white; font-family:Arial,sans-serif; min-height:100vh; display:flex; align-items:center; justify-content:center; }
    .box { width:min(760px,90vw); text-align:center; }
    h1 { font-size:50px; margin-bottom:12px; }
    p { opacity:.78; font-size:18px; }
    input { width:100%; padding:18px; font-size:24px; border-radius:14px; border:0; margin:28px 0 18px; box-sizing:border-box; text-align:center; }
    button { padding:16px 30px; font-size:18px; border:0; border-radius:999px; cursor:pointer; }
    .message { margin-top:24px; font-size:18px; }
    .ok { color:#aef5c4; }
    .error { color:#ff9a9a; }
    .status { margin-top:28px; opacity:.65; font-size:14px; }
    a { color:white; opacity:.8; }
  </style>
</head>
<body>
  <div class="box">
    <h1>Unum Momentum</h1>
    <p>Ievadi vienu emociju, simbolu vai vārdu. Tava ievade kļūs par daļu no kopīgas gleznas.</p>
    <form method="post">
      <input name="word" placeholder="piemēram: lapsa, upe, cerība" required autofocus>
      <button type="submit">Pievienot kopīgajai ainai</button>
    </form>
    <div class="status">
      <a href="/status">Skatīt queue statusu</a>
    </div>
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return HTML_FORM

    word = request.form["word"].strip()
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    result = add_input(word, source="web_collective", ip_address=ip_address)

    if not result["accepted"]:
        reason = escape(result["reason"])
        return f"""
        {HTML_FORM}
        <script>
          document.body.innerHTML = `
            <div class="box">
              <h1>Pieprasījums noraidīts</h1>
              <p class="message error">{reason}</p>
              <p><a href="/">Mēģināt vēlreiz</a></p>
            </div>
          `;
        </script>
        """

    safe_word = escape(result["item"]["text"])
    status = queue_status()

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Added</title>
      <style>
        body {{ margin:0; background:#080808; color:white; font-family:Arial,sans-serif; min-height:100vh; display:flex; align-items:center; justify-content:center; }}
        .box {{ width:min(760px,90vw); text-align:center; }}
        h1 {{ font-size:48px; }}
        .ok {{ color:#aef5c4; font-size:20px; }}
        .status {{ margin-top:24px; opacity:.7; }}
        a {{ color:white; }}
      </style>
    </head>
    <body>
      <div class="box">
        <h1>Pievienots</h1>
        <p class="ok">“{safe_word}” ir pievienots kopīgajai ainai.</p>
        <p class="status">Queue: {status["queued"]} gaida apvienošanu.</p>
        <p><a href="/">Pievienot vēl vienu</a></p>
      </div>
    </body>
    </html>
    """


@app.route("/status")
def status():
    return jsonify({
        "status": queue_status(),
        "pending_inputs": get_pending_inputs(limit=15)
    })


@app.route("/admin/create-batch", methods=["POST", "GET"])
def admin_create_batch():
    result = create_batch(force=True)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5051)
