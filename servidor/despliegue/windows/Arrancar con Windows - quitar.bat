@echo off
chcp 65001 >nul
rem Hace que el servidor de Puerto Bravo deje de arrancar solo al iniciar sesion en Windows.
rem No para el servidor si esta en marcha: para eso esta el archivo Parar el servidor.
set "INICIO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%INICIO%\Servidor de Puerto Bravo.bat" (
    del "%INICIO%\Servidor de Puerto Bravo.bat"
    echo Hecho. El servidor ya no arrancara solo con Windows.
) else (
    echo El servidor no estaba puesto para arrancar solo con Windows.
)
echo.
pause
