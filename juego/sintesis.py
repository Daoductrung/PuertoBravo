"""Todos los efectos de sonido del juego, sintetizados con numpy.

No hay ni un archivo de audio: cada sonido se genera al arrancar (y se guarda
en caché). Para sustituir uno por una grabación propia basta con dejar un WAV
con el mismo nombre en la carpeta mods/sonidos.
"""
import os

import numpy as np

SR = 44100
VERSION_CACHE = 11
PI2 = 2 * np.pi


def _t(d):
    return np.arange(int(SR * d)) / SR


def _filtro(x, lo=None, hi=None, orden=4):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1.0 / (1.0 + (f / hi) ** orden)
    if lo:
        r = (f / lo) ** orden
        g *= r / (1.0 + r)
    return np.fft.irfft(X * g, len(x))


def _norm(x, pico=0.8):
    m = np.max(np.abs(x)) if len(x) else 0
    if m > 0:
        x = x * (pico / m)
    return x.astype(np.float32)


def _bordes(x, ms=4):
    n = min(int(SR * ms / 1000), len(x) // 2)
    if n > 0:
        r = np.linspace(0, 1, n)
        x = x.copy()
        x[:n] *= r
        x[-n:] *= r[::-1]
    return x


def _decae(d, tau, ataque=0.003):
    t = _t(d)
    return np.minimum(1.0, t / ataque) * np.exp(-t / tau)


def _bucle(x, ms=60):
    """Funde el final con el principio para que el bucle no haga clic."""
    n = min(int(SR * ms / 1000), len(x) // 3)
    r = np.linspace(0, 1, n)
    cuerpo = x[:-n].copy()
    cuerpo[:n] = cuerpo[:n] * r + x[-n:] * (1 - r)
    return cuerpo


def _seno(f, d, fase=0.0):
    return np.sin(PI2 * f * _t(d) + fase)


def _barrido(f0, f1, d, forma="seno"):
    t = _t(d)
    f = f0 + (f1 - f0) * (t / d)
    fase = PI2 * np.cumsum(f) / SR
    if forma == "sierra":
        return 2 * ((fase / PI2) % 1.0) - 1
    if forma == "cuadrada":
        return np.sign(np.sin(fase))
    return np.sin(fase)


def _sierra(f, d):
    return 2 * ((f * _t(d)) % 1.0) - 1


def _cuadrada(f, d):
    return np.sign(np.sin(PI2 * f * _t(d)))


def _nota(f, d, tau=0.25, arm=(1, 0.4, 0.2)):
    x = sum(a * _seno(f * (k + 1), d) for k, a in enumerate(arm))
    return x * _decae(d, tau)


def _poner(dest, x, t0, g=1.0):
    i = int(t0 * SR)
    if i >= len(dest):
        return
    n = min(len(x), len(dest) - i)
    dest[i:i + n] += x[:n] * g


def _sec(notas, paso, d_nota, tau=0.2, arm=(1, 0.4, 0.2)):
    out = np.zeros(int(SR * (paso * len(notas) + d_nota)))
    for k, f in enumerate(notas):
        if f:
            _poner(out, _nota(f, d_nota, tau, arm), k * paso)
    return out


def generar(semilla=7):
    rng = np.random.default_rng(semilla)
    S = {}

    def ruido(d):
        return rng.standard_normal(int(SR * d))

    # ------------------------------------------------------------ interfaz
    S["menu_mover"] = _norm(_seno(1100, 0.03) * _decae(0.03, 0.01), 0.35)
    S["menu_ok"] = _norm(_sec([880, 1320], 0.06, 0.15, 0.06), 0.5)
    S["menu_atras"] = _norm(_sec([660, 440], 0.06, 0.15, 0.06), 0.5)
    S["menu_borde"] = _norm(_seno(180, 0.08) * _decae(0.08, 0.03), 0.5)
    S["menu_ajuste"] = _norm(_seno(1500, 0.03) * _decae(0.03, 0.012), 0.35)
    S["error"] = _norm(_filtro(_cuadrada(140, 0.22), hi=1200) * _decae(0.22, 0.12), 0.5)
    S["notificacion"] = _norm(_sec([988, 1319, 1568], 0.08, 0.3, 0.12), 0.5)
    S["mision_ok"] = _norm(_sec([523, 659, 784, 1047, 784, 1047], 0.11, 0.7, 0.3, (1, 0.5, 0.3, 0.2)), 0.7)
    S["mision_fallo"] = _norm(_sec([392, 370, 330, 262], 0.2, 0.8, 0.4, (1, 0.6, 0.4)), 0.7)
    S["dinero"] = _norm(_sec([2093, 2637, 0, 2093, 3136], 0.05, 0.3, 0.08, (1, 0.3)), 0.5)
    S["guardado"] = _norm(_sec([659, 784, 1047], 0.09, 0.4, 0.15), 0.5)
    S["movil"] = _norm(_sec([1319, 1760], 0.05, 0.12, 0.04), 0.4)
    S["dialogo"] = _norm(_seno(700, 0.05) * _decae(0.05, 0.02), 0.3)
    S["pasan_horas"] = _norm(_sec([440, 554, 659, 554, 440], 0.25, 0.6, 0.3), 0.4)

    # --------------------------------------------------------------- pasos
    def paso(lo, hi, d, tau, g):
        return _norm(_filtro(ruido(d), lo, hi) * _decae(d, tau, 0.002), g)

    for k in range(2):
        S[f"paso_acera{k}"] = paso(700, 3200, 0.09, 0.02, 0.45)
        S[f"paso_calzada{k}"] = paso(250, 1300, 0.1, 0.03, 0.5)
        S[f"paso_hierba{k}"] = paso(2000, 7000, 0.16, 0.05, 0.3)
        S[f"paso_arena{k}"] = paso(500, 3000, 0.2, 0.07, 0.35)
        S[f"paso_plaza{k}"] = paso(1200, 4500, 0.08, 0.018, 0.45)
        S[f"paso_muelle{k}"] = _norm(_filtro(ruido(0.14), 90, 600) * _decae(0.14, 0.04), 0.6)
    S["paso_npc"] = paso(500, 2200, 0.08, 0.02, 0.3)
    S["choque_pared"] = _norm(_filtro(ruido(0.12), 80, 500) * _decae(0.12, 0.04), 0.6)

    # ------------------------------------------------------------- personas
    def vocal(f0, f1, d, formantes, tau):
        x = _barrido(f0, f1, d, "sierra")
        y = sum(_filtro(x, fo * 0.8, fo * 1.25, 6) for fo in formantes)
        return y * _decae(d, tau, 0.02)

    S["dolor"] = _norm(vocal(150, 95, 0.3, (650, 1100), 0.15), 0.6)
    S["dolor_npc"] = _norm(vocal(190, 120, 0.28, (700, 1250), 0.14), 0.6)
    S["muerte_npc"] = _norm(vocal(170, 70, 0.7, (600, 1000), 0.35), 0.6)
    S["grito"] = _norm(np.concatenate([vocal(450, 760, 0.25, (900, 1900), 0.4),
                                       vocal(760, 380, 0.5, (900, 1900), 0.3)]), 0.55)
    S["murmullo"] = _norm(vocal(130, 115, 0.35, (500, 1400), 0.3) + 0.6 * np.roll(vocal(160, 140, 0.35, (450, 1500), 0.3), 4000), 0.3)
    S["golpe"] = _norm(_filtro(ruido(0.1), 60, 900) * _decae(0.1, 0.03) + _seno(90, 0.1) * _decae(0.1, 0.04), 0.8)
    S["golpe_aire"] = _norm(_filtro(ruido(0.15), 800, 4000) * np.sin(np.pi * _t(0.15) / 0.15) ** 2, 0.3)
    lat = _seno(55, 0.16) * _decae(0.16, 0.05)
    lz = np.zeros(SR)
    _poner(lz, lat, 0.0)
    _poner(lz, lat, 0.28, 0.7)
    S["latido"] = _norm(lz, 0.8)
    cr = np.zeros(int(SR * 0.6))
    for k in range(4):
        _poner(cr, _filtro(ruido(0.07), 1500, 6000) * _decae(0.07, 0.02), 0.14 * k)
    S["comer"] = _norm(cr, 0.4)
    S["curar"] = _norm(_sec([523, 659, 784, 1047], 0.07, 0.5, 0.25), 0.5)

    # ---------------------------------------------------------------- armas
    def disparo(lo, hi, d, tau, grave):
        x = _filtro(ruido(d), lo, hi) * _decae(d, tau, 0.0008)
        x += grave * _barrido(160, 50, d) * _decae(d, tau * 0.8, 0.001)
        return _norm(np.tanh(x * 3), 0.95)

    S["disparo_pistola"] = disparo(300, 5000, 0.35, 0.05, 0.6)
    S["disparo_revolver"] = disparo(200, 3500, 0.5, 0.08, 1.0)
    S["disparo_subfusil"] = disparo(500, 6000, 0.2, 0.03, 0.4)
    S["disparo_escopeta"] = disparo(120, 3000, 0.7, 0.12, 1.2)
    S["disparo_rifle"] = disparo(250, 7000, 0.8, 0.1, 0.8)
    S["sin_balas"] = _norm(_filtro(ruido(0.04), 2000, 8000) * _decae(0.04, 0.008), 0.4)
    rc = np.zeros(int(SR * 0.7))
    _poner(rc, _filtro(ruido(0.06), 1500, 6000) * _decae(0.06, 0.015), 0.0)
    _poner(rc, _filtro(ruido(0.08), 800, 4000) * _decae(0.08, 0.02), 0.3)
    _poner(rc, _filtro(ruido(0.06), 2000, 7000) * _decae(0.06, 0.012), 0.5)
    S["recarga"] = _norm(rc, 0.5)
    S["amartillar"] = _norm(rc[int(SR * 0.28): int(SR * 0.6)], 0.45)
    S["bala_impacto"] = _norm(_filtro(ruido(0.12), 1500, 7000) * _decae(0.12, 0.02) + 0.5 * _barrido(3000, 1200, 0.12) * _decae(0.12, 0.04), 0.5)
    S["bala_silbido"] = _norm(_barrido(4200, 1500, 0.18) * np.sin(np.pi * _t(0.18) / 0.18) ** 2, 0.5)
    ex = _filtro(ruido(1.8), 30, 1800) * _decae(1.8, 0.45, 0.002) + 1.5 * _barrido(90, 30, 1.8) * _decae(1.8, 0.3)
    S["explosion"] = _norm(np.tanh(ex * 2.5), 0.98)
    S["navaja"] = _norm(_filtro(ruido(0.12), 2500, 9000) * np.sin(np.pi * _t(0.12) / 0.12) ** 3, 0.4)

    # ------------------------------------------------------------ vehículos
    def motor(f0, n_arm, brillo, rugoso):
        d = 1.0
        t = _t(d)
        x = np.zeros_like(t)
        for k in range(1, n_arm + 1):
            x += np.sin(PI2 * f0 * k * t + rng.uniform(0, PI2)) / (k ** brillo)
        x *= 1.0 + 0.35 * np.sin(PI2 * (f0 / 2) * t) + 0.15 * np.sin(PI2 * (f0 / 4) * t)
        x += rugoso * _filtro(ruido(d), 100, 1200)
        return _norm(np.tanh(x * 1.2), 0.55)

    S["motor_coche"] = motor(56, 12, 1.0, 0.25)
    S["motor_deportivo"] = motor(80, 16, 0.7, 0.2)
    S["motor_moto"] = motor(96, 14, 0.5, 0.35)
    S["motor_camion"] = motor(40, 10, 1.1, 0.5)
    S["motor_furgoneta"] = motor(48, 10, 1.0, 0.4)
    rod = _filtro(ruido(1.5), 300, 2500)
    S["rodadura"] = _norm(_bucle(rod), 0.4)
    S["claxon"] = _norm(_bordes(_filtro(_cuadrada(420, 0.45) + _cuadrada(530, 0.45), hi=2500), 10), 0.6)
    S["claxon_camion"] = _norm(_bordes(_filtro(_cuadrada(170, 0.7) + _cuadrada(215, 0.7), hi=1500), 15), 0.7)
    fr = _filtro(ruido(0.9), 900, 2600, 6) + 0.5 * _barrido(1100, 850, 0.9, "sierra")
    S["frenazo"] = _norm(_bordes(fr * (1 - 0.6 * _t(0.9) / 0.9), 20), 0.5)
    ch = _filtro(ruido(0.6), 80, 2500) * _decae(0.6, 0.12, 0.001)
    for f in (310, 470, 830, 1240):
        ch += 0.25 * _seno(f, 0.6) * _decae(0.6, 0.1)
    S["choque"] = _norm(np.tanh(ch * 2), 0.9)
    S["choque_leve"] = _norm(ch[: int(SR * 0.3)] * _decae(0.3, 0.06), 0.6)
    pu = _seno(110, 0.18) * _decae(0.18, 0.04) + 0.5 * _filtro(ruido(0.18), 1000, 4000) * _decae(0.18, 0.012)
    S["puerta_coche"] = _norm(pu, 0.7)
    al = np.concatenate([_cuadrada(900, 0.25), _cuadrada(1250, 0.25)])
    S["alarma"] = _norm(_filtro(np.tile(al, 2), hi=4000), 0.5)
    arr = _filtro(_sierra(38, 0.9) * (0.6 + 0.4 * np.sin(PI2 * 9 * _t(0.9))), hi=900)
    S["arranque"] = _norm(_bordes(arr, 20), 0.6)
    tw = _t(2.0)
    fw = 650 + 650 * (0.5 - 0.5 * np.cos(PI2 * tw / 2.0))
    S["sirena"] = _norm(_filtro(np.sign(np.sin(PI2 * np.cumsum(fw) / SR)), hi=3500), 0.5)
    S["sirena_lejana"] = _norm(_filtro(S["sirena"].astype(np.float64), hi=800), 0.25)
    cris = _filtro(ruido(0.7), 3000, 12000) * _decae(0.7, 0.1, 0.001)
    for _ in range(14):
        _poner(cris, _seno(rng.uniform(3000, 9000), 0.3) * _decae(0.3, rng.uniform(0.02, 0.1)), rng.uniform(0, 0.3), 0.2)
    S["cristal"] = _norm(cris, 0.6)
    gz = np.zeros(SR)
    for k in range(9):
        _poner(gz, _seno(rng.uniform(2500, 5000), 0.03) * _decae(0.03, 0.006), k * 0.11 + rng.uniform(0, 0.03), rng.uniform(0.4, 1))
    S["ganzua"] = _norm(gz, 0.4)
    it = np.zeros(int(SR * 0.8))
    _poner(it, _seno(1800, 0.02) * _decae(0.02, 0.005), 0.0)
    _poner(it, _seno(1300, 0.02) * _decae(0.02, 0.005), 0.4)
    S["intermitente"] = _norm(it, 0.35)
    S["radio_cambio"] = _norm(_bordes(_filtro(ruido(0.3), 1000, 6000), 20), 0.3)
    S["reparar"] = _norm(np.concatenate([_filtro(_sierra(180, 0.25) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 30 * _t(0.25)))), hi=3000)] * 3), 0.5)
    S["pintura"] = _norm(_bordes(_filtro(ruido(1.2), 3000, 10000), 80), 0.4)
    S["fuego"] = _norm(_bucle(_filtro(ruido(2.0), 200, 3000) * (0.6 + 0.4 * _filtro(ruido(2.0), hi=12))), 0.5)

    # --------------------------------------------------- ayudas de orientación
    S["baliza"] = _norm(_nota(880, 0.35, 0.1, (1, 0.5, 0.25)) + _nota(1320, 0.35, 0.12, (0.6, 0.2)), 0.6)
    S["baliza_destino"] = _norm(_sec([1047, 1568], 0.09, 0.35, 0.12, (1, 0.4, 0.2)), 0.6)
    S["sonar"] = _norm(_bordes(_seno(1500, 0.05), 3), 0.45)
    S["tono_objetivo"] = _norm(_bordes(_seno(660, 0.07) + 0.4 * _seno(1980, 0.07), 6), 0.45)
    S["tono_apuntado"] = _norm(_bordes(_seno(1320, 0.04), 4), 0.4)
    S["tono_pared"] = _norm(_bordes(_seno(440, 0.15), 10), 0.4)
    S["tono_libre"] = _norm(_bordes(_seno(880, 0.08), 8), 0.3)
    S["bordillo"] = _norm(_bordes(_filtro(_cuadrada(85, 0.12), hi=500), 8), 0.6)
    S["cruce"] = _norm(_sec([784, 988], 0.07, 0.25, 0.09), 0.4)
    S["llegada"] = _norm(_sec([784, 988, 1175, 1568], 0.08, 0.5, 0.2), 0.6)
    S["radar"] = _norm(_bordes(_seno(1000, 0.06) * (1 + 0.5 * _seno(2000, 0.06)), 5), 0.45)
    S["estrella_sube"] = _norm(_filtro(_barrido(300, 900, 0.4, "sierra"), hi=3000) * _decae(0.4, 0.5, 0.01), 0.6)
    S["estrella_baja"] = _norm(_sec([880, 659, 523], 0.1, 0.4, 0.2), 0.45)
    S["policia_perdida"] = _norm(_sec([523, 659, 784, 1047], 0.12, 0.9, 0.5, (1, 0.5, 0.3)), 0.6)
    S["buscando"] = _norm(_seno(70, 0.12) * _decae(0.12, 0.04), 0.6)
    S["reloj"] = _norm(_seno(2000, 0.03) * _decae(0.03, 0.008), 0.4)
    S["semaforo_pio"] = _norm(_barrido(2900, 1900, 0.09) * _decae(0.09, 0.05, 0.005), 0.4)
    S["semaforo_tic"] = _norm(_seno(1000, 0.03) * _decae(0.03, 0.01), 0.4)
    S["recoger"] = _norm(_barrido(600, 1800, 0.18) * _decae(0.18, 0.2, 0.01), 0.5)
    S["esposas"] = _norm(np.concatenate([S["ganzua"][: int(SR * 0.35)], _filtro(ruido(0.1), 1500, 6000) * _decae(0.1, 0.02)]), 0.5)

    # --------------------------------------------- localizadores (en bucle)
    ob = np.zeros(int(SR * 1.2))
    _poner(ob, _nota(1568, 0.2, 0.05, (1, 0.3)), 0.0)
    _poner(ob, _nota(2093, 0.2, 0.05, (1, 0.3)), 0.12)
    S["loc_objeto"] = _norm(ob, 0.5)
    cs = np.zeros(int(SR * 1.6))
    for k, f in enumerate([1319, 1568, 1976, 2637, 1976, 1568]):
        _poner(cs, _nota(f, 0.3, 0.1, (1, 0.2)), k * 0.12)
    S["loc_casete"] = _norm(cs, 0.45)
    mi = np.zeros(int(SR * 1.5))
    _poner(mi, (_seno(392, 0.9) + _seno(587, 0.9) + 0.5 * _seno(784, 0.9)) * np.sin(np.pi * _t(0.9) / 0.9) ** 2, 0.1)
    S["loc_mision"] = _norm(mi, 0.5)
    lu = np.zeros(int(SR * 2.0))
    _poner(lu, _nota(523, 0.4, 0.15, (1, 0.5, 0.2)), 0.0)
    S["loc_lugar"] = _norm(lu, 0.4)
    vp = np.zeros(int(SR * 1.8))
    _poner(vp, _filtro(ruido(0.05), 2500, 7000) * _decae(0.05, 0.012), 0.0)
    _poner(vp, _filtro(ruido(0.05), 2500, 7000) * _decae(0.05, 0.012), 0.2)
    S["loc_vehiculo"] = _norm(vp, 0.3)

    # ---------------------------------------------------- firmas de lugares
    def bucle_eventos(d, eventos):
        out = np.zeros(int(SR * d))
        for x, t0, g in eventos:
            _poner(out, x, t0, g)
        return out

    S["lugar_armeria"] = _norm(bucle_eventos(2.6, [(S["amartillar"].astype(np.float64), 0.2, 1), (S["sin_balas"].astype(np.float64), 1.4, 0.8)]), 0.45)
    fri = _filtro(ruido(2.0), 3500, 11000) * (0.5 + 0.5 * np.abs(_filtro(ruido(2.0), hi=25)) * 6)
    S["lugar_comida"] = _norm(_bucle(fri), 0.3)
    S["lugar_hospital"] = _norm(bucle_eventos(1.0, [(_bordes(_seno(1000, 0.09), 4), 0.0, 1)]), 0.4)
    com = np.zeros(int(SR * 3.0))
    for t0, dd in ((0.1, 0.5), (0.9, 0.3), (1.6, 0.7)):
        _poner(com, _bordes(_filtro(ruido(dd), 700, 2600, 6) * (0.4 + np.abs(_filtro(ruido(dd), hi=14)) * 5), 8), t0)
    _poner(com, _bordes(_seno(1700, 0.06), 4), 2.4, 0.5)
    S["lugar_comisaria"] = _norm(com, 0.4)
    ta = np.zeros(int(SR * 3.0))
    for t0 in (0.2, 0.7, 1.9):
        _poner(ta, _bordes(_filtro(_sierra(170, 0.35) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 28 * _t(0.35)))), hi=2800), 6), t0)
    S["lugar_taller"] = _norm(ta, 0.45)
    cam = np.zeros(int(SR * 4.0))
    for _ in range(9):
        _poner(cam, _nota(rng.choice([1047, 1175, 1319, 1568, 1760, 2093]), 0.9, 0.4, (1, 0.3, 0.1)), rng.uniform(0, 3.0), rng.uniform(0.3, 1))
    S["lugar_casa"] = _norm(cam, 0.4)
    bar = np.zeros(int(SR * 2.0))
    for k in range(4):
        _poner(bar, _barrido(120, 45, 0.25) * _decae(0.25, 0.08), k * 0.5)
        _poner(bar, _filtro(_sierra([55, 55, 65.4, 49][k], 0.22), hi=300) * _decae(0.22, 0.2), k * 0.5 + 0.25, 0.6)
    S["lugar_bar"] = _norm(_filtro(bar, hi=500), 0.6)
    cas = np.zeros(int(SR * 2.4))
    for k in range(16):
        _poner(cas, _nota([1047, 1319, 1568, 2093][k % 4] * (1 + (k // 8) * 0.122), 0.12, 0.04, (1, 0.5)), k * 0.09)
    _poner(cas, S["dinero"].astype(np.float64), 1.6, 0.8)
    S["lugar_casino"] = _norm(cas, 0.4)
    S["lugar_tienda"] = _norm(bucle_eventos(3.2, [(_nota(1319, 0.7, 0.3, (1, 0.3)), 0.1, 1), (_nota(1047, 0.9, 0.4, (1, 0.3)), 0.55, 1)]), 0.4)
    S["lugar_banco"] = _norm(bucle_eventos(2.4, [(_bordes(_seno(1400, 0.05), 3), 0.1 + 0.16 * k, 1) for k in range(4)] + [(_bordes(_seno(1900, 0.2), 5), 1.1, 0.8)]), 0.35)
    camp = sum(a * _seno(f, 3.5) * _decae(3.5, tau) for f, a, tau in ((220, 1, 1.4), (440.5, 0.6, 1.0), (594, 0.45, 0.8), (880, 0.3, 0.5), (1175, 0.2, 0.3)))
    S["lugar_iglesia"] = _norm(camp, 0.5)
    ag = _filtro(ruido(3.0), 900, 6000) * (0.6 + 0.4 * np.abs(_filtro(ruido(3.0), hi=18)) * 5)
    S["lugar_fuente"] = _norm(_bucle(ag), 0.35)
    S["lugar_contacto"] = S["loc_mision"]
    S["lugar_generico"] = S["loc_lugar"]
    tx = np.zeros(int(SR * 2.5))
    _poner(tx, S["claxon"].astype(np.float64)[: int(SR * 0.12)], 0.1, 0.5)
    _poner(tx, S["claxon"].astype(np.float64)[: int(SR * 0.12)], 0.3, 0.5)
    S["lugar_taxi"] = _norm(tx, 0.3)
    S["lugar_periodico"] = _norm(bucle_eventos(2.0, [(_filtro(ruido(0.03), 1500, 5000) * _decae(0.03, 0.006), t0, g) for t0, g in zip(np.sort(rng.uniform(0, 1.9, 14)), rng.uniform(0.4, 1, 14))]), 0.35)

    # ------------------------------------------------------------- ambiente
    def olas(d):
        n = ruido(d)
        t = _t(d)
        env = (0.5 - 0.5 * np.cos(PI2 * t / (d / 2))) ** 1.5
        return _filtro(n, 150, 2500) * (0.25 + env) + 0.4 * _filtro(n, 2000, 7000) * env ** 3

    S["amb_playa"] = _norm(_bucle(olas(9.0), 300), 0.5)

    def gaviota():
        d = 0.45
        t = _t(d)
        f = 1500 - 500 * t / d + 60 * np.sin(PI2 * 25 * t)
        x = np.sin(PI2 * np.cumsum(f) / SR)
        x = x + 0.5 * np.sin(2 * PI2 * np.cumsum(f) / SR)
        return x * np.sin(np.pi * t / d)

    gv = np.zeros(int(SR * 2.0))
    for k in range(3):
        _poner(gv, gaviota(), 0.1 + 0.5 * k, 1 - 0.2 * k)
    S["gaviota"] = _norm(gv, 0.5)
    pu_ = olas(9.0) * 0.7
    _poner(pu_, _seno(98, 2.0) * np.sin(np.pi * _t(2.0) / 2.0) ** 2, 3.0, 0.5)   # sirena de barco lejana
    S["amb_puerto"] = _norm(_bucle(pu_, 300), 0.5)
    ciu = _filtro(ruido(8.0), 40, 350) + 0.3 * _filtro(ruido(8.0), 300, 1500) * (0.5 + 0.5 * _filtro(ruido(8.0), hi=0.7) * 20).clip(0, 2)
    S["amb_ciudad"] = _norm(_bucle(ciu, 300), 0.45)
    ind = _filtro(ruido(6.0), 40, 500) + 0.5 * _seno(50, 6.0) + 0.25 * _seno(100, 6.0) + 0.15 * _seno(150, 6.0)
    for t0 in (0.8, 2.9, 4.4):
        _poner(ind, sum(_seno(f, 0.5) * _decae(0.5, 0.08) for f in (520, 833, 1370)), t0, 0.35)
    S["amb_industrial"] = _norm(_bucle(ind, 300), 0.45)

    def pajaro():
        n = rng.integers(2, 6)
        out = np.zeros(int(SR * 0.9))
        f = rng.uniform(2800, 5200)
        for k in range(n):
            _poner(out, _barrido(f, f * rng.uniform(0.7, 1.4), 0.07) * np.sin(np.pi * _t(0.07) / 0.07), k * 0.13)
        return out

    par = 0.35 * _filtro(ruido(10.0), 300, 3000) * (0.6 + 0.4 * _filtro(ruido(10.0), hi=0.5) * 25).clip(0, 2)
    for _ in range(14):
        _poner(par, pajaro(), rng.uniform(0, 9.0), rng.uniform(0.2, 0.7))
    S["amb_parque"] = _norm(_bucle(par, 300), 0.45)
    S["pajaro"] = _norm(pajaro(), 0.4)
    res = 0.5 * _filtro(ruido(8.0), 40, 300)
    for _ in range(4):
        _poner(res, pajaro(), rng.uniform(0, 7.0), 0.25)
    S["amb_residencial"] = _norm(_bucle(res, 300), 0.35)
    tg = _t(6.0)
    gr = _seno(4400, 6.0) * (np.sin(PI2 * 32 * tg) > 0.3) * (np.sin(PI2 * 1.6 * tg) > -0.2)
    S["amb_noche"] = _norm(_bucle(gr + 0.3 * _filtro(ruido(6.0), 40, 250), 200), 0.3)
    S["lluvia"] = _norm(_bucle(_filtro(ruido(5.0), 1200, 9000) + 0.5 * _filtro(ruido(5.0), 200, 900), 300), 0.4)
    tr = _filtro(ruido(3.5), 25, 180) * _decae(3.5, 0.9, 0.05) * (1 + 0.5 * _filtro(ruido(3.5), hi=6) * 8)
    S["trueno"] = _norm(tr, 0.9)
    lad = np.zeros(int(SR * 1.0))
    for k in range(3):
        _poner(lad, vocal(520, 300, 0.12, (800, 1600), 0.08), k * 0.28)
    S["ladrido"] = _norm(lad, 0.5)
    mart = np.zeros(int(SR * 1.2))
    for k in range(4):
        _poner(mart, (sum(_seno(f, 0.2) for f in (640, 1130, 2210)) + _filtro(ruido(0.2), 800, 4000)) * _decae(0.2, 0.03), k * 0.28)
    S["martillo"] = _norm(mart, 0.5)
    S["claxon_lejano"] = _norm(_filtro(S["claxon"].astype(np.float64), hi=900), 0.25)
    mu = _filtro(ruido(6.0), 250, 1300) * (0.4 + np.abs(_filtro(ruido(6.0), hi=5)) * 7)
    S["multitud"] = _norm(_bucle(mu, 300), 0.35)
    S["viento_playa"] = S["amb_playa"]

    # ------------------------------------------------- ampliación: mar y más
    mar = olas(10.0) * 0.8 + 0.5 * _filtro(ruido(10.0), 60, 400) * (0.6 + 0.4 * np.sin(PI2 * _t(10.0) / 5.0))
    S["amb_mar"] = _norm(_bucle(mar, 300), 0.5)
    campo = 0.3 * _filtro(ruido(10.0), 200, 1500) * (0.5 + 0.5 * _filtro(ruido(10.0), hi=0.4) * 25).clip(0, 2)
    for _ in range(8):
        _poner(campo, pajaro(), rng.uniform(0, 9.0), rng.uniform(0.2, 0.6))
    for t0 in (2.0, 6.5):
        _poner(campo, _nota(660, 0.5, 0.2, (1, 0.6, 0.5, 0.3)), t0, 0.25)      # cencerro lejano
    S["amb_campo"] = _norm(_bucle(campo, 300), 0.4)
    t1 = _t(1.0)
    lan = sum(np.sin(PI2 * 110 * k * t1 + rng.uniform(0, PI2)) / k ** 0.6 for k in range(1, 14))
    lan = lan * (1 + 0.4 * np.sin(PI2 * 55 * t1)) + 1.2 * _filtro(ruido(1.0), 800, 5000)
    S["motor_lancha"] = _norm(np.tanh(lan * 0.8), 0.5)
    bar_ = sum(np.sin(PI2 * 32 * k * t1 + rng.uniform(0, PI2)) / k for k in range(1, 10))
    bar_ = bar_ * (1 + 0.7 * np.sign(np.sin(PI2 * 8 * t1))) + 0.8 * _filtro(ruido(1.0), 200, 2000)
    S["motor_barco"] = _norm(np.tanh(bar_), 0.55)
    S["motor_tractor"] = _norm(np.tanh(bar_ * 1.5 + 0.5 * _filtro(ruido(1.0), 100, 900)), 0.55)
    sal = _filtro(ruido(0.9), 600, 7000) * _decae(0.9, 0.25, 0.02)
    S["salpicadura"] = _norm(sal, 0.5)
    S["pesca_lanzar"] = _norm(np.concatenate([_filtro(ruido(0.35), 2500, 9000) * np.sin(np.pi * _t(0.35) / 0.35) ** 2, np.zeros(int(SR * 0.4)), sal[: int(SR * 0.4)] * 0.5]), 0.45)
    pica = np.zeros(int(SR * 0.6))
    for k in range(5):
        _poner(pica, _nota(1760, 0.08, 0.02, (1, 0.5)), k * 0.09)
    _poner(pica, sal[: int(SR * 0.3)], 0.1, 0.4)
    S["pez_pica"] = _norm(pica, 0.6)
    car = np.zeros(int(SR * 0.9))
    for k in range(22):
        _poner(car, _filtro(ruido(0.012), 2500, 8000) * _decae(0.012, 0.004), k * 0.04)
    S["carrete"] = _norm(car, 0.4)
    boya = np.zeros(int(SR * 3.5))
    _poner(boya, sum(a * _seno(f, 2.5) * _decae(2.5, tau) for f, a, tau in ((520, 1, 0.9), (1043, 0.5, 0.5), (1570, 0.3, 0.3))), 0.2)
    _poner(boya, sal * 0.25, 2.0)
    S["lugar_boya"] = _norm(boya, 0.5)
    emb = _filtro(ruido(4.0), 300, 2500) * (0.3 + 0.7 * (0.5 - 0.5 * np.cos(PI2 * _t(4.0) / 2.0)) ** 2)
    for t0 in (0.9, 2.8):
        _poner(emb, _barrido(180, 240, 0.5, "sierra") * np.sin(np.pi * _t(0.5) / 0.5) * 0.25, t0)     # crujido de amarras
    S["lugar_embarcadero"] = _norm(_bucle(_filtro(emb, hi=3500), 200), 0.45)
    gim = np.zeros(int(SR * 3.0))
    for t0 in (0.2, 1.6):
        _poner(gim, (sum(_seno(f, 0.4) for f in (310, 742, 1190, 2030)) + _filtro(ruido(0.4), 500, 3000)) * _decae(0.4, 0.07), t0)
        _poner(gim, _filtro(ruido(0.5), 300, 1500) * np.sin(np.pi * _t(0.5) / 0.5) ** 2 * 0.3, t0 + 0.6)
    S["lugar_gimnasio"] = _norm(gim, 0.45)
    cine = _filtro(ruido(2.0), 1500, 6000) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 24 * _t(2.0)))) * 0.5
    _poner(cine, _sec([523, 659, 784], 0.15, 0.5, 0.25), 0.3, 0.6)
    S["lugar_cine"] = _norm(_bucle(cine, 80), 0.35)
    est = np.zeros(int(SR * 4.0))
    _poner(est, _bordes(_filtro(ruido(0.8), 1500, 9000) * np.linspace(1, 0.1, int(SR * 0.8)), 10), 0.2)       # frenos de aire
    _poner(est, _sec([659, 523], 0.3, 0.6, 0.3), 1.6, 0.6)                                                    # megafonía
    S["lugar_estacion"] = _norm(est, 0.4)
    sal_ = np.zeros(int(SR * 3.0))
    for k in range(3):
        _poner(sal_, _bordes(_filtro(ruido(0.7), 150, 1200) * np.sin(np.pi * _t(0.7) / 0.7) ** 2, 20), 0.2 + k * 0.9, 1 - k * 0.2)   # coches pasando
    S["lugar_salida"] = _norm(sal_, 0.4)
    S["disparo_fusil"] = disparo(350, 6500, 0.3, 0.045, 0.7)
    S["disparo_silenciado"] = _norm(_filtro(ruido(0.12), 900, 3500) * _decae(0.12, 0.02, 0.001), 0.35)
    S["lanzar"] = _norm(_filtro(ruido(0.3), 700, 3500) * np.sin(np.pi * _t(0.3) / 0.3) ** 2, 0.4)
    coh = _filtro(ruido(1.0), 300, 5000) * np.linspace(1, 0.2, SR) + 0.6 * _barrido(900, 250, 1.0, "sierra") * np.linspace(1, 0, SR)
    S["cohete"] = _norm(_bordes(coh, 15), 0.7)
    ta = _t(1.6)
    S["sirena_ambulancia"] = _norm(_filtro(np.where((ta % 0.8) < 0.4, np.sign(np.sin(PI2 * 960 * ta)), np.sign(np.sin(PI2 * 770 * ta))), hi=3500), 0.5)
    dad = np.zeros(int(SR * 0.8))
    for k in range(7):
        _poner(dad, _filtro(ruido(0.03), 1200, 5000) * _decae(0.03, 0.008), 0.05 + k * 0.09 + rng.uniform(0, 0.03), rng.uniform(0.5, 1))
    S["dados"] = _norm(dad, 0.5)
    S["caja"] = _norm(np.concatenate([_nota(1568, 0.12, 0.04, (1, 0.4)), S["dinero"].astype(np.float64)]), 0.5)
    S["sirena_barco"] = _norm(_bordes(_filtro(_sierra(98, 1.8) + _sierra(147, 1.8), hi=900), 80), 0.6)

    # ----------------------------------------------- segunda ampliación
    th = _t(1.0)
    pala = (0.5 + 0.5 * np.sign(np.sin(PI2 * 12 * th))) * np.exp(-((th * 12) % 1.0) * 4)
    heli = _filtro(ruido(1.0), 60, 900) * pala * 2.5 + 0.5 * sum(np.sin(PI2 * 180 * k * th + rng.uniform(0, PI2)) / k for k in range(1, 8))
    S["motor_helicoptero"] = _norm(np.tanh(heli), 0.6)
    bici = np.zeros(SR)
    for k in range(10):
        _poner(bici, _filtro(ruido(0.02), 3000, 9000) * _decae(0.02, 0.005), k * 0.1, 0.8)
    bici += 0.25 * _filtro(ruido(1.0), 500, 2500)
    S["motor_bici"] = _norm(bici, 0.3)
    S["claxon_bici"] = _norm(_sec([2637, 2637], 0.12, 0.3, 0.15, (1, 0.5, 0.3)), 0.5)
    S["claxon_helados"] = _norm(_sec([784, 988, 1175, 988, 784, 988, 1175, 1568], 0.14, 0.35, 0.18, (1, 0.6, 0.2)), 0.5)
    S["diana"] = _norm(_nota(1175, 0.25, 0.08, (1, 0.5, 0.3)), 0.7)
    dok = _nota(1760, 0.2, 0.06)
    _poner(dok, _filtro(ruido(0.08), 1500, 6000) * _decae(0.08, 0.02), 0.0)
    S["diana_ok"] = _norm(dok, 0.6)
    rul = np.zeros(int(SR * 2.4))
    tt = 0.05
    pos = 0.0
    while pos < 2.2:
        _poner(rul, _filtro(ruido(0.015), 2000, 7000) * _decae(0.015, 0.004), pos)
        pos += tt
        tt *= 1.12
    S["ruleta"] = _norm(rul, 0.5)
    # jugar con amigos
    S["amigo_entra"] = _norm(_sec([523, 784, 1047], 0.09, 0.5, 0.25, (1, 0.4)), 0.5)
    S["amigo_sale"] = _norm(_sec([1047, 784, 523], 0.09, 0.5, 0.25, (1, 0.4)), 0.45)
    S["chat"] = _norm(_sec([1568, 2093], 0.045, 0.2, 0.09, (1, 0.6)), 0.45)
    S["logro"] = _norm(_sec([784, 1047, 1319, 1568, 2093], 0.09, 0.6, 0.3, (1, 0.5, 0.25)), 0.6)
    S["nivel"] = _norm(_sec([659, 880, 1319], 0.1, 0.5, 0.25, (1, 0.4)), 0.5)
    S["campana_ring"] = _norm(sum(a * _seno(f, 1.2) * _decae(1.2, tau) for f, a, tau in ((1320, 1, 0.4), (2650, 0.5, 0.25), (3990, 0.3, 0.15))), 0.6)
    S["evento"] = _norm(_sec([988, 784, 988, 784], 0.11, 0.3, 0.12), 0.55)
    S["cursor_mapa"] = _norm(_seno(900, 0.04) * _decae(0.04, 0.015), 0.4)
    for k, f in enumerate((784, 587, 392, 494)):          # arriba, derecha, abajo, izquierda
        S[f"simon_{k}"] = _norm(_nota(f, 0.45, 0.18, (1, 0.5, 0.25, 0.12)), 0.7)
    prot = np.zeros(int(SR * 4.0))
    _poner(prot, S["ladrido"].astype(np.float64), 0.2, 1.0)
    _poner(prot, np.interp(np.arange(0, len(S["ladrido"]), 1.35), np.arange(len(S["ladrido"])), S["ladrido"].astype(np.float64)), 2.1, 0.7)
    S["lugar_protectora"] = _norm(prot, 0.4)

    # ------------------------------------------- vida social, sustancias y negocios
    club = np.zeros(int(SR * 2.0))
    for k in range(4):
        _poner(club, _barrido(110, 42, 0.22) * _decae(0.22, 0.07), k * 0.5)
        _poner(club, _filtro(ruido(0.05), 5000, 11000) * _decae(0.05, 0.012), k * 0.5 + 0.25, 0.3)
    club = _filtro(club, hi=700) + 0.25 * _filtro(ruido(2.0), 400, 1800) * (0.5 + np.abs(_filtro(ruido(2.0), hi=4)) * 6)
    _poner(club, _nota(2350, 0.25, 0.05, (1, 0.6)), 1.3, 0.25)          # copas que chocan
    S["lugar_club"] = _norm(_bucle(club, 40), 0.5)
    prov = np.zeros(int(SR * 3.5))
    for k in range(2):                                                    # «pst, pst»
        _poner(prov, _filtro(ruido(0.16), 3500, 9000) * np.sin(np.pi * _t(0.16) / 0.16) ** 2, 0.2 + k * 0.32, 0.8)
    _poner(prov, (sum(_seno(f, 0.5) for f in (190, 430, 910)) + _filtro(ruido(0.5), 300, 2500)) * _decae(0.5, 0.1), 1.6, 0.5)   # persiana metálica
    S["lugar_proveedor"] = _norm(prov, 0.4)
    S["afinidad_sube"] = _norm(_sec([523, 659, 784], 0.13, 0.7, 0.35, (1, 0.6, 0.3, 0.15)), 0.5)
    S["afinidad_baja"] = _norm(_sec([440, 415, 349], 0.2, 0.8, 0.4, (1, 0.5, 0.25)), 0.5)
    cor = np.zeros(int(SR * 1.6))
    for k, t0 in enumerate((0.0, 0.22, 0.75, 0.97)):
        _poner(cor, _seno(62, 0.16) * _decae(0.16, 0.05), t0, 1.0 if k % 2 == 0 else 0.7)
    _poner(cor, _sec([784, 988, 1175, 1568], 0.1, 0.6, 0.3, (1, 0.4)), 0.3, 0.35)
    S["pareja"] = _norm(cor, 0.6)
    S["ruptura"] = _norm(_sec([392, 370, 311, 262, 196], 0.28, 1.2, 0.6, (1, 0.6, 0.3)), 0.55)
    S["noche_juntos"] = _norm(_sec([392, 494, 587, 784, 587, 784, 988], 0.22, 1.4, 0.8, (1, 0.5, 0.25)), 0.45)
    S["animo_sube"] = _norm(_sec([659, 880], 0.09, 0.3, 0.14, (1, 0.3)), 0.4)
    S["animo_baja"] = _norm(_sec([440, 330], 0.11, 0.35, 0.16, (1, 0.5)), 0.4)
    S["fama"] = _norm(_sec([330, 440, 554, 659], 0.07, 0.4, 0.2, (1, 0.7, 0.5, 0.3)), 0.5)
    copa = np.zeros(int(SR * 1.3))
    _poner(copa, _filtro(ruido(0.6), 1500, 6000) * np.linspace(0.2, 1, int(SR * 0.6)) * (0.6 + 0.4 * np.sin(PI2 * 14 * _t(0.6))), 0.0, 0.6)   # servir
    _poner(copa, _nota(2100, 0.4, 0.12, (1, 0.5, 0.2)) + _nota(2790, 0.4, 0.1, (0.6, 0.2)), 0.75)                                            # brindis
    S["tomar_copa"] = _norm(copa, 0.5)
    hum = np.zeros(int(SR * 1.6))
    _poner(hum, _filtro(ruido(0.05), 2500, 9000) * _decae(0.05, 0.01), 0.0)                                       # mechero
    _poner(hum, _filtro(ruido(0.7), 700, 3000) * np.sin(np.pi * _t(0.7) / 0.7) ** 2, 0.25, 0.7)                   # calada
    _poner(hum, _filtro(ruido(0.5), 300, 1500) * np.sin(np.pi * _t(0.5) / 0.5) ** 2, 1.05, 0.5)                   # soltar el humo
    S["tomar_hierba"] = _norm(hum, 0.45)
    past = np.zeros(int(SR * 0.9))
    _poner(past, _filtro(ruido(0.04), 3000, 9000) * _decae(0.04, 0.008), 0.0)                                     # blíster
    _poner(past, _filtro(ruido(0.04), 3000, 9000) * _decae(0.04, 0.008), 0.12, 0.7)
    _poner(past, _barrido(260, 150, 0.18) * _decae(0.18, 0.06), 0.5, 0.9)                                         # tragar
    S["tomar_pastillas"] = _norm(past, 0.5)
    esn = np.zeros(int(SR * 1.0))
    for k in range(3):
        _poner(esn, _filtro(ruido(0.02), 2000, 7000) * _decae(0.02, 0.005), k * 0.09, 0.6)                        # picar con una tarjeta
    _poner(esn, _filtro(ruido(0.4), 1800, 8000) * np.linspace(0.3, 1, int(SR * 0.4)) ** 2, 0.45)                 # inspirar
    S["tomar_polvo"] = _norm(esn, 0.45)
    cri = np.zeros(int(SR * 1.5))
    _poner(cri, _filtro(ruido(0.05), 2500, 9000) * _decae(0.05, 0.01), 0.0)
    _poner(cri, _filtro(ruido(0.8), 2500, 9000) * (0.4 + 0.6 * np.abs(_filtro(ruido(0.8), hi=30)) * 4), 0.15, 0.5)   # crepitar
    _poner(cri, _filtro(ruido(0.4), 500, 2500) * np.sin(np.pi * _t(0.4) / 0.4) ** 2, 1.0, 0.6)
    S["tomar_cristal"] = _norm(cri, 0.45)
    S["bajon"] = _norm(_filtro(_barrido(330, 90, 1.6, "sierra"), hi=900) * np.sin(np.pi * _t(1.6) / 1.6), 0.5)
    tem = _seno(140, 1.2) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 11 * _t(1.2)))) * np.sin(np.pi * _t(1.2) / 1.2)
    S["abstinencia"] = _norm(tem + 0.3 * _filtro(ruido(1.2), 200, 900), 0.5)
    sob = np.zeros(int(SR * 3.2))
    for k, t0 in enumerate((0.0, 0.5, 1.15, 1.95)):
        _poner(sob, _seno(58, 0.18) * _decae(0.18, 0.06), t0, 1.0 - 0.15 * k)
    _poner(sob, _bordes(_seno(1000, 1.0), 20), 2.2, 0.35)                                                         # pitido continuo de monitor
    S["sobredosis"] = _norm(sob, 0.7)
    trato = np.zeros(int(SR * 0.9))
    for k in range(5):
        _poner(trato, _filtro(ruido(0.05), 1500, 6000) * _decae(0.05, 0.015), k * 0.09, 0.7)                      # contar billetes
    _poner(trato, _filtro(ruido(0.12), 400, 2000) * _decae(0.12, 0.04), 0.55, 0.8)                                # el paquete cambia de manos
    S["trato"] = _norm(trato, 0.5)
    S["rechazo"] = _norm(vocal(170, 120, 0.22, (500, 1300), 0.12), 0.4)
    plc = np.zeros(int(SR * 1.1))
    _poner(plc, _bordes(_filtro(ruido(0.25), 700, 2600, 6), 8), 0.0)                                             # emisora
    _poner(plc, _bordes(_seno(1700, 0.08), 4), 0.3, 0.6)
    _poner(plc, S["esposas"].astype(np.float64), 0.45, 0.7)
    S["paisano"] = _norm(plc, 0.5)
    S["precio_ganga"] = _norm(_sec([1319, 1047, 784], 0.07, 0.3, 0.12, (1, 0.3)), 0.4)
    S["precio_escasez"] = _norm(_sec([784, 1047, 1319], 0.07, 0.3, 0.12, (1, 0.3)), 0.4)
    S["perro_olfatea"] = _norm(np.concatenate([_filtro(ruido(0.09), 1500, 6000) * np.sin(np.pi * _t(0.09) / 0.09) for _ in range(4)]), 0.4)
    S["bolsa"] = _norm(_sec([988, 988, 1319], 0.08, 0.25, 0.08, (1, 0.5)), 0.4)
    S["territorio"] = _norm(_sec([196, 247, 294, 392, 494, 587], 0.11, 0.9, 0.5, (1, 0.8, 0.6, 0.4)), 0.65)
    S["cita"] = _norm(_sec([587, 740, 880, 740, 1175], 0.14, 0.6, 0.3, (1, 0.4, 0.2)), 0.45)
    S["regalo"] = _norm(_filtro(ruido(0.3), 2500, 9000) * np.sin(np.pi * _t(0.3) / 0.3) * 0.5, 0.35)

    # ------------------------------------------- puertas, horas del día y vida honrada
    pt = np.zeros(int(SR * 1.1))
    _poner(pt, _filtro(ruido(0.25), 150, 1200) * np.sin(np.pi * _t(0.25) / 0.25), 0.0, 0.7)            # la puerta se abre
    _poner(pt, _nota(1976, 0.5, 0.2, (1, 0.4)), 0.2, 0.8)                                              # campanilla
    _poner(pt, _nota(2349, 0.5, 0.2, (1, 0.4)), 0.33, 0.6)
    S["puerta_entrar"] = _norm(pt, 0.5)
    ps = np.zeros(int(SR * 0.7))
    _poner(ps, _nota(2349, 0.3, 0.1, (1, 0.4)), 0.0, 0.5)
    _poner(ps, _seno(105, 0.2) * _decae(0.2, 0.05) + 0.6 * _filtro(ruido(0.2), 300, 2000) * _decae(0.2, 0.03), 0.3)   # se cierra
    S["puerta_salir"] = _norm(ps, 0.5)
    cam2 = np.zeros(int(SR * 4.2))
    for k in range(3):
        _poner(cam2, sum(a * _seno(f, 2.2) * _decae(2.2, tau) for f, a, tau in ((262, 1, 0.9), (525, 0.6, 0.6), (790, 0.4, 0.4), (1050, 0.25, 0.25))), k * 1.0)
    S["campanadas"] = _norm(cam2, 0.45)
    ga = np.concatenate([vocal(600, 900, 0.18, (1100, 2200), 0.3), vocal(900, 950, 0.12, (1200, 2400), 0.3), vocal(950, 1100, 0.3, (1300, 2600), 0.4), vocal(1100, 500, 0.5, (1100, 2200), 0.3)])
    S["gallo"] = _norm(ga, 0.4)
    bu = np.zeros(int(SR * 1.6))
    for t0, d_ in ((0.0, 0.25), (0.4, 0.2), (0.7, 0.5)):
        _poner(bu, _seno(330, d_) * np.sin(np.pi * _t(d_) / d_) * (1 + 0.3 * _seno(6, d_)), t0)
    S["buho"] = _norm(bu, 0.35)
    S["agacharse"] = _norm(_filtro(ruido(0.25), 300, 2500) * np.linspace(1, 0.1, int(SR * 0.25)), 0.3)
    S["levantarse"] = _norm(_filtro(ruido(0.25), 300, 2500) * np.linspace(0.1, 1, int(SR * 0.25)), 0.3)
    hd = np.zeros(int(SR * 2.6))
    for k in range(3):
        _poner(hd, _bordes(_seno(1000, 0.09), 4), 0.2 + k * 0.8, 0.8)
    _poner(hd, _filtro(ruido(0.8), 300, 1500) * np.sin(np.pi * _t(0.8) / 0.8) ** 2 * 0.4, 1.4)        # una respiración
    S["hospital_despertar"] = _norm(hd, 0.45)
    ce = (sum(_seno(f, 0.9) for f in (160, 370, 910, 1730)) + 1.5 * _filtro(ruido(0.9), 150, 2500)) * _decae(0.9, 0.16, 0.001)
    S["celda"] = _norm(np.tanh(ce), 0.7)
    S["ascenso"] = _norm(_sec([392, 523, 659, 784, 1047], 0.12, 0.8, 0.45, (1, 0.7, 0.4, 0.2)), 0.6)
    S["diploma"] = _norm(_sec([523, 659, 784, 659, 784, 1047], 0.13, 0.6, 0.3, (1, 0.4, 0.2)), 0.5)
    don = np.zeros(int(SR * 0.9))
    for k in range(4):
        _poner(don, _nota(float(rng.uniform(2800, 4200)), 0.2, 0.05, (1, 0.5)), 0.05 + k * 0.13 + float(rng.uniform(0, 0.03)), 0.8)   # monedas
    S["donativo"] = _norm(don, 0.45)
    S["prestigio"] = _norm(_sec([659, 784, 988], 0.11, 0.5, 0.25, (1, 0.5, 0.25)), 0.45)
    S["jornada"] = _norm(np.concatenate([_filtro(_cuadrada(520, 0.5), hi=2500) * _decae(0.5, 0.6, 0.02), np.zeros(int(SR * 0.15)), S["pasan_horas"].astype(np.float64)]), 0.45)   # sirena de fábrica y pasan las horas
    of = np.zeros(int(SR * 3.0))
    for t0, g in zip(np.sort(rng.uniform(0, 2.2, 10)), rng.uniform(0.4, 1, 10)):
        _poner(of, _filtro(ruido(0.03), 1500, 5000) * _decae(0.03, 0.006), float(t0), float(g))        # teclado
    _poner(of, _bordes(_seno(880, 0.12), 5) + _bordes(_seno(1100, 0.12), 5), 2.5, 0.5)                 # turno siguiente
    S["lugar_empleo"] = _norm(of, 0.4)
    ac = np.zeros(int(SR * 3.5))
    _poner(ac, sum(a * _seno(f, 1.2) * _decae(1.2, 0.4) for f, a in ((1568, 1), (3140, 0.4))), 0.1)    # timbre de clase
    _poner(ac, _filtro(ruido(1.2), 300, 1400) * (0.4 + np.abs(_filtro(ruido(1.2), hi=6)) * 6) * 0.5, 1.6)   # murmullo
    S["lugar_academia"] = _norm(ac, 0.4)
    ong = np.zeros(int(SR * 3.0))
    for k in range(4):
        _poner(ong, _nota(float(rng.uniform(1500, 2600)), 0.25, 0.06, (1, 0.5)), 0.2 + k * 0.45, 0.7)   # platos y cubiertos
    _poner(ong, _filtro(ruido(1.5), 300, 1200) * 0.25, 1.2)
    S["lugar_ong"] = _norm(ong, 0.4)
    hp = np.zeros(int(SR * 3.0))
    _poner(hp, _filtro(ruido(1.6), 80, 700) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 11 * _t(1.6)))) * np.sin(np.pi * _t(1.6) / 1.6) ** 2, 0.2)
    _poner(hp, _bordes(_seno(1100, 0.12), 6), 2.2, 0.5)
    S["lugar_helipuerto"] = _norm(hp, 0.45)
    pris = np.zeros(int(SR * 4.0))
    _poner(pris, (sum(_seno(f, 0.6) for f in (240, 610, 1390)) + _filtro(ruido(0.6), 300, 2500)) * _decae(0.6, 0.12), 0.3)      # reja
    _poner(pris, S["sirena_lejana"].astype(np.float64)[: int(SR * 1.2)], 2.2, 1.5)
    S["lugar_prision"] = _norm(pris, 0.45)
    mina = np.zeros(int(SR * 3.0))
    for t0 in (0.2, 0.9, 1.6):
        _poner(mina, (sum(_seno(f, 0.25) for f in (830, 1670, 2900)) + _filtro(ruido(0.25), 1000, 5000)) * _decae(0.25, 0.04), t0)   # pico
    _poner(mina, _filtro(ruido(0.8), 60, 500) * _decae(0.8, 0.3), 2.1, 0.8)                                                           # derrumbe
    S["lugar_mina"] = _norm(mina, 0.45)
    rio = _filtro(ruido(4.0), 500, 5000) * (0.7 + 0.3 * np.abs(_filtro(ruido(4.0), hi=10)) * 5)
    S["lugar_rio"] = _norm(_bucle(rio, 200), 0.4)
    mont = 0.5 * _filtro(ruido(10.0), 100, 900) * (0.4 + 0.6 * (0.5 - 0.5 * np.cos(PI2 * _t(10.0) / 5.0)))
    for _ in range(3):
        _poner(mont, pajaro(), rng.uniform(0, 9.0), 0.25)
    S["amb_montana"] = _norm(_bucle(mont, 300), 0.4)
    return S


# Sonidos que el juego reproduce en bucle: si los sustituyes, el final debe empalmar con el principio.
PREFIJOS_BUCLE = ("amb_", "motor_", "lugar_", "loc_")
BUCLES = {"rodadura", "alarma", "sirena", "sirena_ambulancia", "fuego", "ganzua", "intermitente", "lluvia", "latido", "multitud"}


def es_bucle(nombre):
    return nombre in BUCLES or nombre.startswith(PREFIJOS_BUCLE)


def leer_audio(ruta, mono=True):
    """Lee un archivo de audio y lo adapta al motor: 44100 Hz, mono si hace falta."""
    import soundfile as sf
    d, sr = sf.read(ruta, dtype="float32", always_2d=True)
    if mono:
        d = d.mean(axis=1)
    elif d.shape[1] == 1:
        d = np.repeat(d, 2, axis=1)
    else:
        d = d[:, :2]
    if sr != SR and len(d) > 1:
        n = max(2, int(len(d) * SR / sr))
        x = np.linspace(0, len(d) - 1, n)
        base = np.arange(len(d))
        if d.ndim == 1:
            d = np.interp(x, base, d)
        else:
            d = np.stack([np.interp(x, base, d[:, 0]), np.interp(x, base, d[:, 1])], axis=1)
    return np.ascontiguousarray(d, dtype=np.float32)


def escribir_wav(ruta, datos):
    import soundfile as sf
    sf.write(ruta, np.clip(datos, -1.0, 1.0), SR, subtype="PCM_16")


def cargar(mezclador, carpeta):
    """Carga todos los sonidos de data/sonidos. Los que falten se generan y se guardan como WAV.

    Cada sonido es un archivo con su nombre: para cambiar uno basta con sustituir el archivo
    (WAV, OGG, FLAC o MP3). Si se borra un archivo, el juego vuelve a crear el original.
    """
    os.makedirs(carpeta, exist_ok=True)
    S = {}
    for f in sorted(os.listdir(carpeta)):
        nombre, ext = os.path.splitext(f)
        if ext.lower() in (".wav", ".ogg", ".flac", ".mp3") and nombre not in S:
            try:
                d = leer_audio(os.path.join(carpeta, f))
                if len(d) > 8:
                    S[nombre] = d
            except Exception:
                pass
    marca = os.path.join(carpeta, "_version.txt")
    try:
        al_dia = open(marca, encoding="utf-8").read().strip() == str(VERSION_CACHE)
    except OSError:
        al_dia = False
    if not al_dia or not S:
        originales = generar()
        for nombre, d in originales.items():
            if nombre not in S:
                S[nombre] = d
                try:
                    escribir_wav(os.path.join(carpeta, nombre + ".wav"), d)
                except Exception:
                    pass
        try:
            open(marca, "w", encoding="utf-8").write(str(VERSION_CACHE))
        except OSError:
            pass
    else:
        # si el jugador ha borrado algún archivo, se recupera el original
        faltan = None
        for nombre in NOMBRES_BASICOS:
            if nombre not in S:
                faltan = faltan or generar()
                if nombre in faltan:
                    S[nombre] = faltan[nombre]
                    try:
                        escribir_wav(os.path.join(carpeta, nombre + ".wav"), faltan[nombre])
                    except Exception:
                        pass
        if faltan:
            for nombre, d in faltan.items():
                if nombre not in S:
                    S[nombre] = d
                    try:
                        escribir_wav(os.path.join(carpeta, nombre + ".wav"), d)
                    except Exception:
                        pass
    for k, v in S.items():
        mezclador.registrar(k, v)
    return S


# Sonidos sin los que el juego no puede funcionar bien: si falta alguno, se regeneran todos los que falten.
NOMBRES_BASICOS = ("menu_mover", "menu_ok", "baliza", "paso_acera0", "motor_coche", "disparo_pistola", "amb_ciudad", "cruce", "radar", "llegada")
