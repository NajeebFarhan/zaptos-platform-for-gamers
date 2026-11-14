# Starts the Zaptos backend (FastAPI on :8000) and frontend (Vite on :5173).
# First run installs dependencies. Usage:  .\start.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# --- backend -------------------------------------------------------------
$backend = Join-Path $root "backend"
$py = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv (Join-Path $backend ".venv")
    & $py -m pip install --upgrade pip
    & $py -m pip install -r (Join-Path $backend "requirements.txt")
}

# --- frontend ------------------------------------------------------------
$frontend = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend packages..." -ForegroundColor Cyan
    Push-Location $frontend; npm install; Pop-Location
}

Write-Host "Starting API on http://127.0.0.1:8000 ..." -ForegroundColor Green
$api = Start-Process -FilePath $py -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" -WorkingDirectory $backend -PassThru -NoNewWindow

Write-Host "Starting web app on http://localhost:5173 ..." -ForegroundColor Green
try {
    Push-Location $frontend
    npm run dev
}
finally {
    Pop-Location
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}
