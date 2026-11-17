@echo off
chcp 65001 >nul
rem Para con orden el servidor que este en marcha con la configuracion de esta carpeta: avisa a los jugadores y lo guarda todo.
rem Sirve sobre todo cuando el servidor arranca solo con Windows y no tiene ventana a la vista.
cd /d "%~dp0"
"..\PuertoBravoServidor.exe" --parar servidor.conf
echo.
pause
