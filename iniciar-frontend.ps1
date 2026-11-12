$ErrorActionPreference = 'Stop'
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    $nodePath = Join-Path $env:LOCALAPPDATA 'Programs\nodejs'
    if (Test-Path $nodePath) {
        $env:PATH = "$nodePath;$env:PATH"
    }
}
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
& npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
