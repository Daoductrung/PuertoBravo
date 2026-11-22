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

echo Poniendo al dia los idiomas: cada texto nuevo del juego tiene que estar traducido al ingles antes de compilar...
".venv\Scripts\python.exe" herramientas\i18n\extraer.py
".venv\Scripts\python.exe" herramientas\i18n\fusionar.py --instalar --estricto
if errorlevel 1 (
    echo ERROR: hay textos sin traducir al ingles. Estan en traduccion\en\pendientes: traducelos en traduccion\en\hechos y vuelve a compilar.
    pause
    exit /b 1
)
rem Los demas idiomas (vietnamita...): su catalogo, al dia con lo traducido. Lo que aun no lo esta sale en espanol y queda
rem en traduccion\<idioma>\pendientes para quien lo traduce; no para la compilacion.
for /d %%L in (traduccion\*) do if /i not "%%~nxL"=="en" if exist "%%L\%%~nxL.json" (
    ".venv\Scripts\python.exe" herramientas\i18n\extraer.py --idioma %%~nxL
    ".venv\Scripts\python.exe" herramientas\i18n\fusionar.py --idioma %%~nxL --instalar
)

echo Exportando el mundo para el servidor en linea...
".venv\Scripts\python.exe" herramientas\exportar_mundo_servidor.py
echo Poniendo al dia la guia del servidor con sus opciones y sus ordenes...
".venv\Scripts\python.exe" herramientas\preparar_carpeta_servidor.py --guia
if errorlevel 1 (
    echo ERROR: no se pudo poner al dia la guia del servidor.
    pause
    exit /b 1
)
echo Limpiando la compilacion anterior...
if exist "build" rmdir /s /q "build"
if exist "%D%" rmdir /s /q "%D%"

echo Compilando el juego, el editor de mods y el servidor con cx_Freeze. Tarda unos minutos...
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
rem Los idiomas: el catalogo de cada uno, legible para quien quiera revisar o hacer una traduccion
xcopy /e /i /y /q "data\idiomas" "%D%\data\idiomas" >nul
rem Las voces viajan dentro de data\datos, en voces_puente: el juego, al arrancar, las coloca en data\voces, quita las de
rem la version anterior y borra el puente. Asi llegan igual a una instalacion nueva que a quien actualiza desde cualquier
rem version (el actualizador de la 1.6.0 y la 1.6.1 no copia la carpeta voces), y no viajan dos veces.
if exist "data\voces" xcopy /e /i /y /q "data\voces" "%D%\data\datos\voces_puente" >nul
if exist "%D%\data\datos\voces_puente\propias" rmdir /s /q "%D%\data\datos\voces_puente\propias"
if not exist "%D%\data\voces" mkdir "%D%\data\voces"
rem El generador de voces para los personajes hechos por el jugador: el modelo Phonon de Gradium, sus voces y su licencia
".venv\Scripts\python.exe" herramientas\preparar_phonon.py
if not errorlevel 1 ".venv\Scripts\python.exe" herramientas\preparar_phonon.py --idioma en
if errorlevel 1 (
    echo ERROR: falta el modelo del generador de voces. Mira herramientas\preparar_phonon.py
    pause
    exit /b 1
)
xcopy /e /i /y /q "data\phonon" "%D%\data\phonon" >nul
copy /y "data\phonon\LICENCIA.txt" "%D%\LICENCIA_Phonon_Gradium.txt" >nul
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
if exist "LEEME_en.txt" copy /y "LEEME_en.txt" "%D%\LEEME_en.txt" >nul
if exist "LEEME_vi.txt" copy /y "LEEME_vi.txt" "%D%\LEEME_vi.txt" >nul
if exist "LEEME_pt.txt" copy /y "LEEME_pt.txt" "%D%\LEEME_pt.txt" >nul

echo Preparando la carpeta del servidor: lanzadores, guia, ejemplo de configuracion y lo necesario para otros sistemas...
".venv\Scripts\python.exe" herramientas\preparar_carpeta_servidor.py "%D%"
if errorlevel 1 (
    echo ERROR: la carpeta del servidor no ha quedado completa. Revisa los mensajes de arriba.
    pause
    exit /b 1
)

echo Firmando el mundo para los servidores en linea, si esta la clave de publicar...
".venv\Scripts\python.exe" herramientas\exportar_mundo_servidor.py --firmar "%D%\data\datos"
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

echo Apuntando los componentes que trae el juego, para que no avise de ellos como nuevos...
".venv\Scripts\python.exe" herramientas\publicar_componentes.py de-serie
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
echo   Juego:                %D%\PuertoBravo.exe
echo   Editor de mods:       %D%\EditorMods.exe
echo   Panel del servidor:   %D%\PuertoBravoServidorPanel.exe
echo   Servidor por consola: %D%\PuertoBravoServidor.exe
echo   Todo lo del servidor: %D%\servidor
echo Es portable y esta limpia: puedes comprimirla en un zip y repartirla.
echo Para publicarla como actualizacion, ejecuta publicar.bat
echo Los datos del juego y los mods van protegidos: no se pueden editar con un editor de texto.
echo Tus partidas y opciones siguen en la carpeta data del proyecto, no en la compilacion.
echo.
pause
endlocal
