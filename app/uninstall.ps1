# Stenografos (By Nikitas Katsaitis) - uninstaller.
# Deletes the WHOLE program folder and the desktop shortcut.
# Before deleting, it asks whether to keep the transcripts (they are moved to the desktop).
# Messages in Greek when Windows is in Greek, otherwise in English (setting ui_language in settings.txt).
# Switches for testing: -Yes (no questions, keeps the transcripts) · -Desktop <folder>
param([switch]$Yes, [string]$Desktop = "")

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$App  = $PSScriptRoot
$Root = Split-Path $App -Parent
$Name = "Stenografos (By Nikitas Katsaitis)"
if (-not $Desktop) { $Desktop = [Environment]::GetFolderPath("Desktop") }
$Transcripts = Join-Path $Root "Transcripts"

$ui = "auto"
try {
    $line = Get-Content (Join-Path $App "settings.txt") -Encoding UTF8 | Where-Object { $_ -match '^\s*ui_language\s*=' } | Select-Object -First 1
    if ($line) { $v = ($line -split '=', 2)[1].Trim().ToLower(); if ($v) { $ui = $v } }
} catch {}
if ($ui -eq "el") { $Greek = $true }
elseif ($ui -eq "en") { $Greek = $false }
else { $Greek = ((Get-UICulture).TwoLetterISOLanguageName -eq "el") -or ((Get-Culture).TwoLetterISOLanguageName -eq "el") }   # display language OR regional format
function L($el, $en) { if ($Greek) { $el } else { $en } }

function Pause-End { if (-not $Yes) { Write-Host ""; Read-Host (L "Πάτα Enter για να κλείσει το παράθυρο" "Press Enter to close this window") | Out-Null } }

Clear-Host
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "   $Name" -ForegroundColor Yellow
Write-Host (L "   Απεγκατάσταση" "   Uninstall") -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow

# Safety: delete only if the folder really is the program (and not e.g. a whole drive).
$looksRight = (Test-Path (Join-Path $Root "Install.bat")) -and (Test-Path (Join-Path $App "transcribe.py"))
$isDriveRoot = ([IO.Path]::GetPathRoot($Root).TrimEnd('\') -eq $Root.TrimEnd('\'))
if (-not $looksRight -or $isDriveRoot) {
    Write-Host ""
    Write-Host (L "✖ Ο φάκελος δεν μοιάζει με τον φάκελο του προγράμματος, οπότε δεν σβήνω τίποτα για ασφάλεια:" "✖ This folder does not look like the program folder, so for safety nothing is deleted:") -ForegroundColor Red
    Write-Host "  $Root" -ForegroundColor Red
    Write-Host (L "  Σβήσ' τον με το χέρι αν είσαι σίγουρος." "  Delete it by hand if you are sure.") -ForegroundColor Red
    Pause-End
    exit 1
}

$sizeGB = 0
try { $sizeGB = [math]::Round(((Get-ChildItem $Root -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1GB, 1) } catch {}
$nTxt = 0
if (Test-Path $Transcripts) { $nTxt = @(Get-ChildItem $Transcripts -Recurse -File -ErrorAction SilentlyContinue).Count }

Write-Host ""
Write-Host (L "Θα σβηστούν ΟΛΑ:" "EVERYTHING will be deleted:")
Write-Host ((L "   • ο φάκελος  {0}  ({1} GB: πρόγραμμα, Python, μοντέλο)" "   • the folder  {0}  ({1} GB: program, Python, model)") -f $Root, $sizeGB) -ForegroundColor White
Write-Host (L "   • η συντόμευση στην επιφάνεια εργασίας (αν υπάρχει)" "   • the desktop shortcut (if there is one)") -ForegroundColor White
Write-Host (L "Τίποτα άλλο στον υπολογιστή δεν αλλάζει (το πρόγραμμα δεν είχε εγκαταστήσει κάτι αλλού)." "Nothing else on the computer changes (the program installed nothing anywhere else).")
Write-Host ""
Write-Host ((L "Μέσα στον φάκελο Transcripts υπάρχουν {0} αρχεία κειμένου." "The Transcripts folder contains {0} text files.") -f $nTxt)
Write-Host (L "(Αν είχες αλλάξει τον φάκελο εξόδου στο settings.txt, εκείνα τα κείμενα ΔΕΝ πειράζονται.)" "(If you changed the output folder in settings.txt, those transcripts are NOT touched.)")

$keep = $true
if (-not $Yes) {
    Write-Host ""
    $a = Read-Host (L "Να κρατήσω τα κείμενα; Θα μεταφερθούν στην επιφάνεια εργασίας. (Ν = ναι / Ο = όχι, σβήσ' τα)" "Keep the transcripts? They will be moved to the desktop. (Y = yes / N = no, delete them)")
    $noWords = if ($Greek) { "^(ο|o|όχι|οχι|no)$" } else { "^(n|no)$" }
    if ($a.Trim().ToLower() -match $noWords) { $keep = $false }
    Write-Host ""
    $c = Read-Host (L "Σίγουρα να γίνει η απεγκατάσταση; Γράψε ΝΑΙ για να συνεχίσει" "Are you sure you want to uninstall? Type YES to continue")
    if ($c.Trim() -notmatch "^(ναι|ΝΑΙ|Ναι|nai|NAI|yes|YES|Yes)$") {
        Write-Host (L "Ακυρώθηκε. Δεν σβήστηκε τίποτα." "Cancelled. Nothing was deleted.") -ForegroundColor Green
        Pause-End
        exit 0
    }
}

try {
    # 1. Transcripts → desktop
    if ($keep -and $nTxt -gt 0) {
        $dest = Join-Path $Desktop "Transcripts (Stenografos)"
        $i = 2
        while (Test-Path $dest) { $dest = Join-Path $Desktop "Transcripts (Stenografos) $i"; $i++ }
        Copy-Item $Transcripts $dest -Recurse
        $copied = @(Get-ChildItem $dest -Recurse -File).Count
        if ($copied -ne $nTxt) { throw ((L "Η αντιγραφή των κειμένων δεν ολοκληρώθηκε ({0} από {1}). Δεν σβήνω τίποτα." "Copying the transcripts did not finish ({0} of {1}). Nothing is deleted.") -f $copied, $nTxt) }
        Write-Host ((L "✓ Τα κείμενα ({0} αρχεία) είναι πλέον στο: {1}" "✓ The transcripts ({0} files) are now in: {1}") -f $nTxt, $dest) -ForegroundColor Green
    }

    # 2. Shortcut (only if it points to THIS program)
    $lnk = Join-Path $Desktop "$Name.lnk"
    if (Test-Path $lnk) {
        $target = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk).TargetPath
        if ($target -like "$Root\*") { Remove-Item $lnk -Force; Write-Host (L "✓ Σβήστηκε η συντόμευση" "✓ Shortcut deleted") -ForegroundColor Green }
    }

    # 3. The folder. It cannot be deleted while this script runs from inside it, so a hidden cmd
    #    waits 3 seconds for this window to close and then deletes it.
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host (L " ✓ Η απεγκατάσταση ολοκληρώνεται." " ✓ Uninstall is finishing.") -ForegroundColor Green
    Write-Host (L "   Ο φάκελος θα σβηστεί μόλις κλείσει αυτό το παράθυρο." "   The folder will be deleted as soon as this window closes.") -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Pause-End
    Set-Location $env:TEMP
    $cmd = "/c timeout /t 3 /nobreak >nul & rmdir /s /q `"$Root`""
    Start-Process -FilePath "cmd.exe" -ArgumentList $cmd -WindowStyle Hidden -WorkingDirectory $env:TEMP
}
catch {
    Write-Host ""
    Write-Host ((L "✖ Κάτι πήγε στραβά: {0}" "✖ Something went wrong: {0}") -f $_.Exception.Message) -ForegroundColor Red
    Write-Host (L "  Μπορείς να σβήσεις τον φάκελο και με το χέρι (δεξί κλικ → Διαγραφή)." "  You can also delete the folder by hand (right-click → Delete).") -ForegroundColor Red
    Pause-End
    exit 1
}
