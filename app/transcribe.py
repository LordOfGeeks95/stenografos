"""Greek Speech To Text (By Nikitas Katsaitis)

Απομαγνητοφώνηση ελληνικών ηχογραφήσεων (φωνητικές σημειώσεις, συναντήσεις, συνεντεύξεις κ.λπ.)
τοπικά στον υπολογιστή σου, με το μοντέλο Whisper (faster-whisper).

Χρήση: σύρε ηχογραφήσεις πάνω στο «Greek Speech To Text (By Nikitas Katsaitis).bat»
ή κάνε διπλό κλικ σε αυτό για να διαλέξεις αρχεία. Τα κείμενα πάνε στον φάκελο Transcripts.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
SITE = APP / ".venv" / "Lib" / "site-packages" / "nvidia"
# Ό,τι γράφει το huggingface (cache, token) μένει κι αυτό μέσα στον φάκελο, όχι στον χρήστη των Windows.
os.environ["HF_HOME"] = str(APP / ".hf")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Οι βιβλιοθήκες CUDA (cuBLAS, cuDNN) εγκαθίστανται ως πακέτα pip μόνο όταν υπάρχει κάρτα NVIDIA.
for sub in ("cublas", "cudnn", "cuda_nvrtc"):
    dll_dir = SITE / sub / "bin"
    if dll_dir.is_dir():
        os.add_dll_directory(str(dll_dir))
        os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ["PATH"]

import av  # noqa: E402

# Το av >= 15 αφαίρεσε την παράμετρο metadata_errors που περνάει το faster-whisper.
_av_open = av.open


def _av_open_compat(*args, metadata_errors=None, **kwargs):
    return _av_open(*args, **kwargs)


av.open = _av_open_compat

from faster_whisper import WhisperModel  # noqa: E402

AUDIO_EXT = {".m4a", ".mp3", ".wav", ".ogg", ".opus", ".flac", ".aac", ".wma", ".mp4", ".mkv", ".webm", ".mov", ".amr", ".3gp"}
# Το Whisper κρατάει μόνο ~220 tokens από το prompt, οπότε κόβουμε τη λίστα όρων εδώ.
PROMPT_MAX_CHARS = 450
# Φράσεις που «φαντάζεται» το Whisper σε σημεία με θόρυβο ή σιωπή.
HALLUCINATIONS = ("υπότιτλοι", "υποτιτλισμός", "subtitles", "authorwave", "ευχαριστώ που παρακολουθήσατε")
# Φράσεις που πετάμε μόνο όταν είναι ολόκληρο το κομμάτι (σε παύσεις βγαίνει σκέτο «Ευχαριστώ.»).
HALLUCINATIONS_EXACT = ("ευχαριστώ", "ευχαριστώ πολύ", "ευχαριστούμε")

DEFAULTS = {
    "model": "large-v3",
    "language": "el",
    "output_folder": "",
    "device": "auto",
    "prompt": "Ηχογράφηση στα ελληνικά.",
    "open_folder_when_done": "yes",
    "notification": "yes",
}

MONTHS = {m: i for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
# «Oct 12, 14.10» (όπως τα σώζουν πολλά κινητά) ή «2026-10-12 14.10» ή «20261012_141000».
PHONE_WHEN = re.compile(r"\b([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{1,2})[.:-](\d{2})")
ISO_WHEN = re.compile(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})(?:[\s_T-]+(\d{2})[.:-]?(\d{2}))?")


# ---------------------------------------------------------------- ρυθμίσεις

def load_settings() -> dict:
    """Διαβάζει το app/settings.txt (γραμμές «κλειδί = τιμή», # = σχόλιο)."""
    settings = dict(DEFAULTS)
    path = APP / "settings.txt"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in settings:
                settings[key] = value
    return settings


def output_dir(settings: dict) -> Path:
    folder = settings["output_folder"].strip().strip('"')
    out = Path(folder) if folder else ROOT / "Transcripts"
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_prompt(settings: dict) -> str:
    """Prompt με τους όρους του app/vocabulary.txt (οι πιο σημαντικοί πρώτοι)."""
    prompt = settings["prompt"].strip()
    vocab = APP / "vocabulary.txt"
    if not vocab.is_file():
        return prompt
    terms = [line.strip() for line in vocab.read_text(encoding="utf-8-sig").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not terms:
        return prompt
    prompt += " Όροι:"
    for term in terms:
        if len(prompt) + len(term) + 2 > PROMPT_MAX_CHARS:
            break
        prompt += f" {term},"
    return prompt.rstrip(",") + "."


# ---------------------------------------------------------------- αρχεία και ομάδες

def when_key(f: Path) -> tuple:
    """Κλειδί χρονικής ταξινόμησης από το όνομα. Αν δεν βρεθεί ημερομηνία, ταξινόμηση με το όνομα."""
    m = PHONE_WHEN.search(f.stem)
    if m and m.group(1).lower()[:3] in MONTHS:
        return (0, 0, MONTHS[m.group(1).lower()[:3]], int(m.group(2)), int(m.group(3)), int(m.group(4)), f.name)
    m = ISO_WHEN.search(f.stem)
    if m and 1 <= int(m.group(2)) <= 12:
        return (0, int(m.group(1)), int(m.group(2)), int(m.group(3)),
                int(m.group(4) or 0), int(m.group(5) or 0), f.name)
    return (1, 0, 0, 0, 0, 0, f.name.lower())


def group_key(f: Path) -> str:
    """Τα κομμάτια της ίδιας ηχογράφησης έχουν ίδιο όνομα αν βγάλεις την ώρα.

    π.χ. «Σημειώσεις Oct 12, 14.10» και «Σημειώσεις Oct 12, 15.12» → ίδια ομάδα.
    """
    stem = f.stem
    m = PHONE_WHEN.search(stem)
    if m and m.group(1).lower()[:3] in MONTHS:
        stem = stem[:m.start(3)] + stem[m.end(4):]
    else:
        m = ISO_WHEN.search(stem)
        if m and m.group(4):
            stem = stem[:m.start(4)] + stem[m.end(5):]
        else:
            return f.stem.lower()  # χωρίς ώρα στο όνομα: κάθε αρχείο μόνο του
    return re.sub(r"[\s​]+", " ", stem).strip().lower()


def make_jobs(files: list[Path]) -> tuple[list[tuple[Path, str]], int]:
    """Λίστα (αρχείο, όνομα εξόδου). Τα κομμάτια μιας ομάδας παίρνουν «(1 από N)» με χρονική σειρά."""
    groups: dict[str, list[Path]] = {}
    for f in sorted(files, key=when_key):
        groups.setdefault(group_key(f), []).append(f)
    jobs = []
    for parts in groups.values():
        for i, f in enumerate(parts, 1):
            jobs.append((f, f"{f.stem} ({i} από {len(parts)})" if len(parts) > 1 else f.stem))
    return jobs, len(groups)


def collect(args: list[str]) -> list[Path]:
    files = []
    for a in args:
        p = Path(a.strip('"'))
        if p.is_dir():
            files += [f for f in p.iterdir() if f.suffix.lower() in AUDIO_EXT]
        elif p.is_file():
            files.append(p)
        else:
            print(f"  ⚠ Δεν βρέθηκε: {a}")
    return files


def pick_files() -> list[Path]:
    """Χωρίς αρχεία (διπλό κλικ): παράθυρο επιλογής."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return []
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    names = filedialog.askopenfilenames(
        title="Διάλεξε ηχογραφήσεις για απομαγνητοφώνηση",
        filetypes=[("Ήχος / βίντεο", " ".join(f"*{e}" for e in sorted(AUDIO_EXT))), ("Όλα τα αρχεία", "*.*")],
    )
    root.destroy()
    return [Path(n) for n in names]


# ---------------------------------------------------------------- βοηθητικά

def fmt(seconds: float) -> str:
    s = int(max(seconds, 0))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def has_nvidia() -> bool:
    try:
        subprocess.run(["nvidia-smi"], capture_output=True, check=True, timeout=15,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except Exception:
        return False


def ensure_model(name: str) -> str:
    """Επιστρέφει τον φάκελο του μοντέλου. Αν λείπει, το κατεβάζει (μία φορά μόνο, θέλει ίντερνετ)."""
    from faster_whisper.utils import download_model
    root = str(APP / "models")
    try:
        return download_model(name, cache_dir=root, local_files_only=True)
    except Exception:
        print(f"Το μοντέλο «{name}» δεν βρέθηκε: κατέβασμα (μία φορά μόνο, ~3 GB για το large-v3)...")
        return download_model(name, cache_dir=root)


def load_model(settings: dict):
    path = ensure_model(settings["model"])
    device = settings["device"].lower()
    tries = []
    if device in ("auto", "cuda", "gpu") and has_nvidia():
        # int8_float16 = πιο γρήγορο σε νέες κάρτες · int8 = δουλεύει και σε παλιές (π.χ. GTX 10xx)
        tries += [("cuda", "int8_float16"), ("cuda", "int8")]
    if device not in ("cuda", "gpu"):
        tries.append(("cpu", "int8"))
    print(f"Φόρτωση μοντέλου «{settings['model']}»...")
    for dev, ctype in tries:
        try:
            model = WhisperModel(path, device=dev, compute_type=ctype)
            label = "κάρτα γραφικών (GPU)" if dev == "cuda" else "επεξεργαστής (CPU, πιο αργά)"
            print(f"  ✓ Δουλεύει με: {label}")
            return model, dev
        except Exception as e:
            if ctype == "int8_float16":
                continue  # παλιότερη κάρτα (π.χ. GTX 10xx): απλώς πάμε στην κανονική λειτουργία int8
            print(f"  ⚠ Δεν έγινε ({str(e).splitlines()[0][:120]}). Δοκιμάζω την επόμενη επιλογή...")
    raise SystemExit("Δεν μπόρεσα να φορτώσω το μοντέλο. Τρέξε ξανά το Install.bat.")


def notify(title: str, text: str, ok: bool = True) -> None:
    """Ήχος + ειδοποίηση των Windows (μπαλονάκι στη γωνία)."""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK if ok else winsound.MB_ICONHAND)
    except Exception:
        pass
    title = title.replace("'", "''")
    text = text.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing;"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        f"$n.BalloonTipTitle = '{title}'; $n.BalloonTipText = '{text}';"
        "$n.Visible = $true; $n.ShowBalloonTip(10000); Start-Sleep -Seconds 10; $n.Dispose()"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        pass


def keep(text: str) -> bool:
    low = text.lower()
    if not text or any(h in low for h in HALLUCINATIONS):
        return False
    return low.strip(" .!,;") not in HALLUCINATIONS_EXACT


# ---------------------------------------------------------------- κύριο πρόγραμμα

def transcribe_one(model, audio: Path, stem: str, out_dir: Path, settings: dict, prompt: str,
                   label: str) -> float:
    print(f"\n=== {label}: {audio.name} ===")
    start = time.time()
    segments, info = model.transcribe(
        str(audio), language=settings["language"] or None, beam_size=5, vad_filter=True,
        initial_prompt=prompt or None, condition_on_previous_text=False,
    )
    total = info.duration or 1
    txt_path = out_dir / f"{stem}.txt"
    ts_path = out_dir / f"{stem} (timestamps).txt"
    paragraph: list[str] = []
    # Γράφουμε σταδιακά, ώστε να μη χαθεί τίποτα αν διακοπεί μια μεγάλη ηχογράφηση.
    with open(txt_path, "w", encoding="utf-8") as txt, open(ts_path, "w", encoding="utf-8") as ts:
        for seg in segments:
            text = seg.text.strip()
            if not keep(text):
                continue
            ts.write(f"[{fmt(seg.start)}] {text}\n")
            paragraph.append(text)
            if len(paragraph) >= 8:
                txt.write(" ".join(paragraph) + "\n\n")
                paragraph.clear()
                txt.flush()
                ts.flush()
            elapsed = time.time() - start
            speed = seg.end / elapsed if elapsed > 0 else 0
            left = (total - seg.end) / speed if speed > 0 else 0
            print(f"\r  {seg.end / total:5.1%}  ·  {fmt(seg.end)} / {fmt(total)}  ·  απομένουν ~{fmt(left)}   ",
                  end="", flush=True)
        if paragraph:
            txt.write(" ".join(paragraph) + "\n")
    elapsed = time.time() - start
    print(f"\r  100%  ·  έτοιμο σε {fmt(elapsed)} (ήχος {fmt(total)}, ταχύτητα x{total / max(elapsed, 1):.1f})          ")
    print(f"  → {txt_path.name}")
    return total


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    os.system("title Greek Speech To Text (By Nikitas Katsaitis)")
    print("=" * 60)
    print("   Greek Speech To Text (By Nikitas Katsaitis)")
    print("=" * 60)

    settings = load_settings()
    files = collect(sys.argv[1:]) if len(sys.argv) > 1 else pick_files()
    if not files:
        print("\nΔεν διάλεξες αρχεία.")
        print("Σύρε μία ή περισσότερες ηχογραφήσεις πάνω στο «Greek Speech To Text (By Nikitas Katsaitis).bat».")
        return

    jobs, n_groups = make_jobs(files)
    out_dir = output_dir(settings)
    print(f"\nΑρχεία: {len(jobs)}  ·  ηχογραφήσεις: {n_groups}")
    for audio, stem in jobs:
        print(f"  • {stem}")
    print(f"\nΤα κείμενα θα μπουν στον φάκελο:\n  {out_dir}")
    if len(jobs) > 1:
        answer = input("\nΣυνέχεια; (Enter = ναι, Ο = όχι): ").strip().lower()
        if answer in ("o", "ο", "όχι", "οχι", "n", "no"):
            print("Ακυρώθηκε.")
            return

    run_start = time.time()
    done_audio = 0.0
    finished = 0
    try:
        model, device = load_model(settings)
        prompt = build_prompt(settings)
        for index, (audio, stem) in enumerate(jobs, 1):
            label = f"Αρχείο {index} από {len(jobs)}"
            done_audio += transcribe_one(model, audio, stem, out_dir, settings, prompt, label)
            finished += 1
    except KeyboardInterrupt:
        print("\n\nΔιακόπηκε από εσένα. Ό,τι γράφτηκε ως εδώ έχει σωθεί.")
        return
    except Exception as e:
        print(f"\n\n✖ Σφάλμα: {e}")
        if settings["notification"].lower().startswith(("y", "ν")):
            notify("Greek Speech To Text: σφάλμα", f"Σταμάτησε στο αρχείο {finished + 1}. Δες το παράθυρο.", ok=False)
        return

    run_elapsed = time.time() - run_start
    print("\n" + "=" * 60)
    print(f"ΤΕΛΟΣ: {finished} αρχείο(α), ήχος {fmt(done_audio)}, συνολικός χρόνος {fmt(run_elapsed)}")
    print(f"Τα κείμενα είναι στο: {out_dir}")
    print("=" * 60)
    if settings["notification"].lower().startswith(("y", "ν")):
        notify("Greek Speech To Text: έτοιμο!", f"{finished} αρχείο(α), ήχος {fmt(done_audio)}, σε {fmt(run_elapsed)}.")
    if settings["open_folder_when_done"].lower().startswith(("y", "ν")):
        os.startfile(out_dir)


if __name__ == "__main__":
    main()
