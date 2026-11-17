@echo off
chcp 65001 >nul
rem Abre el panel del servidor en linea de Puerto Bravo: una ventana para arrancarlo, pararlo y administrarlo.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo No existe el entorno. Ejecuta primero entorno.bat
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" servidor_panel.py
