import subprocess

subprocess.run(
    "uvicorn backend.server:app --reload"
)

