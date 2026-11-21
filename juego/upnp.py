"""Abrir el puerto del router automáticamente para jugar con amigos de fuera de casa.

Casi todos los routers domésticos aceptan que un programa de la red les pida abrir un puerto (el mecanismo se
llama UPnP). Si el router lo permite, el jugador no tiene que entrar en su configuración. Si no lo permite o
lo tiene desactivado, no pasa nada: el juego lo dice y queda la manera manual, que explica el manual.

Solo se habla con el router de la propia red, y solo cuando el jugador abre su partida a los amigos. Al cerrar
la partida se le pide que vuelva a cerrar el puerto.
"""
from .i18n import tr
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

SSDP = ("239.255.255.250", 1900)
SERVICIOS = ("urn:schemas-upnp-org:service:WANIPConnection:1", "urn:schemas-upnp-org:service:WANIPConnection:2",
             "urn:schemas-upnp-org:service:WANPPPConnection:1")


def descubrir(espera=2.0):
    """Pregunta a la red quién es el router. Devuelve las direcciones de la descripción de cada uno que responda."""
    vistos = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(espera)
        for st in ("urn:schemas-upnp-org:device:InternetGatewayDevice:1", "urn:schemas-upnp-org:device:InternetGatewayDevice:2"):
            s.sendto(('M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: {st}\r\n\r\n'.format(st=(st))).encode("ascii"), SSDP)
        while True:
            try:
                datos, _ = s.recvfrom(4096)
            except (socket.timeout, OSError):
                break
            m = re.search(r"^location:\s*(\S+)", datos.decode("utf-8", "replace"), re.I | re.M)
            if m and m.group(1) not in vistos:
                vistos.append(m.group(1))
    except OSError:
        pass
    finally:
        s.close()
    return vistos


def _leer(que, espera, tope):
    """Lee una respuesta del router. Los routers domésticos cortan a veces la primera conexión: se intenta hasta tres veces."""
    for intento in range(4):
        try:
            with urllib.request.urlopen(que, timeout=espera) as r:
                return r.read(tope).decode("utf-8", "replace")
        except (ConnectionError, socket.timeout, urllib.error.URLError) as e:
            # el corte puede llegar tal cual o envuelto por urllib; un «no existe» de verdad (404, 500) no se reintenta
            if isinstance(e, urllib.error.HTTPError) or (isinstance(e, urllib.error.URLError) and not isinstance(e.reason, (ConnectionError, socket.timeout, OSError))):
                raise
            if intento == 3:
                raise
            time.sleep(0.2)


def servicio(descripcion_url, espera=3.0):
    """Lee la descripción del router y devuelve (dirección de control, tipo de servicio), o None si no ofrece abrir puertos."""
    xml = _leer(descripcion_url, espera, 200000)
    for bloque in re.findall(r"<service>(.*?)</service>", xml, re.S):
        tipo = re.search(r"<serviceType>\s*(.*?)\s*</serviceType>", bloque, re.S)
        control = re.search(r"<controlURL>\s*(.*?)\s*</controlURL>", bloque, re.S)
        if tipo and control and tipo.group(1) in SERVICIOS:
            return urllib.parse.urljoin(descripcion_url, control.group(1)), tipo.group(1)
    return None


def _pedir(control, tipo, accion, campos, espera=4.0):
    cuerpo = "".join(f"<{k}>{v}</{k}>" for k, v in campos)
    sobre = (tr('<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:{accion} xmlns:u="{tipo}">{cuerpo}</u:{accion}></s:Body></s:Envelope>').format(accion=(accion), tipo=(tipo), cuerpo=(cuerpo)))
    pet = urllib.request.Request(control, data=sobre.encode("utf-8"), method="POST",
                                 headers={"Content-Type": tr('text/xml; charset="utf-8"'), "SOAPAction": f'"{tipo}#{accion}"'})
    return _leer(pet, espera, 100000)


def ip_local_hacia(url):
    """La dirección de este ordenador en la red por la que se llega al router."""
    host = urllib.parse.urlparse(url).hostname
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, 9))
        return s.getsockname()[0]
    finally:
        s.close()


def abrir(puerto, descripcion=tr("Puerto Bravo"), buscar=descubrir):
    """Intenta abrir el puerto en el router. Devuelve (conseguido, datos para cerrarlo después o None, motivo si falla)."""
    try:
        routers = buscar()
    except Exception:
        routers = []
    if not routers:
        return False, None, "no_responde"
    motivo = "no_permite"
    for url in routers:
        try:
            s = servicio(url)
            if s is None:
                continue
            control, tipo = s
            mia = ip_local_hacia(control)
            _pedir(control, tipo, "AddPortMapping", [("NewRemoteHost", ""), ("NewExternalPort", int(puerto)), ("NewProtocol", "TCP"),
                                                     ("NewInternalPort", int(puerto)), ("NewInternalClient", mia), ("NewEnabled", 1),
                                                     ("NewPortMappingDescription", descripcion), ("NewLeaseDuration", 0)])
            return True, {"control": control, "tipo": tipo, "puerto": int(puerto)}, ""
        except Exception:
            motivo = "rechazado"
    return False, None, motivo


def cerrar(datos):
    """Pide al router que cierre el puerto que se abrió. Si falla, no pasa nada."""
    if not datos:
        return False
    try:
        _pedir(datos["control"], datos["tipo"], "DeletePortMapping", [("NewRemoteHost", ""), ("NewExternalPort", datos["puerto"]), ("NewProtocol", "TCP")])
        return True
    except Exception:
        return False


FRASES = {
    "": tr("He abierto el puerto en tu router: tus amigos de fuera de casa ya pueden entrar con la dirección de internet."),
    "no_responde": tr("No he podido abrir el puerto del router yo solo: el router no responde a la petición. Tus amigos de casa pueden entrar; para los de fuera, el manual explica cómo abrirlo a mano."),
    "no_permite": tr("No he podido abrir el puerto del router yo solo: tu router no lo permite. Para los amigos de fuera de casa, el manual explica cómo abrirlo a mano."),
    "rechazado": tr("No he podido abrir el puerto del router yo solo: el router ha rechazado la petición. Para los amigos de fuera de casa, el manual explica cómo abrirlo a mano."),
}
