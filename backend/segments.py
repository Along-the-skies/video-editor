import subprocess
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = Path(__file__).resolve().parent.parent

FFMPEG_PATH = BASE_PATH / "backend" / "bin" / "ffmpeg.exe"

WIDTH = 1280
HEIGHT = 720

SCALE_FILTER = (
    f"scale={WIDTH}:{HEIGHT}:"
    "force_original_aspect_ratio=decrease,"
    f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
    "setsar=1"
)

def run_ffmpeg(cmd):
    print("FFMPEG PATH:", FFMPEG_PATH)
    print("FFMPEG EXISTS:", FFMPEG_PATH.exists())
    print("COMMAND:", cmd)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

def build_image_segment(image_path: Path, duration: float, out_path: Path):
    cmd = [
        str(FFMPEG_PATH),
        "-loop", "1",
        "-i", str(image_path),
        "-t", str(duration),
        "-vf", SCALE_FILTER,
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-y", str(out_path)
    ]
    run_ffmpeg(cmd)

def build_video_segment(video_path: Path, duration: float, out_path: Path):
    cmd = [
        str(FFMPEG_PATH),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", SCALE_FILTER,
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-an",
        "-y", str(out_path)
    ]
    run_ffmpeg(cmd)

def concat_segments(segment_paths: list[Path], out_path: Path, work_dir: Path):
    list_file = work_dir / "concat_list.txt"

    with list_file.open("w", encoding="utf-8") as f:
        for seg in segment_paths:
            f.write(f"file '{seg.as_posix()}'\n")

    cmd = [
        str(FFMPEG_PATH),
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        "-y", str(out_path)
    ]
    run_ffmpeg(cmd)

def build_preview(final_video_path: Path, out_path: Path):
    cmd = [
        str(FFMPEG_PATH),
        "-i", str(final_video_path),
        "-c:v", "libvpx-vp9",
        "-b:v", "1M",
        "-deadline", "realtime",
        "-cpu-used", "5",
        "-c:a", "libopus",
        "-y", str(out_path)
    ]
    run_ffmpeg(cmd)

def mux_audio(video_path: Path, audio_path: Path, out_path: Path):
    cmd = [
        str(FFMPEG_PATH),
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "-y", str(out_path)
    ]
    run_ffmpeg(cmd)