#!/bin/sh
# Para el servidor de Puerto Bravo con orden: avisa a los jugadores y lo guarda todo.
cd "$(dirname "$0")" || exit 1
if [ -f servidor.pid ] && kill -0 "$(cat servidor.pid)" 2>/dev/null; then
    kill -TERM "$(cat servidor.pid)"
    for i in 1 2 3 4 5 6 7 8 9 10; do
        kill -0 "$(cat servidor.pid)" 2>/dev/null || break
        sleep 1
    done
    echo "Servidor parado."
else
    echo "El servidor no estaba en marcha."
fi
rm -f servidor.pid
