"""Crea un certificado propio para cifrar la conexión, sin ningún programa aparte.

Si el ordenador tiene openssl, el servidor lo usa. Si no lo tiene, que es lo normal en Windows, se usa esto: una clave
RSA de 2048 bits y un certificado X.509 firmado con ella, escritos con la biblioteca de Python y nada más.

El certificado no lo firma ninguna autoridad: lo que da seguridad es que el juego recuerda su huella la primera vez
que entra en el servidor y avisa si un día es otra.
"""
import base64
import hashlib
import secrets
import time

_PRIMOS = [p for p in range(3, 2000, 2) if all(p % q for q in range(3, int(p ** 0.5) + 1, 2))]


def _es_primo(n, rondas=40):
    if n < 2:
        return False
    for p in _PRIMOS:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rondas):                          # Miller-Rabin
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _primo(bits):
    while True:
        n = secrets.randbits(bits) | (3 << (bits - 2)) | 1      # los dos bits de arriba puestos, e impar
        if _es_primo(n):
            return n


# ---------------------------------------------------------------------- DER
def _largo(n):
    if n < 128:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def _tlv(etiqueta, contenido):
    return bytes([etiqueta]) + _largo(len(contenido)) + contenido


def _entero(n):
    b = n.to_bytes(n.bit_length() // 8 + 1, "big")              # con un cero delante si hace falta: siempre positivo
    return _tlv(0x02, b)


def _sec(*partes):
    return _tlv(0x30, b"".join(partes))


def _oid(texto):
    nums = [int(x) for x in texto.split(".")]
    out = bytes([40 * nums[0] + nums[1]])
    for n in nums[2:]:
        trozo = [n & 0x7F]
        n >>= 7
        while n:
            trozo.append(0x80 | (n & 0x7F))
            n >>= 7
        out += bytes(reversed(trozo))
    return _tlv(0x06, out)


def _bits(contenido):
    return _tlv(0x03, b"\x00" + contenido)


def _pem(tipo, der):
    b64 = base64.b64encode(der).decode("ascii")
    lineas = [b64[i:i + 64] for i in range(0, len(b64), 64)]
    return "-----BEGIN %s-----\n%s\n-----END %s-----\n" % (tipo, "\n".join(lineas), tipo)


RSA = "1.2.840.113549.1.1.1"
SHA256_RSA = "1.2.840.113549.1.1.11"
SHA256 = "2.16.840.1.101.3.4.2.1"
NULO = b"\x05\x00"


def crear(nombre="PuertoBravo", dias=3650, bits=2048):
    """Devuelve (certificado, llave), los dos en texto PEM."""
    e = 65537
    while True:
        p, q = _primo(bits // 2), _primo(bits // 2)
        n, fi = p * q, (p - 1) * (q - 1)
        if p != q and n.bit_length() == bits and fi % e:
            break
    d = _inverso(e, fi)
    llave = _sec(_entero(0), _entero(n), _entero(e), _entero(d), _entero(p), _entero(q), _entero(d % (p - 1)), _entero(d % (q - 1)), _entero(_inverso(q, p)))
    quien = _sec(_tlv(0x31, _sec(_oid("2.5.4.3"), _tlv(0x0C, nombre.encode("utf-8")))))
    ahora = time.time()

    def fecha(t):
        return _tlv(0x17, time.strftime("%y%m%d%H%M%SZ", time.gmtime(t)).encode("ascii"))
    algoritmo = _sec(_oid(SHA256_RSA), NULO)
    publica = _sec(_sec(_oid(RSA), NULO), _bits(_sec(_entero(n), _entero(e))))
    cuerpo = _sec(_tlv(0xA0, _entero(2)), _entero(secrets.randbits(120) | 1), algoritmo, quien,
                  _sec(fecha(ahora - 86400), fecha(ahora + 86400.0 * dias)), quien, publica)
    resumen = _sec(_sec(_oid(SHA256), NULO), _tlv(0x04, hashlib.sha256(cuerpo).digest()))
    k = (bits + 7) // 8
    bloque = b"\x00\x01" + b"\xff" * (k - len(resumen) - 3) + b"\x00" + resumen      # PKCS#1 v1.5
    firma = pow(int.from_bytes(bloque, "big"), d, n).to_bytes(k, "big")
    certificado = _sec(cuerpo, algoritmo, _bits(firma))
    return _pem("CERTIFICATE", certificado), _pem("RSA PRIVATE KEY", llave)


def _inverso(a, m):
    """El inverso de a módulo m, para las versiones de Python que no lo traen en pow."""
    g, x, y = m, 0, 1
    r = a % m
    while r:
        c = g // r
        g, r = r, g - c * r
        x, y = y, x - c * y
    return x % m


def escribir(ruta_cert, ruta_llave, nombre="PuertoBravo"):
    cert, llave = crear(nombre)
    with open(ruta_cert, "w", encoding="ascii", newline="\n") as f:
        f.write(cert)
    with open(ruta_llave, "w", encoding="ascii", newline="\n") as f:
        f.write(llave)
    return True
