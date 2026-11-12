**🇬🇧 English** | [🇬🇷 Ελληνικά](README.el.md)

# Stenografos (By Nikitas Katsaitis)

**Turns your recordings into text, locally on your own computer.**
Free, no account, no limits, and your files never leave your PC.

*Stenografos* (Στενογράφος) is Greek for **stenographer**: the person who records speech word for word, as fast as it is spoken.

---

## 🎙️ What it does and how it works

You record something (voice notes, a meeting, an interview, a lecture, a podcast…), drag the file onto the program and get back **text**.

- It uses **Whisper large-v3**, OpenAI's speech recognition model, through [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
- **Everything runs on your computer**: no audio is sent to any server. After installation it works **without internet**.
- **What the installer downloads** (once, only inside the program's folder):
    - its own **Python 3.12** (you don't need Python, and if you have it, it is not touched),
    - the **libraries** it needs (plus the CUDA libraries, only if you have an NVIDIA card),
    - the **speech model** (~3 GB).
- **What you get:** for each recording **two** text files, a clean one in paragraphs and one with the time of every phrase `[00:12:34]`.
- **Long recordings in parts:** if a recording is split into several files with the time in the name (as phones save them), it puts them in **time order** by itself and numbers them «(1 of 3)», «(2 of 3)»…
- At the end: **sound + Windows notification**, and the folder with the transcripts opens.
- The program speaks **English**, or **Greek** if Windows is in Greek.

---

## 🌍 Languages

Whisper understands **~100 languages** and detects the language by itself.

- **Excellent** in widely spoken languages such as **English, Spanish, German, French, Italian, Portuguese, Dutch, Polish, Japanese** and more (see OpenAI's [accuracy per language](https://github.com/openai/whisper#available-models-and-languages)).
- **Really good in Greek 🇬🇷**: this project started for Greek and is **tested on many hours of real Greek recordings** (university lectures, with noise and several speakers). For Greek it gives the model a Greek hint and removes the phrases Whisper tends to "imagine" in silence.

> [!TIP]
> Automatic detection works well, but if all your recordings are in one language, set it in `app\settings.txt` (e.g. `language = de`): it is a bit more accurate, especially at the start of a recording.

---

## ⚡ Works on any computer, but much faster with an NVIDIA card

It runs on **any Windows 10/11 computer**. If you have an **NVIDIA graphics card**, it uses it automatically and finishes **10-20 times faster**. Without NVIDIA it runs on the processor (CPU): same result, just slower. It uses **all the real cores** of your processor (by default faster-whisper uses only 4).

**Approximate times for 1 hour of recording:**

| Computer | `large-v3` (default, most accurate) | `large-v3-turbo` (faster) |
|---|---|---|
| NVIDIA RTX 30xx / 40xx / 50xx | ~4-8 min | ~2-4 min |
| NVIDIA GTX 1060-1080 / 16xx | ~12-15 min | ~6-8 min |
| Without NVIDIA: modern processor, 8+ cores | ~1-2 hours | ~30-60 min |
| Without NVIDIA: older 4-core processor (e.g. i7-6700) | ~3-3½ hours | ~1-1½ hours |
| AMD or Intel graphics card | same as without NVIDIA | same as without NVIDIA |

> [!NOTE]
> Measured: **GTX 1060 6GB** and **i7-6700** with `large-v3` (the i7-6700 runs at ~0.3× real time); the others are estimates and depend on the computer, the noise and the silences of the recording. Only **NVIDIA cards** (CUDA) are used; with an AMD/Intel card the program works normally on the processor. Without NVIDIA, try `large-v3-turbo` (see «Settings» below) or let it run while you are away.

---

## 📥 Installation

**You need:** Windows 10 or 11 (64-bit), ~5 GB of free space and internet **only for the installation**.

1. At the top right of this page: **Code → Download ZIP**.
2. Unzip the folder (it will be called `stenografos-main`, you can rename it) where you want the program to live, e.g. `C:\` or `D:\Programs\`.
   > ⚠️ **Not** inside OneDrive / Google Drive / Dropbox: ~5 GB would be uploaded to the cloud.
3. In the folder, **double-click `Install.bat`**.
   If Windows shows a blue «Windows protected your PC» window: **More info → Run anyway**.
4. A black window opens and tells you **which folder** everything goes into (the `app` subfolder). Press **Enter**.
5. Wait for the 4 steps (**10-30 minutes** in total, depending on your connection):
   ```
   [1/4] Downloading the installer tool (uv)...          ✓
   [2/4] Downloading Python 3.12...                      ✓
   [3/4] Installing the libraries (Whisper)...           ✓
   [4/4] Downloading the speech model (~3 GB)...         ✓
   ```
   At the end it tells you whether an NVIDIA card was found and asks if you want a **desktop shortcut** (Y/N).

After installation the folder contains:

```
stenografos-main\
├─ Stenografos (By Nikitas Katsaitis).bat   ← this is what you use
├─ Transcripts\                             ← the transcripts appear here
├─ Install.bat
├─ Uninstall.bat
└─ app\                                     ← the "engine" (no need to go in)
```

> 💡 If the installation stops (e.g. the internet dropped), just run `Install.bat` again: it continues where it stopped.

---

## ▶️ Usage

1. **Drag** one or more recordings onto **`Stenografos (By Nikitas Katsaitis).bat`** (or the shortcut).
   *Or:* **double-click** it and choose files in the window.
2. You see the list of files, the language and where they will be saved. If there are several, it asks «Continue?» (**Enter** = yes).
3. Wait. The progress looks like this:
   ```
   42.5%  ·  00:25:30 / 01:00:00  ·  ~00:08:10 left
   ```
4. At the end you hear a sound, a notification appears and the **`Transcripts`** folder opens by itself.

You can close the window at any time: whatever was written so far stays saved.

**Accepted files:** `m4a, mp3, wav, ogg, opus, flac, aac, wma, amr, 3gp` and video `mp4, mkv, webm, mov` (only the audio is used).

### The transcripts

For each recording you get **two** files with the same name:

```
Transcripts\
├─ Notes Oct 12, 14.10.txt                ← clean text in paragraphs
└─ Notes Oct 12, 14.10 (timestamps).txt   ← every phrase with its time
```

### Recordings in parts

Phones save recordings with the **date and time** in the name (e.g. `Oct 12, 14.10.m4a`). **Keep it**, and if you like, add a word in front to tell them apart:

```
Notes Oct 12, 14.10.m4a
Notes Oct 12, 15.12.m4a      ← 2nd part of the same recording
Meeting Oct 13, 10.05.m4a
```

If you drag them all together, the program understands which parts belong together (same name, same day, different time), puts them in order and numbers them «(1 of 2)», «(2 of 2)». The formats `2026-10-12 14.10` and `20261012_141000` also work.

> 💡 A long recording is safer in parts of ~1 hour. Keep the phone close to the speaker (not in a pocket) and put it in airplane mode so a call doesn't interrupt it.

### ⚙️ Settings

Open **`app\settings.txt`** with Notepad:

| Setting | What it does |
|---|---|
| `ui_language` | Language of the messages: `auto` (= Windows language) · `en` · `el` |
| `model` | `large-v3` (default) · `large-v3-turbo` (2-3× faster) · `medium` / `small` (for very weak computers) |
| `language` | `auto` (Greek if Windows is in Greek, otherwise automatic detection) · `detect` (always automatic) · `en`, `el`, `de`, `fr`… (always this language) |
| `output_folder` | Another folder for the transcripts, e.g. `D:\Transcripts` (empty = `Transcripts`) |
| `device` | `auto` (NVIDIA if present) · `cpu` (processor only) |
| `cpu_threads` | Processor threads: `auto` (all the real cores) or a number |
| `prompt` | A sentence describing the recording, in its language; helps the model a little |
| `open_folder_when_done` / `notification` | `yes` / `no` |

**Vocabulary:** in **`app\vocabulary.txt`** write, one per line, names and special terms that come out wrong. The model "sees" them before it starts and writes them more correctly (~40-50 fit).

---

## ✨ Make the text perfect with an AI

> [!TIP]
> The text you get is **raw**: everything that was said, with repetitions, "umm", small talk and some mistakes in names or special terms. To turn it into **clean notes**, give the `.txt` to an AI (ChatGPT, Claude, Gemini etc.) together with a **short "setup"**: what the recording is and what you want out of it.
>
> **Example setup** (change the parts in [brackets]):
>
> ```
> Here is text from an automatic transcription in [language].
> It is [e.g. my voice notes / a work meeting / a lecture recorded
> in class, so it has noise and side conversations].
> I want you to:
> 1. Fix words, names and terms that came out wrong
>    (the topic is [topic], the speakers are [names]).
> 2. Remove repetitions, "umm" and unrelated chat.
> 3. Organise it in sections with headings [or: a list of the key points /
>    a one-page summary / questions and answers for studying].
> 4. Mark with [?] anything you are not sure you understood correctly.
> 5. NOT add information that was not said.
> ```
>
> **Ideas for what to ask:** notes with headings · a short summary · a list of decisions and to-dos (for meetings) · questions and answers for revision · an email or text ready to send.
>
> **Tips:**
> - If the text is very long, give it in **parts** (e.g. one hour of recording at a time).
> - The **`(timestamps)`** file helps you find where in the audio something was said, to listen again.
> - Put the terms the AI corrected into `app\vocabulary.txt`: the next recording comes out better from the start.
> - ⚠️ When you give text to an **online** AI, the text **leaves** your computer. Don't do it for sensitive or personal conversations without the consent of the people speaking.

---

## 🗑️ Uninstall

**Double-click `Uninstall.bat`:**

1. It shows you what will be deleted (the whole folder and the shortcut) and how many transcripts you have.
2. It asks whether to **keep the transcripts**: if yes, they are moved to the **desktop**, into the folder «Transcripts (Stenografos)».
3. To confirm, type **YES**. Anything else cancels, without deleting anything.
4. As soon as the window closes, the folder deletes itself within a few seconds.

**Everything goes:** Python, libraries, model, settings, shortcut. The program **installed nothing outside its own folder**, so no trace is left on the computer.

> Alternatively: delete the whole folder and the shortcut by hand (save your transcripts from `Transcripts` first). If you changed `output_folder`, those transcripts are not touched.

---

## 🛠️ Common problems

| Problem | Solution |
|---|---|
| «Stenografos is not installed yet» | Run `Install.bat` first |
| Stuck for a long time at `[4/4]` | ~3 GB are being downloaded, that's normal. If it stopped completely, run `Install.bat` again |
| It says «Trying the next option...» | The graphics card didn't cooperate; it continues on the processor. Nothing to do |
| The computer is slow while it works | Normal: it uses the whole card / processor. Don't run it twice at the same time |
| Strange phrases appear in silences | Whisper "imagines" things in silence. The most common ones (e.g. «Thanks for watching») are removed automatically |
| Wrong language in the text | Set the language in `app\settings.txt` (e.g. `language = en`) |
| I moved the folder and the shortcut doesn't work | Run `Install.bat` again |

---

## 📂 Structure

```
Install.bat            installation (once)
Uninstall.bat          uninstall
README.md              these instructions (README.el.md: in Greek)
LICENSE                MIT license
app/
  transcribe.py        the transcription
  install.ps1          what Install.bat does
  uninstall.ps1        what Uninstall.bat does
  download_model.py    model download
  settings.txt         settings
  vocabulary.txt       vocabulary
  requirements*.txt    library versions
```

## 📜 License

MIT © Nikitas Katsaitis · Built on [OpenAI Whisper](https://github.com/openai/whisper), [SYSTRAN faster-whisper](https://github.com/SYSTRAN/faster-whisper), [CTranslate2](https://github.com/OpenNMT/CTranslate2) and [Astral uv](https://github.com/astral-sh/uv).

