@echo off
rem Arranca el servidor en linea de Puerto Bravo en este ordenador. Se para con Control C.
cd /d "%~dp0"
if not exist servidor.conf .venv\Scripts\python.exe -m servidor --ejemplo
.venv\Scripts\python.exe -m servidor servidor.conf
pause
