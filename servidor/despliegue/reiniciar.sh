#!/bin/sh
# Reinicia el servidor de Puerto Bravo avisando a los jugadores: les dice que se reinicia para actualizarse, con la
# cuenta atrás de la opción parada_aviso, espera a que sus juegos guarden, lo guarda todo, lo para y lo vuelve a
# arrancar. Los juegos esperan y vuelven a entrar solos, y cada jugador sigue donde estaba.
# Es lo que hay que usar después de sustituir la carpeta servidor por la de una versión nueva.
cd "$(dirname "$0")" || exit 1
if [ -f servidor.pid ] && kill -0 "$(cat servidor.pid)" 2>/dev/null; then
    python3 -m servidor servidor.conf --actualizar || exit 1
    i=0
    while kill -0 "$(cat servidor.pid)" 2>/dev/null; do
        i=$((i + 1))
        if [ "$i" -gt 200 ]; then
            echo "El servidor no termina de pararse. Mira servidor.log"
            exit 1
        fi
        sleep 1
    done
    rm -f servidor.pid
    echo "Servidor parado. Arrancando otra vez."
else
    echo "El servidor no estaba en marcha. Lo arranco."
fi
exec sh arrancar.sh
