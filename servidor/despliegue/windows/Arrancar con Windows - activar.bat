@echo off
chcp 65001 >nul
rem Hace que el servidor de Puerto Bravo arranque solo, minimizado, cada vez que inicies sesion en Windows.
rem Deja un acceso en la carpeta Inicio de tu usuario. No hacen falta permisos de administrador.
cd /d "%~dp0"
if not exist "..\PuertoBravoServidor.exe" (
    echo No encuentro PuertoBravoServidor.exe en la carpeta del juego.
    pause
    exit /b 1
)
if not exist servidor.conf "..\PuertoBravoServidor.exe" --ejemplo
set "INICIO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
for %%I in ("%~dp0..") do set "JUEGO=%%~fI"
> "%INICIO%\Servidor de Puerto Bravo.bat" echo @echo off
>> "%INICIO%\Servidor de Puerto Bravo.bat" echo chcp 65001 ^>nul
>> "%INICIO%\Servidor de Puerto Bravo.bat" echo start "Servidor de Puerto Bravo" /min "%JUEGO%\PuertoBravoServidor.exe" servidor.conf
if exist "%INICIO%\Servidor de Puerto Bravo.bat" (
    echo Hecho. El servidor arrancara solo, minimizado, cada vez que inicies sesion en Windows.
    echo Para pararlo usa el archivo Parar el servidor. Para que deje de arrancar solo usa Arrancar con Windows - quitar.
) else (
    echo No se ha podido dejar el acceso en la carpeta Inicio.
)
echo.
pause
