import subprocess
from frontend.ui import initialize_ui
subprocess.Popen("uvicorn backend.server:app --host 127.0.0.1 --port 8000",shell=True)
initialize_ui()