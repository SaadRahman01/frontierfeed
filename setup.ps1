# One-shot local setup for Windows.
# Right-click this file and choose "Run with PowerShell", or from a terminal:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Setting up frontierfeed in $PSScriptRoot`n"

# --- Python check -----------------------------------------------------------
$py = $null
foreach ($candidate in @("py", "python", "python3")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $py = $candidate; break }
}
if (-not $py) {
    Write-Host "Python not found. Install Python 3.10 or newer from https://python.org"
    Write-Host "During install, tick 'Add Python to PATH'."
    Read-Host "Press Enter to close"
    exit 1
}

$version = & $py -c "import sys; print('%d.%d' % sys.version_info[:2])"
Write-Host "Python $version"
$parts = $version.Split(".")
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 10)) {
    Write-Host "This needs Python 3.10 or newer."
    Read-Host "Press Enter to close"
    exit 1
}

# --- Virtual environment ----------------------------------------------------
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    & $py -m venv .venv
}
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Installing dependencies..."
& $venvPy -m pip install --quiet --upgrade pip
& $venvPy -m pip install --quiet -r requirements.txt

# --- First run --------------------------------------------------------------
Write-Host "`nFetching sources. A 403 or timeout on one source is fine - the run"
Write-Host "continues on whatever else responds.`n"
& $venvPy -m src.main

# --- Open the result --------------------------------------------------------
$page = Join-Path $PSScriptRoot "docs\index.html"
Write-Host "`nDone. Site written to:"
Write-Host "  $page"
Write-Host "`nNext time, run:"
Write-Host "  .\.venv\Scripts\python.exe -m src.main"

if (Test-Path $page) { Start-Process $page }
Read-Host "`nPress Enter to close"
