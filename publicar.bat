@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ============================================================
echo  Puerto Bravo: Ley del Asfalto - Publicar una version
echo ============================================================
echo.
if not exist "dist\PuertoBravo\PuertoBravo.exe" (
    echo No hay juego compilado. Ejecuta primero compilar.bat
    pause
    exit /b 1
)
if not exist "herramientas\claves\firma_ed25519.key" (
    echo No hay clave de firma. Se crea con:
    echo   .venv\Scripts\python.exe herramientas\publicar.py clave
    pause
    exit /b 1
)
echo Se comprime dist\PuertoBravo, se firma version.json y se copian los dos archivos
echo a la carpeta escrita en publicar_destino.txt, si existe.
echo.
".venv\Scripts\python.exe" herramientas\publicar.py publicar %*
if errorlevel 1 (
    echo.
    echo ERROR: no se ha publicado. Revisa los mensajes de arriba.
    pause
    exit /b 1
)
echo.
pause
endlocal
