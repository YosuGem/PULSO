@echo off
REM Launcher de Noósfera v_prueba (solo localhost 127.0.0.1)
setlocal
cd /d "%~dp0"
set NOOSFERA_API_KEY=noosfera_local_prueba_2026
set NOOSFERA_PUERTO=8080
set NOOSFERA_HOST=127.0.0.1
echo Iniciando Noósfera en http://localhost:8080 (CTRL+C para detener)
python noosfera.py --server 8080
endlocal
