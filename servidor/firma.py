"""Firma Ed25519 (RFC 8032) con la biblioteca estándar de Python.

El actualizador comprueba con esto que la información de una versión nueva la ha firmado quien publica
el juego. Si el paquete `cryptography` está instalado se usa ese, que es más rápido; si no, se usa esta
implementación, que sigue al pie de la letra el código de referencia del RFC 8032 y se comprueba en las
pruebas con sus vectores oficiales. Verificar una firma solo maneja datos públicos.
"""
import hashlib

P = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
RAIZ_M1 = pow(2, (P - 1) // 4, P)


def _h(datos):
    return hashlib.sha512(datos).digest()


def _inv(x):
    return pow(x, P - 2, P)


def _suma(a, b):
    aa = (a[1] - a[0]) * (b[1] - b[0]) % P
    bb = (a[1] + a[0]) * (b[1] + b[0]) % P
    cc = 2 * a[3] * b[3] * D % P
    dd = 2 * a[2] * b[2] % P
    e, f, g, h = bb - aa, dd - cc, dd + cc, bb + aa
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _por(s, punto):
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _suma(q, punto)
        punto = _suma(punto, punto)
        s >>= 1
    return q


def _iguales(a, b):
    return (a[0] * b[2] - b[0] * a[2]) % P == 0 and (a[1] * b[2] - b[1] * a[2]) % P == 0


def _x_de(y, signo):
    if y >= P:
        return None
    x2 = (y * y - 1) * _inv(D * y * y + 1) % P
    if x2 == 0:
        return None if signo else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P != 0:
        x = x * RAIZ_M1 % P
    if (x * x - x2) % P != 0:
        return None
    if (x & 1) != signo:
        x = P - x
    return x


_GY = 4 * _inv(5) % P
_GX = _x_de(_GY, 0)
G = (_GX, _GY, 1, _GX * _GY % P)


def _comprimir(p):
    zi = _inv(p[2])
    x, y = p[0] * zi % P, p[1] * zi % P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _descomprimir(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    signo = y >> 255
    y &= (1 << 255) - 1
    x = _x_de(y, signo)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


def _expandir(semilla):
    if len(semilla) != 32:
        raise ValueError("La clave privada debe tener 32 bytes.")
    h = _h(semilla)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def publica(semilla):
    """Clave pública (32 bytes) de una clave privada (32 bytes)."""
    a, _ = _expandir(semilla)
    return _comprimir(_por(a, G))


def firmar(semilla, mensaje):
    a, prefijo = _expandir(semilla)
    pub = _comprimir(_por(a, G))
    r = int.from_bytes(_h(prefijo + mensaje), "little") % L
    rs = _comprimir(_por(r, G))
    h = int.from_bytes(_h(rs + pub + mensaje), "little") % L
    return rs + int.to_bytes((r + h * a) % L, 32, "little")


def verificar(pub, mensaje, firma):
    """True si la firma (64 bytes) de ese mensaje es de la clave pública (32 bytes)."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception:
        return _verificar(pub, mensaje, firma)
    try:
        Ed25519PublicKey.from_public_bytes(pub).verify(firma, mensaje)
        return True
    except (InvalidSignature, ValueError):
        return False


def _verificar(pub, mensaje, firma):
    if len(pub) != 32 or len(firma) != 64:
        return False
    a = _descomprimir(pub)
    r = _descomprimir(firma[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(firma[32:], "little")
    if s >= L:
        return False
    h = int.from_bytes(_h(firma[:32] + pub + mensaje), "little") % L
    return _iguales(_por(s, G), _suma(r, _por(h, a)))
