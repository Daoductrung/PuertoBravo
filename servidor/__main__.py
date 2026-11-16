"""Arranque del servidor en línea de Puerto Bravo.

    python -m servidor                      con servidor.conf de la carpeta actual, si existe
    python -m servidor mi_servidor.conf     con otro archivo de configuración
    python -m servidor --ejemplo            escribe un servidor.conf de ejemplo y sale

Mientras funciona, se le pueden escribir órdenes: ayuda las dice todas.
"""
import asyncio
import os
import signal
import sys
import threading
import time

from .nucleo import CONFIG, Servidor, leer_config

EJEMPLO = """# Servidor en línea de Puerto Bravo: Ley del Asfalto
# Una opción por línea: nombre = valor. Las líneas que empiezan por almohadilla no cuentan.

# Cómo se llama tu servidor y qué se le dice a quien entra.
nombre = Servidor de Puerto Bravo
bienvenida = Bienvenido. Juega limpio.

# Puerto en el que escucha. Hay que abrirlo en el router si quieres que entren desde fuera de casa.
puerto = 47820
max_jugadores = 32

# Quién puede crear un personaje: abierta, clave o invitacion.
#   abierta: cualquiera que tenga la dirección.
#   clave: hay que saber la contraseña de entrada.
#   invitacion: hace falta un código de un solo uso. Se crean con la orden invitar.
entrada = abierta
clave =

# Dónde se guarda todo: personajes, bandas, territorios y vehículos.
datos = datos_servidor

# Cifrado de la conexión: auto, si o no. Con auto, el servidor crea su propio certificado la primera vez que arranca.
# No hace falta instalar nada, tampoco en Windows.
cifrado = auto

# Reglas del combate entre jugadores.
pvp = si
zonas_seguras = si
modo_pasivo = si
proteccion = 20
botin = 10
botin_max = 5000
# Atracar a otro jugador: el tanto por ciento de lo que lleva encima que se le quita, y su tope.
atraco = 15
atraco_max = 1000
# Atracar el negocio de otro jugador: los segundos que hay que aguantar en la puerta. Al dueño le salta el aviso.
robo_segundos = 20

# Personajes que lleva el servidor y que son los mismos para todos: paseantes, rateros, pistoleros, ladrones de coches
# y atracadores de negocios. Salen al azar, solo donde hay jugadores. Con 0, ninguno.
personajes = 6

# Casas y negocios: lo que recupera quien vende al mercado, en tanto por ciento, y los días de reloj sin entrar
# tras los que las propiedades de un jugador vuelven a estar en venta.
venta_mercado = 70
propiedad_dias = 30
recompensa = 500

# Contenido para adultos. Con no, quien entra juega sin él aunque lo tenga activado en su juego.
adultos = no

# Bandas y territorios. Los minutos son minutos de reloj, de los de verdad.
precio_banda = 2000
precio_barrio = 3000
renta_barrio = 300
precio_guerra = 1000
guerra_espera = 20
guerra_dura = 10

# Vehículos dejados en la calle: cuántas horas siguen ahí y cuántos puede tener aparcados cada jugador.
vehiculos_horas = 12
vehiculos_por_jugador = 3

# Administradores, por su nombre de jugador, separados por comas. Con primer_admin, lo es la primera cuenta que entra.
admins =
primer_admin = si

# El mundo del juego (lugares, armas, misiones) no va atado al servidor: se lo da el juego de quien entra.
# Cuando sale una versión nueva del juego, el primero que entra con ella se lo trae, y el servidor sigue sin tocarlo.
#   firmado: se acepta de cualquiera, si lo firma quien publica el juego. Es lo de serie y lo seguro.
#   admin: además, sin firma, de un administrador. Para servidores con mods.
#   no: nunca; el servidor se queda con el mundo que tiene.
actualizar_mundo = firmado

# Anotar en la pantalla la dirección de quien se conecta. De serie, no.
registro_ip = no
"""


def _hora():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    if "--ejemplo" in args:
        if os.path.exists("servidor.conf"):
            print("Ya hay un servidor.conf en esta carpeta. No lo toco.")
            return 1
        with open("servidor.conf", "w", encoding="utf-8", newline="\n") as f:
            f.write(EJEMPLO)
        print("Escrito servidor.conf. Ábrelo con un editor de texto, cámbialo a tu gusto y arranca el servidor.")
        return 0
    ruta = next((a for a in args if not a.startswith("--")), "servidor.conf")
    cfg = leer_config(ruta)
    for a in args:                                           # también valen opciones sueltas: --puerto=47821
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            if k in CONFIG:
                cfg[k] = int(v) if isinstance(CONFIG[k], int) else v
    srv = Servidor(cfg)
    srv.log = lambda t: print("%s  %s" % (_hora(), t), flush=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(srv.iniciar())
    except OSError as e:
        print("No se pudo abrir el puerto %s: %s" % (cfg["puerto"], e))
        return 2
    except RuntimeError as e:
        print(str(e))
        return 2
    if not os.path.exists(ruta):
        srv.log("No hay archivo de configuración: uso los valores de serie. Con --ejemplo se escribe uno.")
    srv.log("Datos del mundo: versión %s, huella %s. %d localidades." % (srv.mundo.get("version"), srv.mundo.get("huella"), len(srv.mundo["mapas"])))
    if srv.huella_cert:
        srv.log("Huella del certificado: %s" % srv.huella_cert)
    srv.log("Escribe ayuda para ver las órdenes.")

    def consola():
        try:
            for linea in sys.stdin:
                linea = linea.strip()
                if linea:
                    loop.call_soon_threadsafe(lambda t=linea: print(srv.orden(t), flush=True))
        except Exception:
            pass
    threading.Thread(target=consola, daemon=True).start()

    def parar(*_):
        loop.call_soon_threadsafe(lambda: loop.create_task(srv.detener()))
    for s in (signal.SIGINT, getattr(signal, "SIGTERM", None)):
        if s is not None:
            try:
                signal.signal(s, parar)
            except (ValueError, OSError):
                pass

    async def esperar():
        while srv.activo:
            await asyncio.sleep(0.5)
        await asyncio.sleep(0.3)
    try:
        loop.run_until_complete(esperar())
    except KeyboardInterrupt:
        loop.run_until_complete(srv.detener())
    print("%s  Servidor parado. Todo guardado." % _hora(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
