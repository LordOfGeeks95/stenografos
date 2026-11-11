# Greek Speech To Text (By Nikitas Katsaitis) - εγκατάσταση.
# Όλα μπαίνουν ΜΟΝΟ μέσα στον φάκελο app\. Για απεγκατάσταση σβήνεις όλο τον φάκελο.
# Παράμετρος -Yes: χωρίς ερωτήσεις (για δοκιμές).
param([switch]$Yes)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # το progress bar του PowerShell 5 κάνει τα downloads πολύ αργά
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$App  = $PSScriptRoot
$Root = Split-Path $App -Parent
$Name = "Greek Speech To Text (By Nikitas Katsaitis)"
$Py   = Join-Path $App ".venv\Scripts\python.exe"
$Uv   = Join-Path $App "tools\uv.exe"

$env:UV_PYTHON_INSTALL_DIR = Join-Path $App "python"
$env:UV_CACHE_DIR          = Join-Path $App ".uv-cache"
$env:UV_PYTHON_PREFERENCE  = "only-managed"
$env:HF_HOME               = Join-Path $App ".hf"   # προσωρινά του κατεβάσματος: κι αυτά μέσα στον φάκελο
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$env:PYTHONIOENCODING = "utf-8"

function Step($n, $text) { Write-Host ""; Write-Host "[$n/4] $text" -ForegroundColor Cyan }
function Ok($text)       { Write-Host "      ✓ $text" -ForegroundColor Green }
function Pause-End {
    if (-not $Yes) { Write-Host ""; Read-Host "Πάτα Enter για να κλείσει το παράθυρο" | Out-Null }
}

Clear-Host
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "   $Name" -ForegroundColor Yellow
Write-Host "   Εγκατάσταση" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Όλα θα εγκατασταθούν ΜΟΝΟ μέσα στον φάκελο:"
Write-Host "   $App" -ForegroundColor White
Write-Host "Δεν αλλάζει τίποτα άλλο στον υπολογιστή σου."
Write-Host "Για απεγκατάσταση αρκεί να σβήσεις όλο τον φάκελο."
Write-Host ""
Write-Host "Χρειάζονται: ~5 GB ελεύθερος χώρος και ίντερνετ (μόνο τώρα)."
Write-Host "Διάρκεια: 10-30 λεπτά, ανάλογα με τη σύνδεση."

# Έλεγχος χώρου στον δίσκο
try {
    $drive = Get-PSDrive -Name ($App.Substring(0, 1))
    $freeGB = [math]::Round($drive.Free / 1GB, 1)
    Write-Host "Ελεύθερος χώρος στον δίσκο $($drive.Name): $freeGB GB"
    if ($freeGB -lt 5) { Write-Host "⚠ Λίγος χώρος! Μπορεί να μη χωρέσει το μοντέλο." -ForegroundColor Red }
} catch {}

if ($Root -match "OneDrive|Google Drive|My Drive|Dropbox") {
    Write-Host ""
    Write-Host "⚠ Ο φάκελος φαίνεται να συγχρονίζεται (OneDrive / Google Drive / Dropbox)." -ForegroundColor Red
    Write-Host "  Θα ανέβουν ~5 GB στο cloud. Καλύτερα μετάφερε τον φάκελο αλλού (π.χ. C:\ ή D:\) και ξανατρέξε το Install.bat." -ForegroundColor Red
}

if (-not $Yes) { Write-Host ""; Read-Host "Πάτα Enter για να ξεκινήσει (ή κλείσε το παράθυρο για ακύρωση)" | Out-Null }

try {
    # ---------------------------------------------------------------- 1. uv
    Step 1 "Κατεβάζω το εργαλείο εγκατάστασης (uv)..."
    if (-not (Test-Path $Uv)) {
        $tools = Join-Path $App "tools"
        New-Item -ItemType Directory -Force $tools | Out-Null
        $zip = Join-Path $tools "uv.zip"
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip
        Expand-Archive -Path $zip -DestinationPath $tools -Force
        Remove-Item $zip
    }
    Ok "uv έτοιμο"

    # ---------------------------------------------------------------- 2. Python
    Step 2 "Κατεβάζω την Python 3.12 (μόνο για αυτό το πρόγραμμα)..."
    if (-not (Test-Path $Py)) {
        & $Uv venv (Join-Path $App ".venv") --python 3.12 --quiet
        if ($LASTEXITCODE -ne 0) { throw "Δεν έγινε η εγκατάσταση της Python." }
    }
    Ok "Python έτοιμη"

    # ---------------------------------------------------------------- 3. βιβλιοθήκες
    Step 3 "Εγκαθιστώ τις βιβλιοθήκες (Whisper)..."
    $gpu = $false
    $gpuName = ""
    try {
        # (Όχι Select-Object -First 1 στο pipeline: σταματά το nvidia-smi και δίνει exit code -1.)
        $out = @(& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null)
        if ($LASTEXITCODE -eq 0 -and $out.Count -gt 0 -and $out[0]) { $gpu = $true; $gpuName = "$($out[0])".Trim() }
    } catch {}
    $reqs = @("-r", (Join-Path $App "requirements.txt"))
    if ($gpu) {
        Write-Host "      Βρέθηκε κάρτα NVIDIA ($gpuName): μπαίνουν και οι βιβλιοθήκες CUDA (~1 GB)."
        $reqs += @("-r", (Join-Path $App "requirements-gpu.txt"))
    }
    & $Uv pip install --python $Py @reqs
    if ($LASTEXITCODE -ne 0) { throw "Δεν έγινε η εγκατάσταση των βιβλιοθηκών." }
    Ok "βιβλιοθήκες έτοιμες"

    # ---------------------------------------------------------------- 4. μοντέλο
    Step 4 "Κατεβάζω το μοντέλο φωνής (~3 GB, θέλει λίγη ώρα)..."
    Push-Location $App
    & $Py -I (Join-Path $App "download_model.py")
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { throw "Δεν κατέβηκε το μοντέλο. Έλεγξε τη σύνδεση και ξανατρέξε το Install.bat." }
    Ok "μοντέλο έτοιμο"

    # Καθάρισμα προσωρινών αρχείων εγκατάστασης (γλιτώνει 1-2 GB)
    try { & $Uv cache clean --quiet } catch {}

    # ---------------------------------------------------------------- αρχείο εκκίνησης + φάκελος κειμένων
    $bat = Join-Path $Root "$Name.bat"
    $lines = @(
        "@echo off",
        "rem Drag recordings onto this file, or double-click it to choose files.",
        "chcp 65001 >nul",
        "set PYTHONIOENCODING=utf-8",
        "if not exist ""%~dp0app\.venv\Scripts\python.exe"" (",
        "  echo Greek Speech To Text is not installed yet. Please run Install.bat first.",
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
        Write-Host "Κάρτα γραφικών: $gpuName → γρήγορη λειτουργία (1 ώρα ήχου ≈ 10-20 λεπτά)." -ForegroundColor Green
    } else {
        Write-Host "Δεν βρέθηκε κάρτα NVIDIA → θα δουλεύει με τον επεξεργαστή (πιο αργά, 1 ώρα ήχου ≈ 2-5 ώρες)." -ForegroundColor Yellow
        Write-Host "Συμβουλή: στο app\settings.txt βάλε model = large-v3-turbo για πιο γρήγορα αποτελέσματα."
    }

    # ---------------------------------------------------------------- συντόμευση
    $answer = "ν"
    if (-not $Yes) { Write-Host ""; $answer = Read-Host "Θέλεις συντόμευση στην επιφάνεια εργασίας; (Ν/Ο)" }
    if (-not $Yes -and $answer -match "^(ν|n|y|ναι|yes)?$") {
        $desktop = [Environment]::GetFolderPath("Desktop")
        $sc = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop "$Name.lnk"))
        $sc.TargetPath = $bat
        $sc.WorkingDirectory = $Root
        $sc.IconLocation = "$env:SystemRoot\System32\imageres.dll,190"
        $sc.Save()
        Ok "συντόμευση στην επιφάνεια εργασίας"
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " ✓ Έτοιμο!" -ForegroundColor Green
    Write-Host "   Σύρε ηχογραφήσεις πάνω στο:" -ForegroundColor Green
    Write-Host "     $Name.bat" -ForegroundColor White
    Write-Host "   Τα κείμενα θα βγαίνουν στον φάκελο Transcripts." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Pause-End
}
catch {
    Write-Host ""
    Write-Host "✖ Κάτι πήγε στραβά: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Έλεγξε τη σύνδεση στο ίντερνετ και ξανατρέξε το Install.bat (συνεχίζει από εκεί που έμεινε)." -ForegroundColor Red
    Pause-End
    exit 1
}
