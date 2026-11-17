"""Actualizaciones del juego.

Cómo funciona:

1. Se lee un archivo pequeño, version.json, de la fuente que el jugador haya elegido en Opciones:
   el servidor del juego, GitHub, las dos (gana la versión más nueva; si una falla se usa la otra)
   o una dirección personalizada.
2. Ese archivo va FIRMADO (Ed25519). La firma se comprueba antes de mirar nada más, venga de donde venga:
   la fuente solo decide de dónde se descarga, no en quién se confía. Sin firma válida no se actualiza.
3. Si la versión es más nueva que la instalada, se descarga el ZIP, se comprueban su tamaño y su SHA-256
   (que también van firmados), y se extrae en una carpeta aparte, rechazando rutas peligrosas.
4. Un pequeño .bat espera a que el juego se cierre, guarda una copia del programa, copia la versión nueva
   y vuelve a abrir el juego. Si algo falla, restaura la copia.

Lo que nunca se toca: partidas, opciones, tu música, tus mods. Solo se admiten direcciones https.
No se envía ningún dato del jugador: son descargas normales.
"""
import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from . import VERSION, ed25519, rutas

NOMBRE_APP = "PuertoBravo"
EJECUTABLE = "PuertoBravo.exe"
URL_SERVIDOR = "https://xebolax.synology.me/PuertoBravo/version.json"
REPOSITORIO_GITHUB = "hxebolax/PuertoBravo"
URL_GITHUB = f"https://github.com/{REPOSITORIO_GITHUB}/releases/latest/download/version.json"
# Claves públicas con las que se aceptan versiones. La privada no está en el juego, ni en el repositorio, ni en el servidor.
CLAVES_PUBLICAS = ("2793c73fefcdb5518570569e41e9ae291373c41126b30d4b3fb99359b09ca23f",)

FUENTES = ("servidor", "github", "ambas", "personalizada")
NOMBRE_FUENTE = {"servidor": "el servidor del juego", "github": "GitHub", "ambas": "el servidor del juego y GitHub", "personalizada": "una dirección personalizada"}
CAMPO_FIRMA = "firma_ed25519"
ARG_TRAS_ACTUALIZAR = "--tras-actualizar"
MAX_MANIFIESTO = 256 * 1024
MAX_DESCARGA = 3 * 1024 ** 3
MAX_EXPANDIDO = 6 * 1024 ** 3
MAX_MIEMBROS = 60000
TIEMPO = 20
# Carpetas del jugador: la actualización no las pisa ni las borra jamás.
INTOCABLES = ("partidas", "config", "mi_musica", "actualizacion", "logs", "ia_local", "propias", "voces_generadas")


class ErrorActualizacion(Exception):
    pass


class ErrorRed(ErrorActualizacion):
    pass


class ErrorFirma(ErrorActualizacion):
    pass


class Cancelado(ErrorActualizacion):
    pass


class Info:
    def __init__(self, version, archivo, sha256, tamano, urls, novedades, fuente):
        self.version = version
        self.archivo = archivo
        self.sha256 = sha256
        self.tamano = tamano
        self.urls = urls
        self.novedades = novedades
        self.fuente = fuente


# ------------------------------------------------------------------ versiones
def clave_version(texto):
    partes = []
    for trozo in str(texto).strip().lstrip("vV").split("."):
        digitos = "".join(c for c in trozo if c.isdigit())
        if not digitos:
            raise ValueError(f"Versión no válida: {texto!r}")
        partes.append(int(digitos))
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes)


def es_mas_nueva(a, b):
    return clave_version(a) > clave_version(b)


# ---------------------------------------------------------------------- firma
def serializar_canonico(manifiesto):
    """Los bytes que se firman: el JSON ordenado, con separadores fijos y sin el campo de la firma."""
    datos = {k: v for k, v in manifiesto.items() if k != CAMPO_FIRMA}
    return json.dumps(datos, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def verificar_firma(manifiesto, claves=None):
    claves = CLAVES_PUBLICAS if claves is None else claves
    firma_b64 = manifiesto.get(CAMPO_FIRMA)
    if not isinstance(firma_b64, str) or not firma_b64:
        raise ErrorFirma("La información de la versión no está firmada.")
    try:
        firma = base64.b64decode(firma_b64, validate=True)
    except ValueError:
        raise ErrorFirma("La firma de la versión está dañada.") from None
    mensaje = serializar_canonico(manifiesto)
    for clave in claves:
        try:
            pub = bytes.fromhex(clave)
        except ValueError:
            continue
        if ed25519.verificar(pub, mensaje, firma):
            return
    raise ErrorFirma("La firma de la versión no es válida. No se actualiza.")


# ------------------------------------------------------------------------ red
def comprobar_url(url):
    p = urllib.parse.urlsplit(str(url))
    if p.scheme != "https" or not p.hostname:
        raise ErrorActualizacion("La dirección tiene que empezar por https.")
    if p.username or p.password:
        raise ErrorActualizacion("La dirección no puede llevar usuario ni contraseña.")


class _SoloHttps(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        comprobar_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def abrir_red(url, tiempo=TIEMPO, desde=0):
    """Abre una dirección https y devuelve el objeto de lectura. Es lo único que toca la red.
    Con `desde`, pide el archivo a partir de ese byte, para seguir una descarga que se cortó."""
    comprobar_url(url)
    abridor = urllib.request.build_opener(_SoloHttps)
    cabeceras = {"User-Agent": "PuertoBravo-Actualizador", "Accept": "*/*"}
    if desde:
        cabeceras["Range"] = f"bytes={int(desde)}-"
    pet = urllib.request.Request(url, headers=cabeceras)
    return abridor.open(pet, timeout=tiempo)


REINTENTOS = 5          # veces que se retoma una descarga cortada, por cada dirección


def _abrir_desde(abrir, url, desde):
    """Abre la descarga para seguirla desde un byte. Devuelve la lectura y el byte por el que empieza de verdad:
    si el servidor no sabe continuar, manda el archivo entero y se empieza de cero."""
    if not desde:
        return abrir(url), 0
    try:
        r = abrir(url, desde=desde)
    except TypeError:
        return abrir(url), 0
    return r, (desde if getattr(r, "status", None) == 206 else 0)


def _leer_manifiesto(url, nombre, abrir):
    try:
        with abrir(url) as r:
            crudo = r.read(MAX_MANIFIESTO + 1)
    except ErrorActualizacion:
        raise
    except urllib.error.HTTPError as e:
        raise ErrorRed(f"Al consultar {nombre}, respondió con el error {e.code}.") from None
    except (OSError, ValueError) as e:
        raise ErrorRed(f"No se pudo conectar con {nombre}. Comprueba la conexión a internet. Si usas AdGuard, un antivirus o un cortafuegos, puede estar bloqueando al juego.") from e
    if len(crudo) > MAX_MANIFIESTO:
        raise ErrorFirma(f"La información de versión de {nombre} es demasiado grande.")
    try:
        m = json.loads(crudo.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError):
        raise ErrorFirma(f"La información de versión de {nombre} está dañada.") from None
    if not isinstance(m, dict):
        raise ErrorFirma(f"La información de versión de {nombre} está dañada.")
    return m


def fuentes_a_consultar(fuente, url_personalizada=""):
    if fuente == "github":
        return [("github", URL_GITHUB)]
    if fuente == "ambas":
        return [("servidor", URL_SERVIDOR), ("github", URL_GITHUB)]
    if fuente == "personalizada":
        url = str(url_personalizada or "").strip()
        if not url:
            raise ErrorActualizacion("Has elegido una dirección personalizada, pero no has escrito ninguna. Escríbela en Opciones, Actualizaciones.")
        comprobar_url(url)
        return [("personalizada", url)]
    return [("servidor", URL_SERVIDOR)]


def _info(m, url_manifiesto, fuente, ambas):
    version = str(m.get("version", ""))
    archivo = str(m.get("file", ""))
    sha = str(m.get("sha256", "")).lower()
    tamano = m.get("size")
    clave_version(version)
    if not archivo or os.path.basename(archivo) != archivo or not archivo.lower().endswith(".zip"):
        raise ErrorFirma("El nombre del archivo de la versión no es válido.")
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ErrorFirma("La huella del archivo de la versión no es válida.")
    if not isinstance(tamano, int) or isinstance(tamano, bool) or not 0 < tamano <= MAX_DESCARGA:
        raise ErrorFirma("El tamaño del archivo de la versión no es válido.")
    junto = urllib.parse.urljoin(url_manifiesto, urllib.parse.quote(archivo))
    principal = str(m.get("url") or "")
    espejos = m.get("espejos") if isinstance(m.get("espejos"), dict) else {}
    github = str(espejos.get("github") or "")
    if fuente == "github":
        orden = [github or junto] + ([principal] if ambas else [])
    elif fuente == "personalizada":
        orden = [junto, principal, github]          # el ZIP junto al version.json; si no está, las direcciones firmadas
    else:
        orden = [principal or junto] + ([github] if ambas else [])
    urls = []
    for u in orden:
        if u and u not in urls:
            try:
                comprobar_url(u)
                urls.append(u)
            except ErrorActualizacion:
                pass
    if not urls:
        raise ErrorFirma("La versión no indica de dónde descargarla.")
    return Info(version, archivo, sha, tamano, urls, str(m.get("novedades") or ""), fuente)


def comprobar(fuente="servidor", url_personalizada="", abrir=None, claves=None, version_actual=None):
    """Consulta la fuente elegida. Devuelve la Info de la versión nueva, o None si ya tienes la última."""
    abrir = abrir or abrir_red
    actual = version_actual or VERSION
    lista = fuentes_a_consultar(fuente if fuente in FUENTES else "servidor", url_personalizada)
    ambas = len(lista) > 1
    encontradas, errores = [], []
    for nombre, url in lista:
        donde = NOMBRE_FUENTE[nombre]
        try:
            m = _leer_manifiesto(url, donde, abrir)
            verificar_firma(m, claves)                 # antes de mirar ningún otro campo
            encontradas.append(_info(m, url, nombre, ambas))
        except ErrorActualizacion as e:
            errores.append(e)
        except ValueError as e:
            errores.append(ErrorFirma(str(e)))
    if not encontradas:
        if len(errores) > 1:
            grave = next((e for e in errores if isinstance(e, ErrorFirma)), errores[0])
            raise type(grave)("No se pudo comprobar en ninguna de las dos fuentes. " + " ".join(str(e) for e in errores))
        raise errores[0]
    mejor = max(encontradas, key=lambda i: clave_version(i.version))
    return mejor if es_mas_nueva(mejor.version, actual) else None


# ------------------------------------------------------------------- descarga
def carpeta_trabajo():
    return os.path.join(rutas.DATA, "actualizacion")


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def descargar(info, carpeta=None, progreso=None, cancelado=None, abrir=None):
    """Descarga el ZIP probando las direcciones en orden y comprueba tamaño y SHA-256. Devuelve su ruta."""
    abrir = abrir or abrir_red
    carpeta = carpeta or carpeta_trabajo()
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, info.archivo)
    ultimo = None
    for url in info.urls:
        try:
            hecho = 0
            # Si la conexión se corta a medias, no se empieza otra vez: se retoma por donde iba, varias veces.
            for intento in range(REINTENTOS + 1):
                antes = hecho
                try:
                    r, hecho = _abrir_desde(abrir, url, hecho)
                    with r, open(destino + ".parcial", "ab" if hecho else "wb") as f:
                        while True:
                            if cancelado and cancelado():
                                raise Cancelado("Descarga cancelada.")
                            bloque = r.read(256 * 1024)
                            if not bloque:
                                break
                            hecho += len(bloque)
                            if hecho > info.tamano:
                                raise ErrorFirma("El archivo descargado es más grande de lo que debería.")
                            f.write(bloque)
                            if progreso:
                                progreso(hecho, info.tamano)
                except (OSError, ValueError):
                    if intento == REINTENTOS or (hecho <= antes and intento >= 2):       # ni avanza: no insistir más con esta dirección
                        raise
                    time.sleep(min(4.0, 0.5 * (intento + 1)) if abrir is abrir_red else 0)
                    continue
                if hecho >= info.tamano or (hecho <= antes and intento >= 2):
                    break
            if hecho != info.tamano:
                raise ErrorRed("La descarga se ha cortado antes de terminar, y no se ha podido retomar. Prueba otra vez dentro de un rato.")
            if not hmac.compare_digest(sha256_de(destino + ".parcial"), info.sha256):
                raise ErrorFirma("El archivo descargado no coincide con el que se publicó. No se instala.")
            os.replace(destino + ".parcial", destino)
            return destino
        except Cancelado:
            _quitar(destino + ".parcial")
            raise
        except ErrorActualizacion as e:
            ultimo = e
        except (OSError, ValueError) as e:
            ultimo = ErrorRed("No se pudo descargar la versión nueva. Comprueba la conexión a internet.")
            ultimo.__cause__ = e
        _quitar(destino + ".parcial")
    raise ultimo or ErrorRed("No se pudo descargar la versión nueva.")


def _quitar(ruta):
    try:
        os.remove(ruta)
    except OSError:
        pass


def extraer(ruta_zip, carpeta):
    """Extrae el ZIP en una carpeta vacía, rechazando cualquier ruta que intente salirse de ella."""
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta, ignore_errors=True)
    os.makedirs(carpeta)
    raiz = os.path.realpath(carpeta)
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            miembros = z.infolist()
            if len(miembros) > MAX_MIEMBROS or sum(m.file_size for m in miembros) > MAX_EXPANDIDO:
                raise ErrorFirma("El paquete de la versión es demasiado grande.")
            for m in miembros:
                nombre = m.filename.replace("\\", "/")
                partes = [p for p in nombre.split("/") if p]
                if nombre.startswith("/") or ":" in nombre or ".." in partes or (m.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ErrorFirma("El paquete de la versión contiene rutas no permitidas. No se instala.")
                destino = os.path.realpath(os.path.join(raiz, *partes))
                if destino != raiz and not destino.startswith(raiz + os.sep):
                    raise ErrorFirma("El paquete de la versión contiene rutas no permitidas. No se instala.")
                if m.is_dir():
                    os.makedirs(destino, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with z.open(m) as origen, open(destino, "wb") as f:
                    shutil.copyfileobj(origen, f, 1024 * 1024)
    except zipfile.BadZipFile:
        raise ErrorFirma("El paquete de la versión está dañado.") from None
    if not os.path.isfile(os.path.join(raiz, EJECUTABLE)):
        raise ErrorFirma("El paquete de la versión no contiene el juego.")
    for base, dirs, _ in os.walk(raiz):               # por si acaso: lo personal no viaja en una versión
        for d in list(dirs):
            if d in INTOCABLES and os.path.basename(base) in ("data", "radio"):
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)
                dirs.remove(d)
    return raiz


# ----------------------------------------------------------------- instalación
def puede_instalar():
    """Solo el juego compilado se sustituye a sí mismo. Desde el código fuente se puede comprobar y avisar."""
    return bool(getattr(sys, "frozen", False))


def carpeta_programa():
    return os.path.dirname(os.path.abspath(sys.executable)) if puede_instalar() else rutas.base()


def escribir_instalador(nueva, programa=None, pid=None, version=""):
    """Escribe el .bat que sustituye el programa cuando el juego se haya cerrado. Devuelve su ruta."""
    programa = programa or carpeta_programa()
    pid = os.getpid() if pid is None else pid
    for ruta in (nueva, programa):
        if any(c in ruta for c in '%"!^&'):
            raise ErrorActualizacion("El juego está en una carpeta con símbolos especiales en el nombre y no se puede actualizar solo. Descarga la versión nueva a mano.")
    trabajo = os.path.dirname(nueva)
    copia = os.path.join(trabajo, "anterior")
    excluir = " ".join(INTOCABLES)
    lineas = [
        "@echo off", "chcp 65001 >nul", "setlocal",
        f'set "APP={programa}"', f'set "NUEVA={nueva}"', f'set "COPIA={copia}"',
        f"echo Actualizando Puerto Bravo a la version {version}. No cierres esta ventana.",
        "set /a N=0", ":espera",
        f'tasklist /fi "PID eq {pid}" 2>nul | find " {pid} " >nul',
        "if errorlevel 1 goto servidor",
        "set /a N+=1", "if %N% geq 90 goto abrir",
        "ping -n 2 127.0.0.1 >nul", "goto espera",
        # Si el servidor en línea de esta misma carpeta está en marcha, sus programas no se pueden sustituir: se espera a
        # que se cierre, y si no se cierra, no se actualiza a medias.
        ":servidor",
        'tasklist /fi "IMAGENAME eq PuertoBravoServidor.exe" 2>nul | find /i "PuertoBravoServidor" >nul',
        "if not errorlevel 1 goto ocupado",
        'tasklist /fi "IMAGENAME eq PuertoBravoServidorPanel.exe" 2>nul | find /i "PuertoBravoServidor" >nul',
        "if errorlevel 1 goto copiar",
        ":ocupado",
        "if %N%==0 echo El servidor en linea de Puerto Bravo esta abierto. Paralo y cierra su panel para seguir con la actualizacion.",
        "set /a N+=1", "if %N% geq 180 goto abrir",
        "ping -n 2 127.0.0.1 >nul", "goto servidor",
        ":copiar",
        'if exist "%COPIA%" rmdir /s /q "%COPIA%"',
        'robocopy "%APP%" "%COPIA%" /e /xd "%APP%\\data" /r:2 /w:1 /njh /njs /ndl /nfl >nul',
        'robocopy "%APP%\\data\\datos" "%COPIA%\\data\\datos" /e /r:2 /w:1 /njh /njs /ndl /nfl >nul',
        'robocopy "%APP%\\data\\mods" "%COPIA%\\data\\mods" /e /r:2 /w:1 /njh /njs /ndl /nfl >nul',
        'robocopy "%APP%\\data\\docs" "%COPIA%\\data\\docs" /e /r:2 /w:1 /njh /njs /ndl /nfl >nul',
        f'robocopy "%NUEVA%" "%APP%" /e /xd {excluir} /r:3 /w:1 /njh /njs /ndl /nfl >nul',
        "if errorlevel 8 goto fallo",
        'if exist "%NUEVA%\\lib" robocopy "%NUEVA%\\lib" "%APP%\\lib" /mir /r:3 /w:1 /njh /njs /ndl /nfl >nul',
        "if errorlevel 8 goto fallo",
        'if exist "%NUEVA%\\data\\datos" robocopy "%NUEVA%\\data\\datos" "%APP%\\data\\datos" /mir /r:3 /w:1 /njh /njs /ndl /nfl >nul',
        "if errorlevel 8 goto fallo",
        'if exist "%APP%\\data\\voces_serie" rmdir /s /q "%APP%\\data\\voces_serie"',     # las voces van ahora en data\voces
        'rmdir /s /q "%NUEVA%"',
        'rmdir /s /q "%COPIA%"',
        f'start "" "%APP%\\{EJECUTABLE}" {ARG_TRAS_ACTUALIZAR}',
        "goto fin",
        ":fallo",
        "echo La actualizacion ha fallado. Se restaura la version anterior.",
        'robocopy "%COPIA%" "%APP%" /e /r:3 /w:1 /njh /njs /ndl /nfl >nul',
        ":abrir",
        f'start "" "%APP%\\{EJECUTABLE}" --actualizacion-fallida',
        ":fin",
        "endlocal",
        '(goto) 2>nul & del "%~f0"',
    ]
    ruta = os.path.join(trabajo, "instalar_actualizacion.bat")
    with open(ruta, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    return ruta


PROGRAMAS_SERVIDOR = ("PuertoBravoServidor.exe", "PuertoBravoServidorPanel.exe")


def servidor_abierto():
    """¿Está en marcha el servidor en línea, o su panel? Con ellos abiertos no se pueden sustituir sus programas."""
    try:
        sin_ventana = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        salida = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=10, creationflags=sin_ventana).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False
    return any('"%s"' % nombre.lower() in salida for nombre in PROGRAMAS_SERVIDOR)


def lanzar_instalador(ruta_bat):
    """Arranca el instalador en su propia consola, pero escondida: no se ve ninguna ventana mientras se actualiza."""
    banderas = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    info = None
    if hasattr(subprocess, "STARTUPINFO"):
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0                                      # SW_HIDE
    subprocess.Popen(["cmd.exe", "/c", ruta_bat], cwd=os.path.dirname(ruta_bat), creationflags=banderas, close_fds=True, startupinfo=info)


def limpiar():
    """Borra los restos de una actualización ya instalada o abandonada."""
    shutil.rmtree(carpeta_trabajo(), ignore_errors=True)
