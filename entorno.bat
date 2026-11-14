@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ============================================================
echo  Puerto Bravo: Ley del Asfalto - Preparar el entorno
echo ============================================================
echo.
echo Este script crea un entorno virtual de Python en la carpeta .venv
echo e instala todo lo necesario para jugar y para compilar el juego.
echo.

set "PY="
py -3.15 --version >nul 2>&1 && set "PY=py -3.15"
if not defined PY py -3.14 --version >nul 2>&1 && set "PY=py -3.14"
if not defined PY py -3.13 --version >nul 2>&1 && set "PY=py -3.13"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
    echo ERROR: no se ha encontrado Python. Instala Python 3.13 o superior desde python.org
    echo y marca la casilla para anadirlo al PATH.
    pause
    exit /b 1
)
echo Usando:
%PY% --version
echo.

if exist ".venv\Scripts\python.exe" (
    echo El entorno .venv ya existe. Se actualizan las dependencias.
) else (
    echo Creando el entorno virtual...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: no se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

echo Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
echo Instalando dependencias. Puede tardar unos minutos...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: fallo al instalar las dependencias. Revisa la conexion a Internet.
    pause
    exit /b 1
)

echo.
echo Entorno listo.
echo   - Para jugar:     jugar.bat
echo   - Para compilar:  compilar.bat
echo   - Para probar:    probar.bat
echo.
pause
endlocal
