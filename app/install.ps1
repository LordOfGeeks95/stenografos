# Stenografos (By Nikitas Katsaitis) - installer.
# Everything goes ONLY inside the app\ folder. To uninstall, delete the whole folder (or run Uninstall.bat).
# Messages in Greek when Windows is in Greek, otherwise in English (setting ui_language in settings.txt).
# Switch -Yes: no questions (for testing).
param([switch]$Yes)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # the PowerShell 5 progress bar makes downloads very slow
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$App  = $PSScriptRoot
$Root = Split-Path $App -Parent
$Name = "Stenografos (By Nikitas Katsaitis)"
$Py   = Join-Path $App ".venv\Scripts\python.exe"
$Uv   = Join-Path $App "tools\uv.exe"

# ---------------------------------------------------------------- language of the messages
$ui = "auto"
try {
    $line = Get-Content (Join-Path $App "settings.txt") -Encoding UTF8 | Where-Object { $_ -match '^\s*ui_language\s*=' } | Select-Object -First 1
    if ($line) { $v = ($line -split '=', 2)[1].Trim().ToLower(); if ($v) { $ui = $v } }
} catch {}
if ($ui -eq "el") { $Greek = $true }
elseif ($ui -eq "en") { $Greek = $false }
else { $Greek = ((Get-UICulture).TwoLetterISOLanguageName -eq "el") -or ((Get-Culture).TwoLetterISOLanguageName -eq "el") }   # display language OR regional format
function L($el, $en) { if ($Greek) { $el } else { $en } }

$env:UV_PYTHON_INSTALL_DIR = Join-Path $App "python"
$env:UV_CACHE_DIR          = Join-Path $App ".uv-cache"
$env:UV_PYTHON_PREFERENCE  = "only-managed"
$env:HF_HOME               = Join-Path $App ".hf"   # download temp files: also inside the folder
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$env:PYTHONIOENCODING = "utf-8"

function Step($n, $text) { Write-Host ""; Write-Host "[$n/4] $text" -ForegroundColor Cyan }
function Ok($text)       { Write-Host "      ✓ $text" -ForegroundColor Green }
function Pause-End {
    if (-not $Yes) { Write-Host ""; Read-Host (L "Πάτα Enter για να κλείσει το παράθυρο" "Press Enter to close this window") | Out-Null }
}

Clear-Host
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "   $Name" -ForegroundColor Yellow
Write-Host (L "   Εγκατάσταση" "   Installation") -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host (L "Όλα θα εγκατασταθούν ΜΟΝΟ μέσα στον φάκελο:" "Everything will be installed ONLY inside this folder:")
Write-Host "   $App" -ForegroundColor White
Write-Host (L "Δεν αλλάζει τίποτα άλλο στον υπολογιστή σου." "Nothing else on your computer changes.")
Write-Host (L "Για απεγκατάσταση: Uninstall.bat (ή σβήνεις όλο τον φάκελο)." "To uninstall: Uninstall.bat (or delete the whole folder).")
Write-Host ""
Write-Host (L "Χρειάζονται: ~5 GB ελεύθερος χώρος και ίντερνετ (μόνο τώρα)." "Needed: ~5 GB of free space and internet (only now).")
Write-Host (L "Διάρκεια: 10-30 λεπτά, ανάλογα με τη σύνδεση." "Time: 10-30 minutes, depending on your connection.")

# Free disk space
try {
    $drive = Get-PSDrive -Name ($App.Substring(0, 1))
    $freeGB = [math]::Round($drive.Free / 1GB, 1)
    Write-Host ((L "Ελεύθερος χώρος στον δίσκο {0}: {1} GB" "Free space on drive {0}: {1} GB") -f $drive.Name, $freeGB)
    if ($freeGB -lt 5) { Write-Host (L "⚠ Λίγος χώρος! Μπορεί να μη χωρέσει το μοντέλο." "⚠ Low on space! The model may not fit.") -ForegroundColor Red }
} catch {}

if ($Root -match "OneDrive|Google Drive|My Drive|Dropbox") {
    Write-Host ""
    Write-Host (L "⚠ Ο φάκελος φαίνεται να συγχρονίζεται (OneDrive / Google Drive / Dropbox)." "⚠ This folder seems to be synced (OneDrive / Google Drive / Dropbox).") -ForegroundColor Red
    Write-Host (L "  Θα ανέβουν ~5 GB στο cloud. Καλύτερα μετάφερε τον φάκελο αλλού (π.χ. C:\ ή D:\) και ξανατρέξε το Install.bat." "  ~5 GB would be uploaded to the cloud. Better move the folder elsewhere (e.g. C:\ or D:\) and run Install.bat again.") -ForegroundColor Red
}

if (-not $Yes) { Write-Host ""; Read-Host (L "Πάτα Enter για να ξεκινήσει (ή κλείσε το παράθυρο για ακύρωση)" "Press Enter to start (or close this window to cancel)") | Out-Null }

try {
    # ---------------------------------------------------------------- 1. uv
    Step 1 (L "Κατεβάζω το εργαλείο εγκατάστασης (uv)..." "Downloading the installer tool (uv)...")
    if (-not (Test-Path $Uv)) {
        $tools = Join-Path $App "tools"
        New-Item -ItemType Directory -Force $tools | Out-Null
        $zip = Join-Path $tools "uv.zip"
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip
        Expand-Archive -Path $zip -DestinationPath $tools -Force
        Remove-Item $zip
    }
    Ok (L "uv έτοιμο" "uv ready")

    # ---------------------------------------------------------------- 2. Python
    Step 2 (L "Κατεβάζω την Python 3.12 (μόνο για αυτό το πρόγραμμα)..." "Downloading Python 3.12 (only for this program)...")
    if (-not (Test-Path $Py)) {
        & $Uv venv (Join-Path $App ".venv") --python 3.12 --quiet
        if ($LASTEXITCODE -ne 0) { throw (L "Δεν έγινε η εγκατάσταση της Python." "Python could not be installed.") }
    }
    Ok (L "Python έτοιμη" "Python ready")

    # ---------------------------------------------------------------- 3. libraries
    Step 3 (L "Εγκαθιστώ τις βιβλιοθήκες (Whisper)..." "Installing the libraries (Whisper)...")
    $gpu = $false
    $gpuName = ""
    try {
        # (No Select-Object -First 1 in the pipeline: it stops nvidia-smi and gives exit code -1.)
        $out = @(& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null)
        if ($LASTEXITCODE -eq 0 -and $out.Count -gt 0 -and $out[0]) { $gpu = $true; $gpuName = "$($out[0])".Trim() }
    } catch {}
    $reqs = @("-r", (Join-Path $App "requirements.txt"))
    if ($gpu) {
        Write-Host ((L "      Βρέθηκε κάρτα NVIDIA ({0}): μπαίνουν και οι βιβλιοθήκες CUDA (~1 GB)." "      NVIDIA card found ({0}): also installing the CUDA libraries (~1 GB).") -f $gpuName)
        $reqs += @("-r", (Join-Path $App "requirements-gpu.txt"))
    }
    & $Uv pip install --python $Py @reqs
    if ($LASTEXITCODE -ne 0) { throw (L "Δεν έγινε η εγκατάσταση των βιβλιοθηκών." "The libraries could not be installed.") }
    Ok (L "βιβλιοθήκες έτοιμες" "libraries ready")

    # ---------------------------------------------------------------- 4. model
    Step 4 (L "Κατεβάζω το μοντέλο φωνής (~3 GB, θέλει λίγη ώρα)..." "Downloading the speech model (~3 GB, takes a while)...")
    Push-Location $App
    & $Py -I (Join-Path $App "download_model.py")
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { throw (L "Δεν κατέβηκε το μοντέλο. Έλεγξε τη σύνδεση και ξανατρέξε το Install.bat." "The model was not downloaded. Check your connection and run Install.bat again.") }
    Ok (L "μοντέλο έτοιμο" "model ready")

    # Clean the installer's temp files (saves 1-2 GB)
    try { & $Uv cache clean --quiet } catch {}

    # ---------------------------------------------------------------- launcher + transcripts folder
    $bat = Join-Path $Root "$Name.bat"
    $lines = @(
        "@echo off",
        "rem Drag recordings onto this file, or double-click it to choose files.",
        "chcp 65001 >nul",
        "set PYTHONIOENCODING=utf-8",
        "if not exist ""%~dp0app\.venv\Scripts\python.exe"" (",
        "  echo Stenografos is not installed yet. Please run Install.bat first.",
        "  pause",
        "  exit /b",
        ")",
        """%~dp0app\.venv\Scripts\python.exe"" ""%~dp0app\transcribe.py"" %*",
        "echo.",
        "pause"
    )
    [IO.File]::WriteAllLines($bat, $lines, [Text.Encoding]::ASCII)
    New-Item -ItemType Directory -Force (Join-Path $Root "Transcripts") | Out-Null

    Write-Host ""
    if ($gpu) {
        Write-Host ((L "Κάρτα γραφικών: {0} → γρήγορη λειτουργία (1 ώρα ήχου ≈ 10-20 λεπτά)." "Graphics card: {0} → fast mode (1 hour of audio ≈ 10-20 minutes).") -f $gpuName) -ForegroundColor Green
    } else {
        Write-Host (L "Δεν βρέθηκε κάρτα NVIDIA → θα δουλεύει με τον επεξεργαστή (πιο αργά)." "No NVIDIA card found → it will run on the processor (slower).") -ForegroundColor Yellow
        Write-Host (L "Συμβουλή: στο app\settings.txt βάλε model = large-v3-turbo για πιο γρήγορα αποτελέσματα." "Tip: set model = large-v3-turbo in app\settings.txt for faster results.")
    }

    # ---------------------------------------------------------------- shortcut
    $answer = "y"
    if (-not $Yes) { Write-Host ""; $answer = Read-Host (L "Θέλεις συντόμευση στην επιφάνεια εργασίας; (Ν/Ο)" "Do you want a desktop shortcut? (Y/N)") }
    # Empty = yes. In Greek, a Latin «n» is usually «ν» (= ναι) typed on the wrong keyboard.
    $yesWords = if ($Greek) { "^(|ν|n|ναι|nai|y|yes)$" } else { "^(|y|yes)$" }
    if (-not $Yes -and $answer.Trim().ToLower() -match $yesWords) {
        $desktop = [Environment]::GetFolderPath("Desktop")
        $sc = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop "$Name.lnk"))
        $sc.TargetPath = $bat
        $sc.WorkingDirectory = $Root
        $sc.IconLocation = "$env:SystemRoot\System32\imageres.dll,190"
        $sc.Save()
        Ok (L "συντόμευση στην επιφάνεια εργασίας" "desktop shortcut created")
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host (L " ✓ Έτοιμο!" " ✓ Done!") -ForegroundColor Green
    Write-Host (L "   Σύρε ηχογραφήσεις πάνω στο:" "   Drag recordings onto:") -ForegroundColor Green
    Write-Host "     $Name.bat" -ForegroundColor White
    Write-Host (L "   Τα κείμενα θα βγαίνουν στον φάκελο Transcripts." "   The transcripts will appear in the Transcripts folder.") -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Pause-End
}
catch {
    Write-Host ""
    Write-Host ((L "✖ Κάτι πήγε στραβά: {0}" "✖ Something went wrong: {0}") -f $_.Exception.Message) -ForegroundColor Red
    Write-Host (L "  Έλεγξε τη σύνδεση στο ίντερνετ και ξανατρέξε το Install.bat (συνεχίζει από εκεί που έμεινε)." "  Check your internet connection and run Install.bat again (it continues where it stopped).") -ForegroundColor Red
    Pause-End
    exit 1
}
