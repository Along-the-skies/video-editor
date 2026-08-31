import json
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4",".mov",".avi",".mkv",".webm"}

def load_session(session_dir: Path) -> dict:
    session_file = session_dir / "session.json"
    if session_file.exists():
        return json.loads(session_file.read_text())
    return {"audio_duration": None, "media": []}

def save_session(session_dir: Path, data: dict):
    session_file = session_dir / "session.json"
    session_file.write_text(json.dumps(data, indent=2))

def is_video(filename:str) -> bool:
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS