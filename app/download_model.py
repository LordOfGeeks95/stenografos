"""Downloads the model of settings.txt into app/models (called by Install.bat)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))  # runs with python -I
from transcribe import ensure_model, load_settings  # noqa: E402

name = load_settings()["model"]
print(f"Model: {name}")
print("Folder:", ensure_model(name))
