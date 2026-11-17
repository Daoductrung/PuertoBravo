@echo off
chcp 65001 >nul
title Servidor de Puerto Bravo
rem Arranca el servidor de Puerto Bravo en esta ventana. Se le escriben ordenes: ayuda las dice todas.
rem Para pararlo escribe apagar, pulsa Control+C o cierra la ventana: en los tres casos lo guarda todo.
cd /d "%~dp0"
if not exist "..\PuertoBravoServidor.exe" (
    echo No encuentro PuertoBravoServidor.exe en la carpeta del juego.
    pause
    exit /b 1
)
if not exist servidor.conf "..\PuertoBravoServidor.exe" --ejemplo
"..\PuertoBravoServidor.exe" servidor.conf
echo.
pause
