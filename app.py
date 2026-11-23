"""
Extractor – Video & Audio Downloader
Flask-Backend auf Basis von yt-dlp + ffmpeg.

Unterstützt u.a. YouTube, TikTok, Instagram, X/Twitter, Facebook, Vimeo,
Reddit, Twitch, SoundCloud, Dailymotion, Pinterest und >1000 weitere Seiten.
"""

import os
import re
import shutil
import tempfile
import threading
import time
import uuid

from flask import Flask, jsonify, render_template, request, send_file, abort
import yt_dlp

app = Flask(__name__)

DOWNLOAD_ROOT = os.path.join(tempfile.gettempdir(), "extractor_downloads")
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

JOB_TTL_SECONDS = 30 * 60  # fertige Dateien werden nach 30 Minuten gelöscht
MAX_DURATION_SECONDS = int(os.environ.get("MAX_DURATION", 4 * 60 * 60))  # 4h

VIDEO_FORMATS = ["mp4", "webm", "mkv", "mov", "avi"]
AUDIO_FORMATS = ["mp3", "m4a", "wav", "flac", "ogg", "opus", "aac"]
RESOLUTIONS = ["best", "2160", "1440", "1080", "720", "480", "360", "240", "144"]
AUDIO_BITRATES = ["320", "256", "192", "128", "96"]

PLATFORMS = [
    ("YouTube", r"(youtube\.com|youtu\.be)"),
    ("TikTok", r"tiktok\.com"),
    ("Instagram", r"instagram\.com"),
    ("X / Twitter", r"(twitter\.com|x\.com)"),
    ("Facebook", r"(facebook\.com|fb\.watch)"),
    ("Vimeo", r"vimeo\.com"),
    ("Reddit", r"(reddit\.com|redd\.it)"),
    ("Twitch", r"twitch\.tv"),
    ("SoundCloud", r"soundcloud\.com"),
    ("Dailymotion", r"(dailymotion\.com|dai\.ly)"),
    ("Pinterest", r"(pinterest\.|pin\.it)"),
    ("Bilibili", r"bilibili\.com"),
    ("Snapchat", r"snapchat\.com"),
    ("Threads", r"threads\.net"),
    ("Bandcamp", r"bandcamp\.com"),
    ("Streamable", r"streamable\.com"),
]

jobs = {}
jobs_lock = threading.Lock()


def detect_platform(url: str) -> str:
    for name, pattern in PLATFORMS:
        if re.search(pattern, url, re.IGNORECASE):
            return name
    return "Andere"


def valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", url or "", re.IGNORECASE))


def base_opts() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "restrictfilenames": False,
        "socket_timeout": 30,
    }


# ---------------------------------------------------------------- Info

@app.route("/")
def index():
    return render_template(
        "index.html",
        video_formats=VIDEO_FORMATS,
        audio_formats=AUDIO_FORMATS,
        resolutions=RESOLUTIONS,
        bitrates=AUDIO_BITRATES,
        platforms=[p[0] for p in PLATFORMS],
    )


@app.post("/api/info")
def api_info():
    url = (request.json or {}).get("url", "").strip()
    if not valid_url(url):
        return jsonify(error="Bitte einen gültigen Link (http/https) eingeben."), 400
    try:
        with yt_dlp.YoutubeDL(base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        return jsonify(error=clean_error(str(e))), 400
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"Unerwarteter Fehler: {e}"), 500

    if info.get("_type") == "playlist" and info.get("entries"):
        info = next(iter(info["entries"]))

    heights = sorted(
        {f.get("height") for f in info.get("formats") or [] if f.get("height") and f.get("vcodec") != "none"},
        reverse=True,
    )
    has_video = bool(heights) or any(
        f.get("vcodec") != "none" for f in info.get("formats") or [info]
    )

    return jsonify(
        title=info.get("title") or "Unbenannt",
        uploader=info.get("uploader") or info.get("channel") or "",
        duration=info.get("duration"),
        thumbnail=info.get("thumbnail"),
        platform=detect_platform(url) if detect_platform(url) != "Andere" else info.get("extractor_key", "Andere"),
        heights=heights,
        has_video=has_video,
    )


# ---------------------------------------------------------------- Download

def build_opts(job_id: str, workdir: str, kind: str, fmt: str, resolution: str, bitrate: str) -> dict:
    def hook(d):
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                # mehrere Streams (Video + Audio) -> grob skalieren
                job["progress"] = round(done / total * 100, 1) if total else job["progress"]
                job["status"] = "downloading"
                job["speed"] = d.get("speed")
                job["eta"] = d.get("eta")
            elif d["status"] == "finished":
                job["status"] = "processing"

    def pp_hook(d):
        if d["status"] == "started":
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id]["status"] = "processing"

    opts = base_opts()
    opts.update(
        {
            "outtmpl": os.path.join(workdir, "%(title).150B.%(ext)s"),
            "progress_hooks": [hook],
            "postprocessor_hooks": [pp_hook],
            "match_filter": yt_dlp.utils.match_filter_func(f"duration <? {MAX_DURATION_SECONDS}"),
        }
    )

    if kind == "audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "vorbis" if fmt == "ogg" else fmt,
                "preferredquality": bitrate,
            },
            {"key": "FFmpegMetadata"},
        ]
        if fmt in ("mp3", "m4a", "flac"):
            opts["writethumbnail"] = True
            opts["postprocessors"].append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
    else:
        h = "" if resolution == "best" else f"[height<={int(resolution)}]"
        if fmt == "mp4":
            # bevorzugt H.264/AAC für maximale Kompatibilität
            opts["format"] = (
                f"bv*{h}[vcodec^=avc1]+ba[acodec^=mp4a]/"
                f"bv*{h}[ext=mp4]+ba[ext=m4a]/bv*{h}+ba/b{h}/best"
            )
        elif fmt == "webm":
            opts["format"] = f"bv*{h}[ext=webm]+ba[ext=webm]/bv*{h}+ba/b{h}/best"
        else:
            opts["format"] = f"bv*{h}+ba/b{h}/best"

        if fmt in ("mp4", "mkv"):
            opts["merge_output_format"] = fmt
            opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": fmt}]
        else:
            opts["merge_output_format"] = "mkv"
            opts["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": fmt}]
        opts["postprocessors"].append({"key": "FFmpegMetadata"})

    return opts


def run_job(job_id, url, kind, fmt, resolution, bitrate):
    workdir = os.path.join(DOWNLOAD_ROOT, job_id)
    os.makedirs(workdir, exist_ok=True)
    try:
        with yt_dlp.YoutubeDL(build_opts(job_id, workdir, kind, fmt, resolution, bitrate)) as ydl:
            ydl.download([url])

        files = [
            f for f in os.listdir(workdir)
            if f.lower().endswith("." + ("m4a" if fmt == "aac" else fmt)) and not f.endswith((".part", ".ytdl"))
        ]
        if not files:
            files = [f for f in os.listdir(workdir) if not f.endswith((".part", ".ytdl", ".jpg", ".webp", ".png"))]
        if not files:
            raise RuntimeError("Keine Datei erzeugt (evtl. zu lang oder nicht verfügbar).")

        path = os.path.join(workdir, max(files, key=lambda f: os.path.getsize(os.path.join(workdir, f))))
        with jobs_lock:
            jobs[job_id].update(status="done", progress=100, file=path,
                                filename=os.path.basename(path), size=os.path.getsize(path))
    except Exception as e:  # noqa: BLE001
        with jobs_lock:
            jobs[job_id].update(status="error", error=clean_error(str(e)))


@app.post("/api/download")
def api_download():
    data = request.json or {}
    url = (data.get("url") or "").strip()
    kind = data.get("kind", "video")
    fmt = (data.get("format") or "").lower()
    resolution = str(data.get("resolution", "best"))
    bitrate = str(data.get("bitrate", "192"))

    if not valid_url(url):
        return jsonify(error="Ungültiger Link."), 400
    if kind not in ("video", "audio"):
        return jsonify(error="Ungültiger Typ."), 400
    if kind == "video" and fmt not in VIDEO_FORMATS:
        return jsonify(error="Ungültiges Videoformat."), 400
    if kind == "audio" and fmt not in AUDIO_FORMATS:
        return jsonify(error="Ungültiges Audioformat."), 400
    if resolution not in RESOLUTIONS or bitrate not in AUDIO_BITRATES:
        return jsonify(error="Ungültige Qualität."), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {"status": "queued", "progress": 0, "created": time.time()}
    threading.Thread(target=run_job, args=(job_id, url, kind, fmt, resolution, bitrate), daemon=True).start()
    return jsonify(job_id=job_id)


@app.get("/api/progress/<job_id>")
def api_progress(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify(error="Job nicht gefunden."), 404
        return jsonify({k: v for k, v in job.items() if k != "file"})


@app.get("/api/file/<job_id>")
def api_file(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        abort(404)
    return send_file(job["file"], as_attachment=True, download_name=job["filename"])


# ---------------------------------------------------------------- Helpers

def clean_error(msg: str) -> str:
    msg = re.sub(r"\x1b\[[0-9;]*m", "", msg).replace("ERROR: ", "")
    if "Unsupported URL" in msg:
        return "Diese Seite / dieser Link wird nicht unterstützt."
    if "Private video" in msg or "private" in msg.lower() and "video" in msg.lower():
        return "Das Video ist privat oder nicht verfügbar."
    if "Sign in to confirm" in msg:
        return "YouTube verlangt eine Anmeldung (Bot-Schutz). Bitte später erneut versuchen."
    if "does not pass filter" in msg:
        return "Das Video ist zu lang."
    return msg[:300]


def cleanup_loop():
    while True:
        time.sleep(60)
        now = time.time()
        with jobs_lock:
            expired = [j for j, v in jobs.items() if now - v["created"] > JOB_TTL_SECONDS]
            for j in expired:
                jobs.pop(j, None)
        for j in expired:
            shutil.rmtree(os.path.join(DOWNLOAD_ROOT, j), ignore_errors=True)


threading.Thread(target=cleanup_loop, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
