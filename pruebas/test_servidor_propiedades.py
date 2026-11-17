"""Con la economía del servidor encendida, una casa o un negocio solo da dinero al venderlo si el servidor vio pagarlo.

El juego de cada jugador paga las compras por su cuenta, y puede traer propiedades de jugar solo. Si el servidor diera
dinero por vender cualquiera de ellas, bastaría apuntarse casas sin pagar y venderlas para hacerse rico. Así que el
servidor casa cada compra con un gasto que le haya visto al jugador en esos segundos: la que casa, vale lo suyo; la que
no, se puede tener y usar, pero no devuelve nada ni se puede vender a otro jugador.
"""
import sqlite3

from servidor import almacen
from test_servidor import Banco, mundo
from test_servidor_diez import J, Sim, avisos, cerrar_todos, sacar, sinc


def _casas():
    lugares = [l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] in ("casa", "negocio") and int(l.get("precio", 0) or 0) > 0]
    lugares.sort(key=lambda l: l["precio"])
    return lugares


def _rico(banco, c, n):
    """El servidor le reconoce n euros, como si los hubiera ganado en él."""
    def f():
        j = J(banco, c)
        j.credito += n
    banco.hacer(f)
    c.est(di=c.e["di"] + n)
    sinc(c)


def _pagada(banco, lugar):
    return banco.hacer(lambda: bool(banco.srv.alm.propiedad(lugar)["pagada"]))


def test_apuntarse_una_casa_sin_pagarla_no_da_dinero_al_venderla(tmp_path):
    banco = Banco(tmp_path, economia="si")
    g = []
    try:
        g = [Sim(banco, "Ana"), Sim(banco, "Blas")]
        casa = _casas()[0]
        for c in g:
            c.est()
        sinc(*g)
        tramposa = g[0]
        antes = banco.hacer(lambda: J(banco, tramposa).saldo)
        # se la apunta sin que salga un euro: es suya, pero no consta el pago
        tramposa.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        sinc(tramposa)
        assert banco.hacer(lambda: banco.srv.alm.propiedad(casa["id"])["cuenta"]) == tramposa.ok["cuenta"] if "cuenta" in (tramposa.ok or {}) else True
        assert not _pagada(banco, casa["id"])
        # no la puede vender a otro jugador
        tramposa.enviar({"t": "prop_oferta", "lugar": casa["id"], "precio": 9000})
        sinc(tramposa)
        assert avisos(tramposa, "no le consta que la pagaras")
        assert banco.hacer(lambda: banco.srv.alm.propiedad(casa["id"])["oferta"]) == 0
        # y al mercado vuelve, pero sin darle nada
        tramposa.enviar({"t": "prop_soltar", "lugar": casa["id"]})
        sinc(tramposa)
        assert not sacar(tramposa, "dinero") and avisos(tramposa, "no te da dinero")
        assert banco.hacer(lambda: banco.srv.alm.propiedad(casa["id"])) is None
        assert banco.hacer(lambda: J(banco, tramposa).saldo) == antes
        # repetirlo cien veces tampoco da un euro
        for _ in range(20):
            tramposa.enviar({"t": "prop_comprar", "lugar": casa["id"]})
            tramposa.enviar({"t": "prop_soltar", "lugar": casa["id"]})
        sinc(tramposa)
        assert not sacar(tramposa, "dinero") and banco.hacer(lambda: J(banco, tramposa).saldo) == antes
    finally:
        cerrar_todos(g)
        banco.parar()


def test_la_casa_pagada_devuelve_su_parte_y_se_puede_vender(tmp_path):
    banco = Banco(tmp_path, economia="si")
    g = []
    try:
        g = [Sim(banco, "Ana"), Sim(banco, "Blas")]
        casa = _casas()[0]
        precio = casa["precio"]
        for c in g:
            c.est()
        sinc(*g)
        _rico(banco, g[0], precio + 500)
        _rico(banco, g[1], precio + 500)
        ana, blas = g
        # paga en su juego y se lo dice al servidor, en ese orden
        ana.est(di=ana.e["di"] - precio)
        ana.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        sinc(ana)
        assert _pagada(banco, casa["id"])
        # la pone en venta y Blas se la compra: la cobra el servidor, así que a Blas también le consta
        ana.enviar({"t": "prop_oferta", "lugar": casa["id"], "precio": precio})
        sinc(ana)
        assert banco.hacer(lambda: banco.srv.alm.propiedad(casa["id"])["oferta"]) == precio
        blas.enviar({"t": "prop_adquirir", "lugar": casa["id"]})
        assert blas.leer("cobro")["n"] == precio
        blas.est(di=blas.e["di"] - precio)
        sinc(blas)
        assert _pagada(banco, casa["id"])
        blas.enviar({"t": "prop_soltar", "lugar": casa["id"]})
        assert blas.leer("dinero")["n"] == precio * 70 // 100
    finally:
        cerrar_todos(g)
        banco.parar()


def test_el_aviso_puede_llegar_antes_que_el_gasto(tmp_path):
    """El juego manda la compra y, una décima después, la posición con el dinero ya restado: también cuenta como pagada."""
    banco = Banco(tmp_path, economia="si")
    g = []
    try:
        g = [Sim(banco, "Ana")]
        ana = g[0]
        casa = _casas()[0]
        ana.est()
        sinc(ana)
        _rico(banco, ana, casa["precio"] + 100)
        ana.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        sinc(ana)
        assert not _pagada(banco, casa["id"])
        ana.est(di=ana.e["di"] - casa["precio"])
        sinc(ana)
        assert _pagada(banco, casa["id"])
        # un mismo gasto no paga dos casas
        otra = _casas()[1]
        ana.enviar({"t": "prop_comprar", "lugar": otra["id"]})
        sinc(ana)
        assert not _pagada(banco, otra["id"])
    finally:
        cerrar_todos(g)
        banco.parar()


def test_lo_que_ya_habia_en_un_servidor_antiguo_cuenta_como_pagado(tmp_path):
    ruta = str(tmp_path / "vieja.db")
    db = sqlite3.connect(ruta)
    db.execute("CREATE TABLE propiedades (lugar TEXT PRIMARY KEY, cuenta INTEGER, desde REAL, robado_dia INTEGER DEFAULT 0, pendiente INTEGER DEFAULT 0, oferta INTEGER DEFAULT 0)")
    db.execute("INSERT INTO propiedades (lugar, cuenta, desde) VALUES ('piso_centro', 1, 0)")
    db.commit()
    db.close()
    alm = almacen.Almacen(ruta) if hasattr(almacen, "Almacen") else None
    assert alm is not None
    try:
        fila = alm.db.execute("SELECT pagada FROM propiedades WHERE lugar='piso_centro'").fetchone()
        assert fila[0] == 1
        alm.poner_propiedad("otra", 1)
        assert alm.db.execute("SELECT pagada FROM propiedades WHERE lugar='otra'").fetchone()[0] == 0
        alm.marcar_pagada("otra", 1)
        assert alm.db.execute("SELECT pagada FROM propiedades WHERE lugar='otra'").fetchone()[0] == 1
    finally:
        alm.db.close()


def test_sin_economia_todo_sigue_como_antes(tmp_path):
    banco = Banco(tmp_path, economia="no")
    g = []
    try:
        g = [Sim(banco, "Ana")]
        ana = g[0]
        casa = _casas()[0]
        ana.est()
        ana.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        sinc(ana)
        ana.enviar({"t": "prop_soltar", "lugar": casa["id"]})
        assert ana.leer("dinero")["n"] == casa["precio"] * 70 // 100
    finally:
        cerrar_todos(g)
        banco.parar()
