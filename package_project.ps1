# PowerShell script to package ClaimForge for deployment
Write-Host "Creating clean deployment package..." -ForegroundColor Cyan
& ".\venv\Scripts\python.exe" package_project.py
