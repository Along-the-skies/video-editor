import subprocess

subprocess.run(
    "uvicorn backend.server:app --host 127.0.0.1 --port 8000",shell=True
)

