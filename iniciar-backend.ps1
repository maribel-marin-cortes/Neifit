param([switch]$Demo)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'backend')
$env:DEBUG = 'true'
$env:PYTHONIOENCODING = 'utf-8'
$env:APP_ENV = 'development'
# Para pruebas demo: .\iniciar-backend.ps1 -Demo
$env:ENABLE_DEMO_AUTH = if ($Demo) { 'true' } else { 'false' }
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
