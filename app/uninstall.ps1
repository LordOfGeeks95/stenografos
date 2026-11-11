# Greek Speech To Text (By Nikitas Katsaitis) - απεγκατάσταση.
# Σβήνει ΟΛΟ τον φάκελο του προγράμματος και τη συντόμευση της επιφάνειας εργασίας.
# Πριν σβήσει, ρωτάει αν θέλεις να κρατήσεις τα κείμενα (μεταφέρονται στην επιφάνεια εργασίας).
# Παράμετροι για δοκιμές: -Yes (χωρίς ερωτήσεις, κρατάει τα κείμενα) · -Desktop <φάκελος>
param([switch]$Yes, [string]$Desktop = "")

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$App  = $PSScriptRoot
$Root = Split-Path $App -Parent
$Name = "Greek Speech To Text (By Nikitas Katsaitis)"
if (-not $Desktop) { $Desktop = [Environment]::GetFolderPath("Desktop") }
$Transcripts = Join-Path $Root "Transcripts"

function Pause-End { if (-not $Yes) { Write-Host ""; Read-Host "Πάτα Enter για να κλείσει το παράθυρο" | Out-Null } }

Clear-Host
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "   $Name" -ForegroundColor Yellow
Write-Host "   Απεγκατάσταση" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow

# Ασφάλεια: σβήνουμε μόνο αν ο φάκελος είναι όντως το πρόγραμμα (και όχι π.χ. ολόκληρος δίσκος).
$looksRight = (Test-Path (Join-Path $Root "Install.bat")) -and (Test-Path (Join-Path $App "transcribe.py"))
$isDriveRoot = ([IO.Path]::GetPathRoot($Root).TrimEnd('\') -eq $Root.TrimEnd('\'))
if (-not $looksRight -or $isDriveRoot) {
    Write-Host ""
    Write-Host "✖ Ο φάκελος δεν μοιάζει με τον φάκελο του προγράμματος, οπότε δεν σβήνω τίποτα για ασφάλεια:" -ForegroundColor Red
    Write-Host "  $Root" -ForegroundColor Red
    Write-Host "  Σβήσ' τον με το χέρι αν είσαι σίγουρος." -ForegroundColor Red
    Pause-End
    exit 1
}

$sizeGB = 0
try { $sizeGB = [math]::Round(((Get-ChildItem $Root -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1GB, 1) } catch {}
$nTxt = 0
if (Test-Path $Transcripts) { $nTxt = @(Get-ChildItem $Transcripts -Recurse -File -ErrorAction SilentlyContinue).Count }

Write-Host ""
Write-Host "Θα σβηστούν ΟΛΑ:"
Write-Host "   • ο φάκελος  $Root  ($sizeGB GB: πρόγραμμα, Python, μοντέλο)" -ForegroundColor White
Write-Host "   • η συντόμευση στην επιφάνεια εργασίας (αν υπάρχει)" -ForegroundColor White
Write-Host "Τίποτα άλλο στον υπολογιστή δεν αλλάζει (το πρόγραμμα δεν είχε εγκαταστήσει κάτι αλλού)."
Write-Host ""
Write-Host "Μέσα στον φάκελο Transcripts υπάρχουν $nTxt αρχεία κειμένου."
Write-Host "(Αν είχες αλλάξει τον φάκελο εξόδου στο settings.txt, εκείνα τα κείμενα ΔΕΝ πειράζονται.)"

$keep = $true
if (-not $Yes) {
    Write-Host ""
    $a = Read-Host "Να κρατήσω τα κείμενα; Θα μεταφερθούν στην επιφάνεια εργασίας. (Ν = ναι / Ο = όχι, σβήσ' τα)"
    if ($a -match "^(ο|o|όχι|οχι|no|n)$") { $keep = $false }
    Write-Host ""
    $c = Read-Host "Σίγουρα να γίνει η απεγκατάσταση; Γράψε ΝΑΙ για να συνεχίσει"
    if ($c -notmatch "^(ναι|ΝΑΙ|nai|NAI|yes|YES|Ναι)$") {
        Write-Host "Ακυρώθηκε. Δεν σβήστηκε τίποτα." -ForegroundColor Green
        Pause-End
        exit 0
    }
}

try {
    # 1. Κείμενα → επιφάνεια εργασίας
    if ($keep -and $nTxt -gt 0) {
        $dest = Join-Path $Desktop "Transcripts (Greek Speech To Text)"
        $i = 2
        while (Test-Path $dest) { $dest = Join-Path $Desktop "Transcripts (Greek Speech To Text) $i"; $i++ }
        Copy-Item $Transcripts $dest -Recurse
        $copied = @(Get-ChildItem $dest -Recurse -File).Count
        if ($copied -ne $nTxt) { throw "Η αντιγραφή των κειμένων δεν ολοκληρώθηκε ($copied από $nTxt). Δεν σβήνω τίποτα." }
        Write-Host "✓ Τα κείμενα ($nTxt αρχεία) είναι πλέον στο: $dest" -ForegroundColor Green
    }

    # 2. Συντόμευση (μόνο αν δείχνει σε ΑΥΤΟ το πρόγραμμα)
    $lnk = Join-Path $Desktop "$Name.lnk"
    if (Test-Path $lnk) {
        $target = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk).TargetPath
        if ($target -like "$Root\*") { Remove-Item $lnk -Force; Write-Host "✓ Σβήστηκε η συντόμευση" -ForegroundColor Green }
    }

    # 3. Ο φάκελος. Δεν σβήνεται όσο τρέχει αυτό το script από μέσα του, οπότε το αναθέτουμε
    #    σε ένα κρυφό cmd που περιμένει 3 δευτερόλεπτα να κλείσει το παράθυρο και μετά σβήνει.
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " ✓ Η απεγκατάσταση ολοκληρώνεται." -ForegroundColor Green
    Write-Host "   Ο φάκελος θα σβηστεί μόλις κλείσει αυτό το παράθυρο." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Pause-End
    Set-Location $env:TEMP
    $cmd = "/c timeout /t 3 /nobreak >nul & rmdir /s /q `"$Root`""
    Start-Process -FilePath "cmd.exe" -ArgumentList $cmd -WindowStyle Hidden -WorkingDirectory $env:TEMP
}
catch {
    Write-Host ""
    Write-Host "✖ Κάτι πήγε στραβά: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Μπορείς να σβήσεις τον φάκελο και με το χέρι (δεξί κλικ → Διαγραφή)." -ForegroundColor Red
    Pause-End
    exit 1
}
