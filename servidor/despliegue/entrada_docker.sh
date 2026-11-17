#!/bin/sh
# Arranque del servidor de Puerto Bravo dentro del contenedor de Docker.
# Si arranca como administrador, deja la carpeta de datos a nombre del usuario sin privilegios (la crea Docker, y si no,
# el servidor no podría escribir en ella), suelta los privilegios y sigue como ese usuario.
if [ "$(id -u)" = "0" ]; then
    chown -R 991:991 /datos 2>/dev/null
    exec setpriv --reuid=991 --regid=991 --clear-groups sh "$0" "$@"
fi
cd /datos || exit 1
# La primera vez escribe un servidor.conf de ejemplo, con todas las opciones explicadas.
[ -f servidor.conf ] || python -m servidor --ejemplo
exec python -m servidor servidor.conf
