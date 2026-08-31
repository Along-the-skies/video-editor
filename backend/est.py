import subprocess
import json
from pathlib import Path

def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])