"""Copias de seguridad de los datos del servidor, y su restauración.

Una copia es un archivo zip con todo lo que hace falta para dejar el servidor como estaba, aquí o en otra máquina:
la base de datos (cuentas, personajes, bandas, territorios, vehículos), el mundo con el que trabajaba, el certificado
con su llave (para que los jugadores no vean un certificado distinto) y la configuración.

Ojo: por llevar la llave del certificado y la configuración, una copia no es para repartir. Guárdala donde solo tú la veas.

Solo usa la biblioteca de serie.
"""
import os
import shutil
import sqlite3
import time
import zipfile

BASE = "puertobravo.db"
CARPETA = "copias"
PREFIJO_AUTO = "copia_auto_"
PREFIJO_MANUAL = "copia_"
# Lo que entra en una copia, además de la base de datos. La configuración entra con el nombre servidor.conf.
ARCHIVOS = ("mundo_actual.json", "certificado.pem", "llave.pem")
PERMITIDOS = (BASE, "servidor.conf") + ARCHIVOS


def carpeta_copias(datos):
    return os.path.join(datos, CARPETA)


def _copiar_base(origen, destino, conexion=None):
    """Copia la base de datos en caliente: vale aunque el servidor esté escribiendo en ella."""
    propia = conexion is None
    if propia:
        conexion = sqlite3.connect(origen)
    try:
        conexion.commit()
        otra = sqlite3.connect(destino)
        try:
            conexion.backup(otra)
        finally:
            otra.close()
    finally:
        if propia:
            conexion.close()


def hacer(datos, conexion=None, conf=None, automatica=False, nombre=None):
    """Hace una copia de seguridad y devuelve su ruta.

    ``conexion`` es la conexión abierta del servidor en marcha, si lo está; así la copia sale coherente.
    ``conf`` es la ruta de servidor.conf, si se quiere guardar también la configuración."""
    destino = carpeta_copias(datos)
    os.makedirs(destino, exist_ok=True)
    nombre = nombre or ((PREFIJO_AUTO if automatica else PREFIJO_MANUAL) + time.strftime("%Y%m%d_%H%M%S") + ".zip")
    ruta = os.path.join(destino, nombre)
    n = 2
    while os.path.exists(ruta):                               # dos copias en el mismo segundo no se pisan
        ruta = os.path.join(destino, "%s_%d.zip" % (nombre[:-4], n))
        n += 1
    temporal_db = ruta + ".db.tmp"
    temporal = ruta + ".tmp"
    try:
        base = os.path.join(datos, BASE)
        hay_base = os.path.exists(base) or conexion is not None
        if hay_base:
            _copiar_base(base, temporal_db, conexion)
        with zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED) as z:
            if hay_base:
                z.write(temporal_db, BASE)
            for a in ARCHIVOS:
                if os.path.exists(os.path.join(datos, a)):
                    z.write(os.path.join(datos, a), a)
            if conf and os.path.exists(conf):
                z.write(conf, "servidor.conf")
        os.replace(temporal, ruta)
    finally:
        for sobra in (temporal_db, temporal):
            try:
                os.remove(sobra)
            except OSError:
                pass
    return ruta


def listar(datos):
    """Las copias que hay, de la más nueva a la más antigua: [(ruta, momento, bytes, automática)]."""
    carpeta = carpeta_copias(datos)
    out = []
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            if nombre.lower().endswith(".zip"):
                ruta = os.path.join(carpeta, nombre)
                try:
                    out.append((ruta, os.path.getmtime(ruta), os.path.getsize(ruta), nombre.startswith(PREFIJO_AUTO)))
                except OSError:
                    continue
    return sorted(out, key=lambda c: c[1], reverse=True)


def podar(datos, conservar):
    """Borra las copias automáticas más antiguas y deja las ``conservar`` más nuevas. Las hechas a mano no se tocan."""
    automaticas = [c for c in listar(datos) if c[3]]
    borradas = 0
    for ruta, _, _, _ in automaticas[max(1, int(conservar)):]:
        try:
            os.remove(ruta)
            borradas += 1
        except OSError:
            pass
    return borradas


def contenido(ruta_zip):
    """Lo que trae una copia: los nombres de sus archivos, o un error con un mensaje claro si no es una copia."""
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            nombres = [n for n in z.namelist() if n in PERMITIDOS]
    except (zipfile.BadZipFile, OSError):
        raise ValueError("Ese archivo no es una copia de seguridad del servidor, o está dañado.")
    if BASE not in nombres:
        raise ValueError("Ese archivo no es una copia de seguridad del servidor: no trae la base de datos.")
    return nombres


def restaurar(ruta_zip, datos, conf=None, con_conf=False):
    """Deja los datos como estaban en la copia. EL SERVIDOR TIENE QUE ESTAR PARADO.

    Antes de tocar nada guarda lo que hay en una copia nueva, por si acaso, y devuelve su ruta junto con lo restaurado:
    (ruta de la copia de lo que había, [archivos restaurados]). La configuración solo se restaura si se pide."""
    nombres = contenido(ruta_zip)
    os.makedirs(datos, exist_ok=True)
    previa = None
    if os.path.exists(os.path.join(datos, BASE)):
        previa = hacer(datos, conf=conf, nombre="antes_de_restaurar_" + time.strftime("%Y%m%d_%H%M%S") + ".zip")
    restaurados = []
    with zipfile.ZipFile(ruta_zip) as z:
        base_tmp = os.path.join(datos, BASE + ".restaurando")
        with z.open(BASE) as origen, open(base_tmp, "wb") as f:
            shutil.copyfileobj(origen, f)
        try:                                                  # que lo que se va a poner sea de verdad una base de datos
            c = sqlite3.connect(base_tmp)
            try:
                c.execute("SELECT COUNT(*) FROM cuentas").fetchone()
            finally:
                c.close()
        except sqlite3.Error:
            os.remove(base_tmp)
            raise ValueError("La base de datos de esa copia está dañada. No se ha cambiado nada.")
        for sobra in (BASE + "-wal", BASE + "-shm", BASE + "-journal"):
            try:
                os.remove(os.path.join(datos, sobra))
            except OSError:
                pass
        os.replace(base_tmp, os.path.join(datos, BASE))
        restaurados.append(BASE)
        for a in ARCHIVOS:
            if a in nombres:
                with z.open(a) as origen, open(os.path.join(datos, a), "wb") as f:
                    shutil.copyfileobj(origen, f)
                restaurados.append(a)
        if con_conf and conf and "servidor.conf" in nombres:
            with z.open("servidor.conf") as origen, open(conf, "wb") as f:
                shutil.copyfileobj(origen, f)
            restaurados.append("servidor.conf")
    return previa, restaurados
