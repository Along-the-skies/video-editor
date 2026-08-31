import subprocess
from pathlib import Path

WIDTH = 1280
HEIGHT = 720
SCALE_FILTER = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1"
def build_image_segment(image_path: Path, duration: float, out_path: Path):
    cmd = [
        "ffmpeg", "-loop", "1", "-i", str(image_path),
        "-t", str(duration),
        "-vf", SCALE_FILTER,
        "-r", "30", "-pix_fmt", "yuv420p",
        "-y", str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")


def build_video_segment(video_path: Path, duration: float, out_path: Path):
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-t", str(duration),
        "-vf", SCALE_FILTER,
        "-r", "30", "-pix_fmt", "yuv420p",
        "-an",
        "-y", str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    
def concat_segments(segment_paths: list[Path], out_path: Path, work_dir: Path):
    list_file = work_dir / "concat_list.txt"
    with list_file.open("w") as f:
        for seg in segment_paths:
            f.write(f"file '{seg.as_posix()}'\n")

    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", "-y", str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")


def mux_audio(video_path: Path, audio_path: Path, out_path: Path):
    cmd = [
        "ffmpeg", "-i", str(video_path), "-i", str(audio_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        "-y", str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")