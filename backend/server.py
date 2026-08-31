import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from backend.est import get_duration
from backend.helper import load_session, save_session, is_video
from backend.fitting import compute_timeline
from backend.segments import build_image_segment, build_video_segment, concat_segments, mux_audio

app = FastAPI()

TMP_ROOT = Path(__file__).resolve().parent.parent / "tmp"
TMP_ROOT.mkdir(exist_ok=True)


@app.get("/")
def home():
    return "Server is alive"


@app.post("/session")
def create_session():
    session_id = str(uuid.uuid4())
    session_dir = TMP_ROOT / session_id
    session_dir.mkdir(parents=True)
    return {"session_id": session_id}


@app.post("/upload/audio/{session_id}")
def upload_audio(session_id: str, file: UploadFile = File(...)):
    session_dir = TMP_ROOT / session_id
    if not session_dir.exists():
        raise HTTPException(404, "session not found")

    dest = session_dir / "audio.mp3"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    duration = get_duration(dest)

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
def generate(session_id: str):
    session_dir = TMP_ROOT / session_id
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
        seg_path = segments_dir / f"seg_{i+1:03d}.mp4"
        if item["kind"] == "video":
            build_video_segment(media_path, duration, seg_path)
        else:
            build_image_segment(media_path, duration, seg_path)
        segment_paths.append(seg_path)

    last_ext = Path(data["last"]["filename"]).suffix
    last_path = session_dir / f"last{last_ext}"
    seg_last = segments_dir / f"seg_{len(segment_paths):03d}.mp4"
    build_image_segment(last_path, timeline["last"], seg_last)
    segment_paths.append(seg_last)

    concat_out = session_dir / "concat.mp4"
    concat_segments(segment_paths, concat_out, segments_dir)

    final_out = session_dir / "output.mp4"
    mux_audio(concat_out, session_dir / "audio.mp3", final_out)

    return {"status": "done"}

@app.get("/download/{session_id}")
def download(session_id:str,background_tasks:BackgroundTasks):
    session_dir = TMP_ROOT/session_id
    output = session_dir / "output.mp4"
    if not output.exists():
        raise HTTPException(404,"video not generated yet")


    background_tasks.add_task(shutil.rmtree,session_dir,ignore_errors=True)

    return FileResponse(output,filename="video.mp4",media_type="video/mp4")

@app.delete("/session/{session_dir}")
def delete_session(session_id:str):
    session_dir = TMP_ROOT/session_id
    if not session_dir.exists():
        raise HTTPException(404,"session not found")

    shutil.rmtree(session_dir,ignore_errors=True)
    return {"status":"deleted"}