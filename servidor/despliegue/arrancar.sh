#!/bin/sh
# Arranca el servidor de Puerto Bravo en segundo plano, si no está ya en marcha.
# Se puede poner en el Programador de tareas del NAS, como tarea de arranque, con tu usuario.
cd "$(dirname "$0")" || exit 1
if [ -f servidor.pid ] && kill -0 "$(cat servidor.pid)" 2>/dev/null; then
    echo "El servidor ya está en marcha, con el proceso $(cat servidor.pid)."
    exit 0
fi
[ -f servidor.conf ] || python3 -m servidor --ejemplo
nohup python3 -m servidor servidor.conf >> servidor.log 2>&1 < /dev/null &
echo $! > servidor.pid
sleep 2
if kill -0 "$(cat servidor.pid)" 2>/dev/null; then
    echo "Servidor arrancado, proceso $(cat servidor.pid). Lo que va diciendo está en servidor.log"
else
    echo "El servidor no ha arrancado. Mira servidor.log"
    tail -5 servidor.log
    exit 1
fi
