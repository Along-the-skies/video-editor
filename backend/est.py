import subprocess
import json
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = Path(__file__).resolve().parent


FFPROBE_PATH = BASE_PATH / "backend" / "bin" / "ffprobe.exe"


def get_duration(path: Path) -> float:
    result = subprocess.run(
        [
            str(FFPROBE_PATH),
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path)
        ],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])