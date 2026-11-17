@echo off
rem Abre el panel del servidor de Puerto Bravo: una ventana para arrancarlo, pararlo y administrarlo.
cd /d "%~dp0"
if not exist "..\PuertoBravoServidorPanel.exe" (
    echo No encuentro PuertoBravoServidorPanel.exe en la carpeta del juego.
    pause
    exit /b 1
)
start "" "..\PuertoBravoServidorPanel.exe"
