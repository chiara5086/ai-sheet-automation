# Script para iniciar ambos servidores (Backend y Frontend)
# Uso: .\start_servers.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Sheet Automation - Iniciando Servidores" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "[ERROR] Este script debe ejecutarse desde el directorio raiz del proyecto" -ForegroundColor Red
    exit 1
}

# Iniciar Backend en una nueva ventana
Write-Host "[INFO] Iniciando Backend (puerto 9000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python run_server.py"

# Esperar un poco para que el backend inicie
Start-Sleep -Seconds 3

# Iniciar Frontend en una nueva ventana
Write-Host "[INFO] Iniciando Frontend (puerto 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm start"

Write-Host ""
Write-Host "[OK] Servidores iniciados!" -ForegroundColor Green
Write-Host "  - Backend: http://localhost:9000" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Ctrl+C para detener los servidores" -ForegroundColor Yellow

