@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo No existe el entorno. Ejecuta primero entorno.bat
    pause
    exit /b 1
)
echo Ejecutando las pruebas automaticas. Tardan alrededor de un minuto...
".venv\Scripts\python.exe" -m pytest pruebas -q
echo.
pause
