@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ============================================================
echo  Puerto Bravo: Ley del Asfalto - Compilar con cx_Freeze
echo ============================================================
echo.
if not exist ".venv\Scripts\python.exe" (
    echo No existe el entorno. Ejecuta primero entorno.bat
    pause
    exit /b 1
)

set "D=dist\PuertoBravo"

echo La compilacion sale LIMPIA para distribuir: sin partidas, sin opciones y sin musica personal.
if exist "%D%\data\partidas\*.json" (
    echo Habia partidas en la compilacion anterior. Se copian a data\partidas del proyecto, sin pisar las que ya tengas...
    robocopy "%D%\data\partidas" "data\partidas" /e /xc /xn /xo /njh /njs /ndl /nfl >nul
)
if exist "%D%\data\config\*.json" (
    if not exist "data\config\config.json" robocopy "%D%\data\config" "data\config" /e /xc /xn /xo /njh /njs /ndl /nfl >nul
)

echo Poniendo al dia los mods de ejemplo...
".venv\Scripts\python.exe" herramientas\crear_mods_ejemplo.py
echo Generando los sonidos, la musica y la documentacion que falten en data...
".venv\Scripts\python.exe" herramientas\generar_datos.py
if errorlevel 1 (
    echo ERROR: no se pudieron generar los datos.
    pause
    exit /b 1
)

echo Limpiando la compilacion anterior...
if exist "build" rmdir /s /q "build"
if exist "%D%" rmdir /s /q "%D%"

echo Compilando el juego y el editor de mods con cx_Freeze. Tarda unos minutos...
".venv\Scripts\python.exe" setup_cx.py build_exe
if errorlevel 1 (
    echo.
    echo ERROR: la compilacion ha fallado. Revisa los mensajes de arriba.
    pause
    exit /b 1
)

echo Copiando la carpeta data junto a los ejecutables...
xcopy /e /i /y /q "data\datos" "%D%\data\datos" >nul
xcopy /e /i /y /q "data\docs" "%D%\data\docs" >nul
if exist "data\voces_serie" xcopy /e /i /y /q "data\voces_serie" "%D%\data\voces_serie" >nul
xcopy /e /i /y /q "data\sonidos" "%D%\data\sonidos" >nul
xcopy /e /i /y /q "data\musica" "%D%\data\musica" >nul
xcopy /i /y /q "data\radio\*.*" "%D%\data\radio" >nul
if not exist "%D%\data\config" mkdir "%D%\data\config"
if not exist "%D%\data\partidas" mkdir "%D%\data\partidas"
if not exist "%D%\data\mods" mkdir "%D%\data\mods"
if not exist "%D%\data\radio\mi_musica" mkdir "%D%\data\radio\mi_musica"
if exist "data\mods\LEEME*.txt" copy /y "data\mods\LEEME*.txt" "%D%\data\mods" >nul
if exist "data\mods\costa_dorada.json" copy /y "data\mods\costa_dorada.json" "%D%\data\mods" >nul
if exist "data\mods\oficios_y_recados.json" copy /y "data\mods\oficios_y_recados.json" "%D%\data\mods" >nul
if exist "data\mods\valdeolmos.json" copy /y "data\mods\valdeolmos.json" "%D%\data\mods" >nul
if exist "data\mods\motor_y_asfalto.json" copy /y "data\mods\motor_y_asfalto.json" "%D%\data\mods" >nul
if exist "data\mods\penas_altas.json" copy /y "data\mods\penas_altas.json" "%D%\data\mods" >nul
if exist "data\mods\isla_de_los_vientos.json" copy /y "data\mods\isla_de_los_vientos.json" "%D%\data\mods" >nul
if exist "data\mods\noches_de_neon.json" copy /y "data\mods\noches_de_neon.json" "%D%\data\mods" >nul
if exist "data\mods\bahia_del_ocaso.json" copy /y "data\mods\bahia_del_ocaso.json" "%D%\data\mods" >nul
if exist "LEEME.txt" copy /y "LEEME.txt" "%D%\LEEME.txt" >nul

echo Protegiendo los datos del juego y los mods...
".venv\Scripts\python.exe" herramientas\cifrar_datos.py "%D%\data"
if errorlevel 1 (
    echo ERROR: no se pudieron proteger los datos.
    pause
    exit /b 1
)

echo Copiando la biblioteca del motor de sonido envolvente...
if exist "terceros\openal_soft\soft_oal.dll" (
    copy /y "terceros\openal_soft\soft_oal.dll" "%D%\lib\soft_oal.dll" >nul
    copy /y "terceros\openal_soft\LICENCIA_OpenAL_Soft.txt" "%D%\LICENCIA_OpenAL_Soft.txt" >nul
)

echo Poniendo la biblioteca para procesadores antiguos...
".venv\Scripts\python.exe" herramientas\poner_numpy_antiguo.py "%D%"
if errorlevel 1 (
    echo ERROR: falta la biblioteca para procesadores antiguos. Ejecuta herramientas\compilar_numpy_antiguo.bat
    pause
    exit /b 1
)

echo Comprobando que la compilacion esta limpia...
".venv\Scripts\python.exe" herramientas\comprobar_limpio.py "%D%"
if errorlevel 1 (
    echo ERROR: la compilacion contiene datos personales o le falta algo. Revisa los mensajes de arriba.
    pause
    exit /b 1
)

if exist "build" rmdir /s /q "build"
if exist "PuertoBravo.egg-info" rmdir /s /q "PuertoBravo.egg-info"

echo.
echo Compilacion terminada.
echo La carpeta para distribuir es %D%
echo   Juego:           %D%\PuertoBravo.exe
echo   Editor de mods:  %D%\EditorMods.exe
echo Es portable y esta limpia: puedes comprimirla en un zip y repartirla.
echo Para publicarla como actualizacion, ejecuta publicar.bat
echo Los datos del juego y los mods van protegidos: no se pueden editar con un editor de texto.
echo Tus partidas y opciones siguen en la carpeta data del proyecto, no en la compilacion.
echo.
pause
endlocal
