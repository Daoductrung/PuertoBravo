@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."
rem Compila numpy para procesadores antiguos (sin exigir SSE4.2 ni las demas instrucciones de x86-64-v2).
rem La rueda queda en terceros\numpy_antiguo. Hace falta Visual Studio con las herramientas de C++.
rem Solo hay que repetirlo si cambia la version de numpy o la de Python.
set "NUMPY=2.5.4"
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath`) do set "VS=%%i"
if not exist "%VS%\VC\Auxiliary\Build\vcvars64.bat" (
    echo No se ha encontrado Visual Studio con las herramientas de C++.
    exit /b 1
)
call "%VS%\VC\Auxiliary\Build\vcvars64.bat" >nul
set AR=
set LD=
set LDFLAGS=
if not exist "terceros\numpy_antiguo" mkdir "terceros\numpy_antiguo"
echo Compilando numpy %NUMPY% para procesadores antiguos. Tarda varios minutos.
.venv\Scripts\python.exe -m pip wheel numpy==%NUMPY% --no-binary numpy --no-deps -w terceros\numpy_antiguo ^
    -Csetup-args=-Dcpu-baseline=none -Csetup-args=-Dcpu-dispatch=max -Csetup-args=-Dallow-noblas=true -Csetup-args=-Dblas=none -Csetup-args=-Dlapack=none
if errorlevel 1 (
    echo La compilacion ha fallado.
    exit /b 1
)
echo Hecho. La rueda esta en terceros\numpy_antiguo.
