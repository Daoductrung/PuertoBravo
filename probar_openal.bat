@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Probando la biblioteca de sonido OpenAL Soft...
echo.
.venv\Scripts\python.exe herramientas\probar_openal.py
echo.
echo El resultado queda guardado en adjuntos\prueba_openal.txt
pause
