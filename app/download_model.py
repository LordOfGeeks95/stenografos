"""Κατεβάζει το μοντέλο του settings.txt στο app/models (καλείται από το Install.bat)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))  # τρέχει με python -I
from transcribe import ensure_model, load_settings  # noqa: E402

name = load_settings()["model"]
print(f"Μοντέλο: {name}")
print("Φάκελος:", ensure_model(name))
