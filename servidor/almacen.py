"""Lo que el servidor guarda en disco: cuentas, personajes, bandas, territorios, vehículos aparcados y el reloj.

Un único archivo SQLite. No se guarda ningún dato personal: de cada jugador, su clave pública, el nombre que eligió
y su personaje. Ni direcciones IP, ni correo, ni contraseñas.
"""
import json
import os
import sqlite3
import time

ESQUEMA = """
CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS cuentas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, pub TEXT UNIQUE NOT NULL, nombre TEXT UNIQUE NOT NULL,
    creada REAL, visto REAL, partida TEXT, recompensa INTEGER DEFAULT 0, bajas INTEGER DEFAULT 0, caidas INTEGER DEFAULT 0,
    vetado INTEGER DEFAULT 0, admin INTEGER DEFAULT 0, pendiente TEXT DEFAULT '[]', dia_salida INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS invitaciones (codigo TEXT PRIMARY KEY, creada REAL, usada_por INTEGER);
CREATE TABLE IF NOT EXISTS bandas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, jefe INTEGER, caja INTEGER DEFAULT 0,
    fuego INTEGER DEFAULT 0, creada REAL);
CREATE TABLE IF NOT EXISTS miembros (cuenta INTEGER PRIMARY KEY, banda INTEGER, rango TEXT);
CREATE TABLE IF NOT EXISTS apuntes (id INTEGER PRIMARY KEY AUTOINCREMENT, banda INTEGER, momento REAL, nombre TEXT, cantidad INTEGER, motivo TEXT);
CREATE TABLE IF NOT EXISTS alianzas (a INTEGER, b INTEGER, PRIMARY KEY (a, b));
CREATE TABLE IF NOT EXISTS territorios (mapa TEXT, barrio TEXT, banda INTEGER, desde REAL, PRIMARY KEY (mapa, barrio));
CREATE TABLE IF NOT EXISTS vehiculos (id INTEGER PRIMARY KEY, datos TEXT, momento REAL);
CREATE TABLE IF NOT EXISTS propiedades (lugar TEXT PRIMARY KEY, cuenta INTEGER, desde REAL, robado_dia INTEGER DEFAULT 0, pendiente INTEGER DEFAULT 0, oferta INTEGER DEFAULT 0);
"""


class Almacen:
    def __init__(self, ruta):
        carpeta = os.path.dirname(os.path.abspath(ruta))
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        self.ruta = ruta
        self.db = sqlite3.connect(ruta)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(ESQUEMA)
        self.db.commit()

    def cerrar(self):
        self.db.commit()
        self.db.close()

    def guardar(self):
        self.db.commit()

    def copia(self, destino):
        """Copia de seguridad en caliente."""
        self.db.commit()
        otra = sqlite3.connect(destino)
        try:
            self.db.backup(otra)
        finally:
            otra.close()

    # ------------------------------------------------------------------ meta
    def meta(self, clave, defecto=None):
        f = self.db.execute("SELECT valor FROM meta WHERE clave=?", (clave,)).fetchone()
        return json.loads(f["valor"]) if f else defecto

    def poner_meta(self, clave, valor):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (clave, json.dumps(valor)))

    # --------------------------------------------------------------- cuentas
    def cuenta_por_pub(self, pub):
        return self.db.execute("SELECT * FROM cuentas WHERE pub=?", (pub,)).fetchone()

    def cuenta_por_nombre(self, nombre):
        return self.db.execute("SELECT * FROM cuentas WHERE nombre=? COLLATE NOCASE", (nombre,)).fetchone()

    def cuenta(self, ident):
        return self.db.execute("SELECT * FROM cuentas WHERE id=?", (ident,)).fetchone()

    def cuentas(self):
        return self.db.execute("SELECT * FROM cuentas ORDER BY nombre").fetchall()

    def crear_cuenta(self, pub, nombre, admin=False):
        ahora = time.time()
        c = self.db.execute("INSERT INTO cuentas (pub, nombre, creada, visto, admin) VALUES (?,?,?,?,?)", (pub, nombre, ahora, ahora, int(admin)))
        self.db.commit()
        return self.cuenta(c.lastrowid)

    def poner(self, ident, **campos):
        if not campos:
            return
        sets = ", ".join(k + "=?" for k in campos)
        self.db.execute("UPDATE cuentas SET " + sets + " WHERE id=?", list(campos.values()) + [ident])

    def sumar(self, ident, campo, n):
        assert campo in ("recompensa", "bajas", "caidas")
        self.db.execute("UPDATE cuentas SET " + campo + "=MAX(0, " + campo + "+?) WHERE id=?", (n, ident))

    def pendientes(self, ident, vaciar=True):
        f = self.cuenta(ident)
        lista = json.loads(f["pendiente"] or "[]") if f else []
        if vaciar and lista:
            self.poner(ident, pendiente="[]")
        return lista

    def dejar_pendiente(self, ident, cosa):
        lista = self.pendientes(ident, vaciar=False)
        lista.append(cosa)
        self.poner(ident, pendiente=json.dumps(lista[-30:], ensure_ascii=False))

    # ----------------------------------------------------------- invitaciones
    def crear_invitacion(self, codigo):
        self.db.execute("INSERT INTO invitaciones VALUES (?,?,NULL)", (codigo, time.time()))
        self.db.commit()

    def usar_invitacion(self, codigo, cuenta):
        f = self.db.execute("SELECT * FROM invitaciones WHERE codigo=? AND usada_por IS NULL", (codigo,)).fetchone()
        if not f:
            return False
        self.db.execute("UPDATE invitaciones SET usada_por=? WHERE codigo=?", (cuenta, codigo))
        return True

    def invitacion_libre(self, codigo):
        return self.db.execute("SELECT 1 FROM invitaciones WHERE codigo=? AND usada_por IS NULL", (codigo,)).fetchone() is not None

    # ---------------------------------------------------------------- bandas
    def banda(self, ident):
        return self.db.execute("SELECT * FROM bandas WHERE id=?", (ident,)).fetchone()

    def banda_por_nombre(self, nombre):
        return self.db.execute("SELECT * FROM bandas WHERE nombre=? COLLATE NOCASE", (nombre,)).fetchone()

    def bandas(self):
        return self.db.execute("SELECT * FROM bandas ORDER BY nombre").fetchall()

    def crear_banda(self, nombre, jefe):
        c = self.db.execute("INSERT INTO bandas (nombre, jefe, creada) VALUES (?,?,?)", (nombre, jefe, time.time()))
        self.db.execute("INSERT OR REPLACE INTO miembros VALUES (?,?,?)", (jefe, c.lastrowid, "jefe"))
        self.db.commit()
        return c.lastrowid

    def borrar_banda(self, ident):
        for tabla, campo in (("miembros", "banda"), ("territorios", "banda"), ("apuntes", "banda")):
            self.db.execute("DELETE FROM " + tabla + " WHERE " + campo + "=?", (ident,))
        self.db.execute("DELETE FROM alianzas WHERE a=? OR b=?", (ident, ident))
        self.db.execute("DELETE FROM bandas WHERE id=?", (ident,))
        self.db.commit()

    def poner_banda(self, ident, **campos):
        sets = ", ".join(k + "=?" for k in campos)
        self.db.execute("UPDATE bandas SET " + sets + " WHERE id=?", list(campos.values()) + [ident])

    def miembro(self, cuenta):
        return self.db.execute("SELECT * FROM miembros WHERE cuenta=?", (cuenta,)).fetchone()

    def miembros(self, banda):
        return self.db.execute("SELECT m.cuenta, m.rango, c.nombre FROM miembros m JOIN cuentas c ON c.id=m.cuenta WHERE m.banda=? "
                               "ORDER BY CASE m.rango WHEN 'jefe' THEN 0 WHEN 'mano' THEN 1 ELSE 2 END, c.nombre", (banda,)).fetchall()

    def meter_miembro(self, cuenta, banda, rango="miembro"):
        self.db.execute("INSERT OR REPLACE INTO miembros VALUES (?,?,?)", (cuenta, banda, rango))
        self.db.commit()

    def sacar_miembro(self, cuenta):
        self.db.execute("DELETE FROM miembros WHERE cuenta=?", (cuenta,))
        self.db.commit()

    def apunte(self, banda, nombre, cantidad, motivo):
        self.db.execute("INSERT INTO apuntes (banda, momento, nombre, cantidad, motivo) VALUES (?,?,?,?,?)", (banda, time.time(), nombre, cantidad, motivo))
        self.db.execute("UPDATE bandas SET caja=MAX(0, caja+?) WHERE id=?", (cantidad, banda))
        self.db.commit()

    def apuntes(self, banda, n=12):
        return self.db.execute("SELECT * FROM apuntes WHERE banda=? ORDER BY id DESC LIMIT ?", (banda, n)).fetchall()

    def aliadas(self, banda):
        filas = self.db.execute("SELECT a, b FROM alianzas WHERE a=? OR b=?", (banda, banda)).fetchall()
        return {f["a"] if f["b"] == banda else f["b"] for f in filas}

    def aliar(self, a, b, si=True):
        a, b = min(a, b), max(a, b)
        if si:
            self.db.execute("INSERT OR IGNORE INTO alianzas VALUES (?,?)", (a, b))
        else:
            self.db.execute("DELETE FROM alianzas WHERE a=? AND b=?", (a, b))
        self.db.commit()

    # ------------------------------------------------------------ territorios
    def territorios(self):
        return self.db.execute("SELECT * FROM territorios").fetchall()

    def territorio(self, mapa, barrio):
        return self.db.execute("SELECT * FROM territorios WHERE mapa=? AND barrio=?", (mapa, barrio)).fetchone()

    def poner_territorio(self, mapa, barrio, banda):
        if banda is None:
            self.db.execute("DELETE FROM territorios WHERE mapa=? AND barrio=?", (mapa, barrio))
        else:
            self.db.execute("INSERT OR REPLACE INTO territorios VALUES (?,?,?,?)", (mapa, barrio, banda, time.time()))
        self.db.commit()

    # ------------------------------------------------------------ propiedades
    def propiedades(self):
        return self.db.execute("SELECT p.*, c.nombre FROM propiedades p JOIN cuentas c ON c.id=p.cuenta").fetchall()

    def propiedad(self, lugar):
        return self.db.execute("SELECT p.*, c.nombre FROM propiedades p JOIN cuentas c ON c.id=p.cuenta WHERE p.lugar=?", (lugar,)).fetchone()

    def poner_propiedad(self, lugar, cuenta):
        self.db.execute("INSERT OR REPLACE INTO propiedades (lugar, cuenta, desde) VALUES (?,?,?)", (lugar, cuenta, time.time()))
        self.db.commit()

    def quitar_propiedad(self, lugar):
        self.db.execute("DELETE FROM propiedades WHERE lugar=?", (lugar,))
        self.db.commit()

    def poner_oferta(self, lugar, precio):
        self.db.execute("UPDATE propiedades SET oferta=? WHERE lugar=?", (precio, lugar))
        self.db.commit()

    def propiedades_abandonadas(self, antes_de):
        return self.db.execute("SELECT p.lugar, p.cuenta FROM propiedades p JOIN cuentas c ON c.id=p.cuenta WHERE c.visto < ?", (antes_de,)).fetchall()

    def robo_en(self, lugar, dia, cantidad):
        self.db.execute("UPDATE propiedades SET robado_dia=?, pendiente=pendiente+? WHERE lugar=?", (dia, cantidad, lugar))
        self.db.commit()

    def cobrar_robos(self, cuenta):
        """Lo que les han robado a los negocios de una cuenta y aún no se le ha descontado. Lo deja a cero."""
        f = self.db.execute("SELECT COALESCE(SUM(pendiente), 0) AS t FROM propiedades WHERE cuenta=?", (cuenta,)).fetchone()
        total = int(f["t"] or 0)
        if total:
            self.db.execute("UPDATE propiedades SET pendiente=0 WHERE cuenta=?", (cuenta,))
            self.db.commit()
        return total

    # -------------------------------------------------------------- vehículos
    def vehiculos(self):
        return [json.loads(f["datos"]) for f in self.db.execute("SELECT datos FROM vehiculos").fetchall()]

    def guardar_vehiculos(self, lista):
        self.db.execute("DELETE FROM vehiculos")
        ahora = time.time()
        self.db.executemany("INSERT INTO vehiculos VALUES (?,?,?)", [(v["id"], json.dumps(v, ensure_ascii=False), ahora) for v in lista])
        self.db.commit()
