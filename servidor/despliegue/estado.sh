#!/bin/sh
# Dice si el servidor está en marcha y enseña lo último que ha dicho.
cd "$(dirname "$0")" || exit 1
if [ -f servidor.pid ] && kill -0 "$(cat servidor.pid)" 2>/dev/null; then
    echo "En marcha, proceso $(cat servidor.pid)."
else
    echo "Parado."
fi
tail -15 servidor.log 2>/dev/null
