$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$appUrl = 'http://127.0.0.1:8790'
$listener = Get-NetTCPConnection -LocalPort 8790 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $existingApp = $false
    try {
        $schema = Invoke-RestMethod -Uri "$appUrl/openapi.json" -TimeoutSec 3
        $existingApp = ($schema.info.title -eq 'Squat Coach') -and
            ($schema.paths.PSObject.Properties.Name -contains '/api/sessions')
    } catch { }
    if ($existingApp) {
        Write-Host "FORM is already running. Open $appUrl in your browser."
        return
    }
    throw "Port 8790 is occupied by another service. Close that service before starting FORM."
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
  py -3.11 -m venv .venv
  if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11, then run this launcher again.' }
  & $python -m pip install -r requirements.txt
  if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
}
if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) {
  throw 'The bundled frontend is missing. Build it using the instructions in README.md.'
}
if (-not (Test-Path -LiteralPath 'data\sessions.sqlite3')) {
  & $python restore_sessions.py
  if ($LASTEXITCODE -ne 0) { throw 'Saved session restoration failed.' }
}
& $python -m uvicorn backend.api:app --host 127.0.0.1 --port 8790
