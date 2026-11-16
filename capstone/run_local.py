"""Run the test site on your own computer, for trying the pages (not for subjects).

    pip install Flask absl-py numpy pandas scipy matplotlib seaborn jieba
    python3 capstone/run_local.py
    open http://localhost:8000/jnd/index.html

The pages live at /jnd/... and the API at /jnd/api/..., as on the lab server.
Differences from the server:
- the database is capstone/local.db (made on first run, never committed);
- the audio files are not in git, so every audio is one second of a quiet
  tone: you can click through a whole list, but there is nothing to hear;
- recordings you make are saved in uploads/, as on the server.
Stop it with Ctrl-C. Delete capstone/local.db to start again from nothing.
"""
import io
import math
import os
import struct
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from absl import flags  # noqa: E402

flags.FLAGS(sys.argv[:1])

from flask import Flask, Response, redirect, send_from_directory  # noqa: E402
from werkzeug.middleware.dispatcher import DispatcherMiddleware  # noqa: E402

from api import APIBlueprint  # noqa: E402

PORT = int(os.environ.get("PORT", 8000))
DB = os.path.join(HERE, "local.db")
STATIC = os.path.join(ROOT, "static")


def tone(seconds=1.0, rate=16000):
    """A short, quiet 440 Hz tone as a WAV file."""
    frames = b"".join(
        struct.pack("<h", int(1500 * math.sin(2 * math.pi * 440 * i / rate)))
        for i in range(int(seconds * rate)))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)
    return out.getvalue()


TONE = tone()

api = Flask("api")
api.secret_key = "local only"
api.register_blueprint(APIBlueprint(db_path=DB))

pages = Flask("pages", static_folder=None)


@pages.route("/")
@pages.route("/jnd/")
def home():
    return redirect("/jnd/index.html")


@pages.route("/jnd/audio/<path:name>")
@api.route("/audio/<path:name>")
def audio(name):
    real = os.path.join(STATIC, "audio", name)
    if os.path.isfile(real):
        return send_from_directory(os.path.join(STATIC, "audio"), name)
    return Response(TONE, mimetype="audio/wav")


@pages.route("/jnd/<path:name>")
@pages.route("/jnd/static/<path:name>")
@api.route("/static/<path:name>")
def static_file(name):
    return send_from_directory(STATIC, name)


app = DispatcherMiddleware(pages, {"/jnd/api": api})

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    print(f"Open http://localhost:{PORT}/jnd/index.html  (Ctrl-C to stop)")
    run_simple("127.0.0.1", PORT, app, threaded=True)
