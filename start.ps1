# Kill any Python/uvicorn processes on port 8000
Write-Host "Stopping old servers..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "Starting Vinted Dashboard on http://127.0.0.1:8000" -ForegroundColor Green
Set-Location $PSScriptRoot
uv run uvicorn main:app --port 8000 --reload
