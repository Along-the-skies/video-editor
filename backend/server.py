import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.est import get_duration
from backend.helper import load_session, save_session, is_video
from backend.fitting import compute_timeline
from backend.segments import build_image_segment, build_video_segment, concat_segments, mux_audio, build_preview

app = FastAPI()

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
TMP_ROOT = Path(__file__).resolve().parent.parent / "tmp"

TMP_ROOT.mkdir(exist_ok=True)

CURRENT_SESSION_FILE = TMP_ROOT / "current_session.txt"


def set_current_session(session_id: str):
    CURRENT_SESSION_FILE.write_text(session_id)


def get_current_session() -> str:
    if CURRENT_SESSION_FILE.exists():
        return CURRENT_SESSION_FILE.read_text().strip()
    return ""


def clear_current_session_if_matches(session_id: str):
    if get_current_session() == session_id:
        CURRENT_SESSION_FILE.write_text("")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/upload")
def upload():
    return FileResponse(FRONTEND / "upload.html")

@app.get("/donate")
def donate():
    return FileResponse(FRONTEND / "donate.html")

@app.get("/assets/qr-image.jpeg")
def qr():
    return FileResponse(FRONTEND / "assets" / "qr-image.jpeg")

@app.get("/generate")
def generate_page():
    return FileResponse(FRONTEND / "generate.html")

@app.get("/Readme")
def readme():
    return FileResponse(FRONTEND / "Readme.html")

@app.get("/style.css")
def style():
    return FileResponse(FRONTEND / "style.css")

@app.get("/script.js")
def script():
    return FileResponse(FRONTEND / "script.js")

@app.post("/session")
def create_session():
    session_id = str(uuid.uuid4())
    session_dir = TMP_ROOT / session_id
    session_dir.mkdir(parents=True)
    set_current_session(session_id)
    return {"session_id": session_id}

@app.post("/upload/audio/{session_id}")
def upload_audio(session_id: str, file: UploadFile = File(...)):
    session_dir = TMP_ROOT / session_id

    if not session_dir.exists():
        raise HTTPException(404, "session not found")

    destination = session_dir / "audio.mp3"

    with destination.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    duration = get_duration(destination)

    data = load_session(session_dir)
    data["audio_duration"] = duration
    save_session(session_dir, data)

    return {"status": "saved", "filename": file.filename, "duration": duration}

@app.post("/upload/first/{session_id}")
def upload_first(session_id: str, file: UploadFile = File(...)):
    session_dir = TMP_ROOT / session_id

    if not session_dir.exists():
        raise HTTPException(404, "session not found")

    extension = Path(file.filename).suffix
    destination = session_dir / f"first{extension}"

    with destination.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    duration = get_duration(destination) if is_video(file.filename) else None

    data = load_session(session_dir)
    data["first"] = {"filename": file.filename, "kind": "video" if is_video(file.filename) else "image", "duration": duration}
    save_session(session_dir, data)

    return {"status": "saved", "filename": file.filename, "duration": duration}

@app.post("/upload/last/{session_id}")
def upload_last(session_id: str, file: UploadFile = File(...)):
    session_dir = TMP_ROOT / session_id

    if not session_dir.exists():
        raise HTTPException(404, "session not found")

    extension = Path(file.filename).suffix
    destination = session_dir / f"last{extension}"

    with destination.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    duration = get_duration(destination) if is_video(file.filename) else None

    data = load_session(session_dir)
    data["last"] = {"filename": file.filename, "kind": "video" if is_video(file.filename) else "image", "duration": duration}
    save_session(session_dir, data)

    return {"status": "saved", "filename": file.filename, "duration": duration}

@app.post("/upload/media/{session_id}")
def upload_media(session_id: str, file: UploadFile = File(...)):
    session_dir = TMP_ROOT / session_id

    if not session_dir.exists():
        raise HTTPException(404, "session not found")

    media_dir = session_dir / "media"
    media_dir.mkdir(exist_ok=True)

    destination = media_dir / file.filename

    with destination.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    duration = get_duration(destination) if is_video(file.filename) else None

    data = load_session(session_dir)
    data["media"].append({"filename": file.filename, "kind": "video" if is_video(file.filename) else "image", "duration": duration})
    save_session(session_dir, data)

    return {"status": "saved", "filename": file.filename, "duration": duration}

@app.post("/generate/{session_id}")
def generate_video(session_id: str):
    session_dir = TMP_ROOT / session_id
    set_current_session(session_id)

    if not session_dir.exists():
        raise HTTPException(404, "session not found")

    data = load_session(session_dir)

    if data.get("audio_duration") is None:
        raise HTTPException(400, "no audio uploaded yet")

    if "first" not in data or "last" not in data:
        raise HTTPException(400, "first and last images are required")

    try:
        timeline = compute_timeline(data["audio_duration"], data["media"])
    except ValueError as e:
        raise HTTPException(400, str(e))

    segments_dir = session_dir / "segments"
    segments_dir.mkdir(exist_ok=True)

    segment_paths = []

    first_extension = Path(data["first"]["filename"]).suffix
    first_path = session_dir / f"first{first_extension}"
    seg0 = segments_dir / "seg_000.mp4"

    build_image_segment(first_path, timeline["first"], seg0)
    segment_paths.append(seg0)

    for i, (item, duration) in enumerate(timeline["middle"]):
        media_path = session_dir / "media" / item["filename"]
        seg_path = segments_dir / f"seg_{i + 1:03d}.mp4"

        if item["kind"] == "video":
            build_video_segment(media_path, duration, seg_path)
        else:
            build_image_segment(media_path, duration, seg_path)

        segment_paths.append(seg_path)

    last_extension = Path(data["last"]["filename"]).suffix
    last_path = session_dir / f"last{last_extension}"
    seg_last = segments_dir / f"seg_{len(segment_paths):03d}.mp4"

    build_image_segment(last_path, timeline["last"], seg_last)
    segment_paths.append(seg_last)

    concat_out = session_dir / "concat.mp4"

    concat_segments(segment_paths, concat_out, segments_dir)

    final_out = session_dir / "output.mp4"

    mux_audio(concat_out, session_dir / "audio.mp3", final_out)

    preview_out = session_dir / "preview.webm"
    build_preview(final_out, preview_out)

    return {"status": "done"}

@app.get("/preview/{session_id}")
def preview(session_id: str):
    session_dir = TMP_ROOT / session_id
    preview_file = session_dir / "preview.webm"

    if not preview_file.exists():
        raise HTTPException(404, "preview not available")

    return FileResponse(preview_file, media_type="video/webm")

@app.get("/download/{session_id}")
def download(session_id: str):
    session_dir = TMP_ROOT / session_id
    output = session_dir / "output.mp4"

    if not output.exists():
        raise HTTPException(404, "video not generated yet")

    data = load_session(session_dir)
    first_name = data.get("first", {}).get("filename", "video")
    download_name = Path(first_name).stem + ".mp4"

    return FileResponse(output, filename=download_name, media_type="video/mp4")

@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    session_dir = TMP_ROOT / session_id

    if not session_dir.exists():
        return {"status": "already_deleted"}

    try:
        shutil.rmtree(session_dir)
        clear_current_session_if_matches(session_id)
        return {"status": "deleted"}

    except Exception as e:
        raise HTTPException(500, f"Failed to delete session: {e}")

@app.get("/current_session")
def current_session():
    return get_current_session()