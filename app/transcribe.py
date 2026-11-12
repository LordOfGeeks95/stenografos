"""Stenografos (By Nikitas Katsaitis)

Speech to text on your own computer, offline, with the Whisper model (faster-whisper).
Works in ~100 languages and is tuned to be really good in Greek.

Usage: drag recordings onto «Stenografos (By Nikitas Katsaitis).bat», or double-click it
to choose files. The transcripts go to the Transcripts folder.

Απομαγνητοφώνηση στον υπολογιστή σου, χωρίς ίντερνετ. Τα μηνύματα βγαίνουν στα ελληνικά
όταν τα Windows είναι στα ελληνικά (ρύθμιση ui_language στο settings.txt).
"""
import ctypes
import os
import re
import subprocess
import sys
import time
from pathlib import Path

APP_NAME = "Stenografos"
TITLE = f"{APP_NAME} (By Nikitas Katsaitis)"
APP = Path(__file__).resolve().parent
ROOT = APP.parent
SITE = APP / ".venv" / "Lib" / "site-packages" / "nvidia"
# Whatever huggingface writes (cache, token) also stays inside the folder.
os.environ["HF_HOME"] = str(APP / ".hf")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# The CUDA libraries (cuBLAS, cuDNN) are installed as pip packages only when an NVIDIA card exists.
for sub in ("cublas", "cudnn", "cuda_nvrtc"):
    dll_dir = SITE / sub / "bin"
    if dll_dir.is_dir():
        os.add_dll_directory(str(dll_dir))
        os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ["PATH"]

import av  # noqa: E402

# av >= 15 removed the metadata_errors argument that faster-whisper passes.
_av_open = av.open


def _av_open_compat(*args, metadata_errors=None, **kwargs):
    return _av_open(*args, **kwargs)


av.open = _av_open_compat

from faster_whisper import WhisperModel  # noqa: E402

AUDIO_EXT = {".m4a", ".mp3", ".wav", ".ogg", ".opus", ".flac", ".aac", ".wma", ".mp4", ".mkv", ".webm", ".mov", ".amr", ".3gp"}
# Whisper keeps only ~220 tokens of the prompt, so the vocabulary list is cut here.
PROMPT_MAX_CHARS = 450
# Phrases Whisper "imagines" in noise or silence.
HALLUCINATIONS = ("υπότιτλοι", "υποτιτλισμός", "subtitles", "authorwave", "ευχαριστώ που παρακολουθήσατε",
                  "thanks for watching", "thank you for watching", "please subscribe")
# Dropped only when they are the whole segment (in pauses Whisper often writes just «Ευχαριστώ.»).
HALLUCINATIONS_EXACT = ("ευχαριστώ", "ευχαριστώ πολύ", "ευχαριστούμε")
GREEK_PROMPT = "Ηχογράφηση στα ελληνικά."

DEFAULTS = {
    "ui_language": "auto",
    "model": "large-v3",
    "language": "auto",
    "output_folder": "",
    "device": "auto",
    "cpu_threads": "auto",
    "prompt": "",
    "open_folder_when_done": "yes",
    "notification": "yes",
}

MONTHS = {m: i for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
# «Oct 12, 14.10» (how many phones save them) or «2026-10-12 14.10» or «20261012_141000».
PHONE_WHEN = re.compile(r"\b([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{1,2})[.:-](\d{2})")
ISO_WHEN = re.compile(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})(?:[\s_T-]+(\d{2})[.:-]?(\d{2}))?")


# ---------------------------------------------------------------- messages (English / Ελληνικά)

TEXT = {
    "en": {
        "not_found": "  ⚠ Not found: {a}",
        "pick_title": "Choose recordings to transcribe",
        "pick_audio": "Audio / video",
        "pick_all": "All files",
        "part": "{i} of {n}",
        "model_missing": "Model «{name}» not found: downloading it (only once, ~3 GB for large-v3)...",
        "loading": "Loading model «{name}»...",
        "dev_gpu": "graphics card (GPU)",
        "dev_cpu": "processor (CPU, slower) · {n} threads",
        "running_on": "  ✓ Running on: {label}",
        "retry": "  ⚠ Did not work ({err}). Trying the next option...",
        "load_fail": "Could not load the model. Run Install.bat again.",
        "file_label": "File {i} of {n}",
        "left": "~{t} left",
        "done_one": "  100%  ·  done in {t} (audio {a}, speed x{s:.1f})          ",
        "no_files": "\nNo files chosen.",
        "drag_hint": "Drag one or more recordings onto «{bat}».",
        "summary": "\nFiles: {f}  ·  recordings: {g}",
        "lang_line": "Language: {lang}",
        "lang_auto": "automatic detection",
        "out_line": "\nTranscripts will be saved in:\n  {d}",
        "continue": "\nContinue? (Enter = yes, N = no): ",
        "no_words": ("n", "no"),
        "cancelled": "Cancelled.",
        "interrupted": "\n\nStopped by you. Everything written so far is saved.",
        "error": "\n\n✖ Error: {e}",
        "err_title": "{app}: error",
        "err_text": "Stopped at file {i}. See the window.",
        "end": "DONE: {n} file(s), audio {a}, total time {t}",
        "end_where": "Transcripts are in: {d}",
        "ok_title": "{app}: done!",
        "ok_text": "{n} file(s), audio {a}, in {t}.",
        "vocab": "Terms:",
    },
    "el": {
        "not_found": "  ⚠ Δεν βρέθηκε: {a}",
        "pick_title": "Διάλεξε ηχογραφήσεις για απομαγνητοφώνηση",
        "pick_audio": "Ήχος / βίντεο",
        "pick_all": "Όλα τα αρχεία",
        "part": "{i} από {n}",
        "model_missing": "Το μοντέλο «{name}» δεν βρέθηκε: κατέβασμα (μία φορά μόνο, ~3 GB για το large-v3)...",
        "loading": "Φόρτωση μοντέλου «{name}»...",
        "dev_gpu": "κάρτα γραφικών (GPU)",
        "dev_cpu": "επεξεργαστής (CPU, πιο αργά) · {n} threads",
        "running_on": "  ✓ Δουλεύει με: {label}",
        "retry": "  ⚠ Δεν έγινε ({err}). Δοκιμάζω την επόμενη επιλογή...",
        "load_fail": "Δεν μπόρεσα να φορτώσω το μοντέλο. Τρέξε ξανά το Install.bat.",
        "file_label": "Αρχείο {i} από {n}",
        "left": "απομένουν ~{t}",
        "done_one": "  100%  ·  έτοιμο σε {t} (ήχος {a}, ταχύτητα x{s:.1f})          ",
        "no_files": "\nΔεν διάλεξες αρχεία.",
        "drag_hint": "Σύρε μία ή περισσότερες ηχογραφήσεις πάνω στο «{bat}».",
        "summary": "\nΑρχεία: {f}  ·  ηχογραφήσεις: {g}",
        "lang_line": "Γλώσσα: {lang}",
        "lang_auto": "αυτόματη αναγνώριση",
        "out_line": "\nΤα κείμενα θα μπουν στον φάκελο:\n  {d}",
        "continue": "\nΣυνέχεια; (Enter = ναι, Ο = όχι): ",
        "no_words": ("o", "ο", "όχι", "οχι", "n", "no"),
        "cancelled": "Ακυρώθηκε.",
        "interrupted": "\n\nΔιακόπηκε από εσένα. Ό,τι γράφτηκε ως εδώ έχει σωθεί.",
        "error": "\n\n✖ Σφάλμα: {e}",
        "err_title": "{app}: σφάλμα",
        "err_text": "Σταμάτησε στο αρχείο {i}. Δες το παράθυρο.",
        "end": "ΤΕΛΟΣ: {n} αρχείο(α), ήχος {a}, συνολικός χρόνος {t}",
        "end_where": "Τα κείμενα είναι στο: {d}",
        "ok_title": "{app}: έτοιμο!",
        "ok_text": "{n} αρχείο(α), ήχος {a}, σε {t}.",
        "vocab": "Όροι:",
    },
}
UI = "en"


def T(key: str, **kw):
    value = TEXT[UI][key]
    return value.format(**kw) if kw and isinstance(value, str) else value


def windows_is_greek() -> bool:
    """True when the Windows display language OR the regional format is Greek (language id 0x08).

    Many Greeks use English Windows with Greek regional settings, so both count.
    """
    try:
        k = ctypes.windll.kernel32
        return 0x08 in ((k.GetUserDefaultUILanguage() & 0x3FF), (k.GetUserDefaultLCID() & 0x3FF))
    except Exception:
        return False


# ---------------------------------------------------------------- settings

def load_settings() -> dict:
    """Reads app/settings.txt («key = value» lines, # = comment) and resolves the «auto» values."""
    global UI
    settings = dict(DEFAULTS)
    path = APP / "settings.txt"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in settings and value:
                settings[key] = value
    greek = windows_is_greek()
    ui = settings["ui_language"].lower()
    UI = ui if ui in TEXT else ("el" if greek else "en")
    lang = settings["language"].lower()
    if lang == "auto":
        lang = "el" if greek else ""   # Greek Windows → Greek (more accurate), otherwise automatic detection
    elif lang == "detect":
        lang = ""
    settings["language"] = lang
    return settings


def output_dir(settings: dict) -> Path:
    folder = settings["output_folder"].strip().strip('"')
    out = Path(folder) if folder else ROOT / "Transcripts"
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_prompt(settings: dict) -> str:
    """Prompt + the terms of app/vocabulary.txt (most important first).

    The Greek default sentence is used only when the language is Greek: for other languages
    a Greek prompt would push the model towards Greek.
    """
    prompt = settings["prompt"].strip()
    if not prompt and settings["language"] == "el":
        prompt = GREEK_PROMPT
    vocab = APP / "vocabulary.txt"
    terms = []
    if vocab.is_file():
        terms = [line.strip() for line in vocab.read_text(encoding="utf-8-sig").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
    if not terms:
        return prompt
    label = TEXT["el" if settings["language"] == "el" else "en"]["vocab"]
    prompt = f"{prompt} {label}".strip()
    for term in terms:
        if len(prompt) + len(term) + 2 > PROMPT_MAX_CHARS:
            break
        prompt += f" {term},"
    return prompt.rstrip(",") + "."


def physical_cores() -> int:
    """Number of real cores. Hyper-threading «twins» don't help Whisper (measured: 4 and 8
    threads on a 4-core/8-thread i7-6700 give exactly the same speed)."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum"],
            capture_output=True, text=True, timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()
        if out.isdigit() and int(out) > 0:
            return int(out)
    except Exception:
        pass
    return max((os.cpu_count() or 8) // 2, 4)


def cpu_threads(settings: dict) -> int:
    """faster-whisper uses only 4 threads by default: «auto» = all the real cores (at least 4)."""
    value = settings["cpu_threads"].strip().lower()
    if value.isdigit() and int(value) > 0:
        return int(value)
    return max(physical_cores(), 4)


# ---------------------------------------------------------------- files and groups

def when_key(f: Path) -> tuple:
    """Sort key from the date/time in the name. Without a date, sort by name."""
    m = PHONE_WHEN.search(f.stem)
    if m and m.group(1).lower()[:3] in MONTHS:
        return (0, 0, MONTHS[m.group(1).lower()[:3]], int(m.group(2)), int(m.group(3)), int(m.group(4)), f.name)
    m = ISO_WHEN.search(f.stem)
    if m and 1 <= int(m.group(2)) <= 12:
        return (0, int(m.group(1)), int(m.group(2)), int(m.group(3)),
                int(m.group(4) or 0), int(m.group(5) or 0), f.name)
    return (1, 0, 0, 0, 0, 0, f.name.lower())


def group_key(f: Path) -> str:
    """Parts of the same recording have the same name once you remove the time.

    e.g. «Notes Oct 12, 14.10» and «Notes Oct 12, 15.12» → same group.
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
            return f.stem.lower()  # no time in the name: each file on its own
    return re.sub(r"[\s​]+", " ", stem).strip().lower()


def make_jobs(files: list[Path]) -> tuple[list[tuple[Path, str]], int]:
    """List of (file, output name). Parts of a group get «(1 of N)» in time order."""
    groups: dict[str, list[Path]] = {}
    for f in sorted(files, key=when_key):
        groups.setdefault(group_key(f), []).append(f)
    jobs = []
    for parts in groups.values():
        for i, f in enumerate(parts, 1):
            jobs.append((f, f"{f.stem} ({T('part', i=i, n=len(parts))})" if len(parts) > 1 else f.stem))
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
            print(T("not_found", a=a))
    return files


def pick_files() -> list[Path]:
    """No files given (double-click): file chooser window."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return []
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    names = filedialog.askopenfilenames(
        title=T("pick_title"),
        filetypes=[(T("pick_audio"), " ".join(f"*{e}" for e in sorted(AUDIO_EXT))), (T("pick_all"), "*.*")],
    )
    root.destroy()
    return [Path(n) for n in names]


# ---------------------------------------------------------------- helpers

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
    """Returns the model folder. If missing, downloads it (only once, needs internet)."""
    from faster_whisper.utils import download_model
    root = str(APP / "models")
    try:
        return download_model(name, cache_dir=root, local_files_only=True)
    except Exception:
        print(T("model_missing", name=name))
        return download_model(name, cache_dir=root)


def load_model(settings: dict):
    path = ensure_model(settings["model"])
    device = settings["device"].lower()
    tries = []
    if device in ("auto", "cuda", "gpu") and has_nvidia():
        # int8_float16 = faster on newer cards · int8 = works on older ones too (e.g. GTX 10xx)
        tries += [("cuda", "int8_float16"), ("cuda", "int8")]
    if device not in ("cuda", "gpu"):
        tries.append(("cpu", "int8"))
    threads = cpu_threads(settings) if "cpu" in [d for d, _ in tries] else 0
    print(T("loading", name=settings["model"]))
    for dev, ctype in tries:
        try:
            model = WhisperModel(path, device=dev, compute_type=ctype, cpu_threads=threads)
            label = T("dev_gpu") if dev == "cuda" else T("dev_cpu", n=threads)
            print(T("running_on", label=label))
            return model, dev
        except Exception as e:
            if ctype == "int8_float16":
                continue  # older card (e.g. GTX 10xx): just go to normal int8
            print(T("retry", err=str(e).splitlines()[0][:120]))
    raise SystemExit(T("load_fail"))


def notify(title: str, text: str, ok: bool = True) -> None:
    """Sound + Windows notification (balloon in the corner)."""
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


def yes(value: str) -> bool:
    return value.strip().lower().startswith(("y", "ν", "1", "t"))


# ---------------------------------------------------------------- main program

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
    # Written as we go, so nothing is lost if a long recording is interrupted.
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
            print(f"\r  {seg.end / total:5.1%}  ·  {fmt(seg.end)} / {fmt(total)}  ·  {T('left', t=fmt(left))}   ",
                  end="", flush=True)
        if paragraph:
            txt.write(" ".join(paragraph) + "\n")
    elapsed = time.time() - start
    print("\r" + T("done_one", t=fmt(elapsed), a=fmt(total), s=total / max(elapsed, 1)))
    print(f"  → {txt_path.name}")
    return total


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    settings = load_settings()
    os.system(f"title {TITLE}")
    print("=" * 60)
    print(f"   {TITLE}")
    print("=" * 60)

    files = collect(sys.argv[1:]) if len(sys.argv) > 1 else pick_files()
    if not files:
        print(T("no_files"))
        print(T("drag_hint", bat=f"{TITLE}.bat"))
        return

    jobs, n_groups = make_jobs(files)
    out_dir = output_dir(settings)
    print(T("summary", f=len(jobs), g=n_groups))
    for audio, stem in jobs:
        print(f"  • {stem}")
    print(T("lang_line", lang=settings["language"] or T("lang_auto")))
    print(T("out_line", d=out_dir))
    if len(jobs) > 1:
        answer = input(T("continue")).strip().lower()
        if answer in T("no_words"):
            print(T("cancelled"))
            return

    run_start = time.time()
    done_audio = 0.0
    finished = 0
    try:
        model, device = load_model(settings)
        prompt = build_prompt(settings)
        for index, (audio, stem) in enumerate(jobs, 1):
            label = T("file_label", i=index, n=len(jobs))
            done_audio += transcribe_one(model, audio, stem, out_dir, settings, prompt, label)
            finished += 1
    except KeyboardInterrupt:
        print(T("interrupted"))
        return
    except Exception as e:
        print(T("error", e=e))
        if yes(settings["notification"]):
            notify(T("err_title", app=APP_NAME), T("err_text", i=finished + 1), ok=False)
        return

    run_elapsed = time.time() - run_start
    print("\n" + "=" * 60)
    print(T("end", n=finished, a=fmt(done_audio), t=fmt(run_elapsed)))
    print(T("end_where", d=out_dir))
    print("=" * 60)
    if yes(settings["notification"]):
        notify(T("ok_title", app=APP_NAME), T("ok_text", n=finished, a=fmt(done_audio), t=fmt(run_elapsed)))
    if yes(settings["open_folder_when_done"]):
        os.startfile(out_dir)


if __name__ == "__main__":
    main()
