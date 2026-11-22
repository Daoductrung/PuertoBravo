"""Monta un pack de sonidos entero generado con genny (https://github.com/ogomez92/genny): cada sonido del juego
sale de una receta de genny, sin grabaciones ni sonidos del juego.

    python herramientas\\pack_genny.py recetas CARPETA        escribe CARPETA\\genny_lote.json, las recetas de genny
    genny render CARPETA\\genny_lote.json                    (con genny instalado) las convierte en WAV
    .venv\\Scripts\\python.exe herramientas\\pack_genny.py montar CARPETA DESTINO
                                                            pasa los WAV a FLAC en DESTINO, con pack.json y CREDITOS.txt

Las recetas van por familias, con la lógica del juego: lo que orienta son señales cortas y estables; lo bueno sube
y lo malo baja; lo que va en pareja (entrar y salir, sube y baja) es la imagen de su contrario; los objetos suenan a
lo que son; los bucles duran lo que el juego repite. Ningún sonido repite la receta de otro.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


# ------------------------------------------------------------------ piezas de las recetas
def sfx(_genny, at=0.0, gain=1.0, fx=None, **params):
    d = {"type": "sfx", "kind": _genny, "at": at, "gain": gain, "params": params}
    if fx:
        d["fx"] = fx
    return d


def drum(kind, at=0.0, gain=1.0, vel=1.0, fx=None, **params):
    d = {"type": "drum", "kind": kind, "at": at, "gain": gain, "vel": vel, "params": params}
    if fx:
        d["fx"] = fx
    return d


def seq(inst, steps, at=0.0, gain=1.0, vel=0.8, fx=None, **params):
    d = {"type": "seq", "inst": inst, "steps": steps, "at": at, "gain": gain, "vel": vel, "params": params}
    if fx:
        d["fx"] = fx
    return d


def nota(inst, notes, dur=0.3, at=0.0, gain=1.0, vel=0.8, fx=None, **params):
    d = {"type": "synth", "inst": inst, "notes": notes, "dur": dur, "at": at, "gain": gain, "vel": vel, "params": params}
    if fx:
        d["fx"] = fx
    return d


def voz(text, at=0.0, gain=1.0, fx=None, **params):
    d = {"type": "speech", "text": text, "at": at, "gain": gain, "params": params}
    if fx:
        d["fx"] = fx
    return d


def rev(mix=0.15, size=0.3):
    return {"type": "reverb", "mix": mix, "size": size}


def lp(cutoff):
    return {"type": "lowpass", "cutoff": cutoff}


def hp(cutoff):
    return {"type": "highpass", "cutoff": cutoff}


def bp(center, q=1.0):
    return {"type": "bandpass", "center": center, "q": q}


LEJOS = [lp(1800), {"type": "reverb", "mix": 0.3, "size": 0.7}]


RECETAS = {}


def r(nombre, capas, fx=None, dur=None, loop=None, mono=True):
    """Una receta. Con loop, el sonido se repite sin costura: dur es lo que dura la vuelta."""
    spec = {"out": nombre + ".wav", "layers": capas, "normalize": -1.0}
    cadena = list(fx or [])
    if mono:
        cadena.append({"type": "mono"})
    spec["fx"] = cadena
    if dur is not None:
        spec["duration"] = dur
    if loop is not None:
        spec["loop"] = loop
    assert nombre not in RECETAS, nombre
    RECETAS[nombre] = spec


# ================================================================== orientación: señales cortas, estables y claras
r("baliza", [nota("marimba", "E6", 0.25, vel=0.7), sfx("blip", freq=2600, dur=0.03, gain=0.25)])
r("baliza_destino", [seq("marimba", "E6:0.09 B6:0.3", vel=0.7), sfx("blip", freq=3000, dur=0.03, gain=0.25)])
r("llegada", [seq("celesta", "C5:0.08 E5:0.08 G5:0.08 C6:0.5", vel=0.7)], fx=[rev(0.2, 0.4)])
r("cruce", [seq("xylophone", "G5:0.06 B5:0.25", vel=0.6)])
r("radar", [sfx("blip", freq=1250, dur=0.05)])
r("tono_pared", [sfx("beep", freq=780, dur=0.13, wave="triangle")])
r("tono_libre", [sfx("beep", freq=1180, dur=0.06, wave="sine")])
r("semaforo_tic", [sfx("click", tone=2800)])
r("semaforo_pio", [sfx("chirp", start=2900, end=1900, dur=0.09, wave="sine")])
r("semaforo_rojo", [seq("marimba", "B4:0.11 F#4:0.35", vel=0.8)])
r("semaforo_verde", [seq("marimba", "A5:0.08 E6:0.28", vel=0.7)])
r("cursor_mapa", [sfx("switch", state="on", seed=3, fx=[hp(800)])])
r("sonar", [sfx("beep", freq=1500, dur=0.045, wave="sine")])
r("bordillo", [sfx("steel_ball", surface="rubber", force=0.8, seed=2), sfx("hit", dur=0.1, tone=90, crunch=0.2, gain=0.5)])
r("loc_mision", [nota("vibraphone", "E5", 0.5, at=0.0, vel=0.6), nota("vibraphone", "B5", 0.5, at=0.75, vel=0.5)], dur=1.5, loop=0.05)
r("loc_objeto", [sfx("magic", dur=1.2, density=6, freq="G6", gain=0.6), sfx("blip", freq=2400, dur=0.03, at=0.0, gain=0.3)], dur=1.2, loop=0.05)
r("loc_casete", [seq("music_box", "C6:0.4 E6:0.4 G6:0.4 E6:0.4", vel=0.6)], dur=1.6, loop=0.05)
r("loc_vehiculo", [sfx("car_engine", rpm=700, cylinders=4, load=0.15, dur=2.1, seed=11, gain=0.6), sfx("blip", freq=2000, dur=0.05, at=0.2), sfx("blip", freq=2000, dur=0.05, at=0.32)], dur=1.8, loop=0.3)
r("loc_lugar", [nota("kalimba", "D5", 0.6, vel=0.6), nota("kalimba", "A5", 0.6, at=1.0, vel=0.5)], dur=2.0, loop=0.05)

# ================================================================== los lugares: cada tipo, su firma (bucles)
r("puerta_entrar", [sfx("door"), drum("triangle", at=0.12, gain=0.5, vel=0.6), drum("finger_cymbals", at=0.2, gain=0.3, vel=0.5)])
r("puerta_salir", [drum("finger_cymbals", gain=0.3, vel=0.5), drum("triangle", at=0.06, gain=0.5, vel=0.6), sfx("door", at=0.35)])
r("lugar_academia", [sfx("phone_ring", dur=1.1, pattern="single", seed=4, gain=0.7)], fx=[rev(0.2, 0.5)], dur=3.5, loop=0.1)
r("lugar_aeropuerto", [seq("vibraphone", "E5:0.45 C5:0.45 A4:0.9", vel=0.6)], fx=[rev(0.35, 0.8)], dur=3.0, loop=0.2)
r("lugar_armeria", [sfx("reload", action="rack", seed=5), sfx("reload", action="rack", seed=9, at=1.4, gain=0.7)], dur=2.6, loop=0.05)
r("lugar_banco", [sfx("beep", freq=1100, dur=0.09, at=0.2), sfx("beep", freq=1100, dur=0.09, at=0.45), sfx("beep", freq=1480, dur=0.15, at=0.7),
                  sfx("receipt_printer", dur=0.5, at=1.1, gain=0.5)], dur=2.4, loop=0.05)
r("lugar_bar", [{"type": "pattern", "kind": "kick", "steps": "x---x---x---x---", "step": 0.125},
                seq("bass", "A1:0.25 A1:0.25 C2:0.25 E2:0.25 A1:0.25 A1:0.25 G1:0.25 E1:0.25", gain=0.7)],
  fx=[{"type": "muffle", "amount": 0.8}], dur=2.0, loop=0.05)
r("lugar_boya", [sfx("waves", dur=4.0, size=0.3, period=3.6, seed=2, gain=0.6), nota("tubular_bell", "D5", 2.0, at=0.4, vel=0.5, gain=0.5)],
  fx=[rev(0.25, 0.7)], dur=3.5, loop=0.3)
r("lugar_casa", [drum("windchimes", gain=0.7), drum("windchimes", at=2.0, gain=0.5, vel=0.7)],
  fx=[rev(0.2, 0.5)], dur=4.0, loop=0.3)
r("lugar_casino", [sfx("slot_machine", dur=1.4, reels=3), seq("board", "C5:0.08 E5:0.08 G5:0.08 C6:0.2", at=1.6, vel=0.5, gain=0.4)], dur=2.4, loop=0.05)
r("lugar_cine", [sfx("projector", dur=2.3)], dur=1.92, loop=0.3)
r("lugar_club", [{"type": "pattern", "kind": "kick909", "steps": "x---x---x---x---", "step": 0.12},
                 {"type": "pattern", "kind": "openhat", "steps": "--x---x---x---x-", "step": 0.12, "gain": 0.25},
                 nota("glass", "E6", 0.3, at=1.2, vel=0.4, gain=0.3)], fx=[{"type": "muffle", "amount": 0.65}], dur=1.96, loop=0.05)
r("lugar_comida", [sfx("sizzle", dur=2.3, heat=0.35, gain=0.6), drum("ride_bell", at=0.5, gain=0.2, vel=0.4), sfx("coins", count=2, surface="metal", seed=8, at=1.2, gain=0.3)], dur=1.94, loop=0.3)
r("lugar_comisaria", [sfx("static", dur=0.25, color="pink", gain=0.5), sfx("beep", freq=1200, dur=0.07, at=0.3), sfx("beep", freq=1500, dur=0.07, at=0.42),
                      sfx("static", dur=0.15, color="pink", at=1.8, gain=0.4)], fx=[{"type": "telephone"}], dur=3.0, loop=0.05)
r("lugar_contacto", [seq("felt_piano", "D4:0.3 F4:0.3 A4:0.6", vel=0.5)], fx=[rev(0.2, 0.4)], dur=1.5, loop=0.05)
r("lugar_embarcadero", [sfx("waves", dur=4.2, size=0.25, period=3.8, seed=5, gain=0.6), sfx("creak", dur=1.0, pitch=0.7, at=1.4, gain=0.5)], dur=3.8, loop=0.3)
r("lugar_empleo", [sfx("keyboard", seed=1, at=0.1), sfx("keyboard", seed=2, at=0.32), sfx("keyboard", seed=3, at=0.5), sfx("keyboard", seed=4, at=0.66),
                   sfx("doorbell", high="G5", low="G5", gap=0.2, at=1.5, gain=0.4)], dur=3.0, loop=0.05)
r("lugar_estacion", [sfx("air_brake", dur=0.9), seq("vibraphone", "C5:0.35 E5:0.35 G5:0.7", at=1.6, vel=0.5, gain=0.6)], fx=[rev(0.25, 0.7)], dur=4.0, loop=0.1)
r("lugar_fuente", [sfx("rain", dur=3.3, intensity=1.0, seed=6, fx=[lp(3500)]), sfx("water_drip", pitch=1.2, seed=2, at=1.0, gain=0.4)], dur=2.94, loop=0.3)
r("lugar_generico", [nota("steel_tongue", "G4", 0.8, vel=0.5), nota("steel_tongue", "D5", 0.8, at=1.0, vel=0.4)], dur=2.0, loop=0.05)
r("lugar_gimnasio", [drum("anvil", gain=0.6), drum("anvil", at=1.2, gain=0.5), sfx("grunt", kind="effort", at=1.05, gain=0.5)], fx=[rev(0.15, 0.5)], dur=3.0, loop=0.05)
r("lugar_helipuerto", [sfx("helicopter", dur=3.3, rate=9.0, gain=0.6), sfx("beep", freq=900, dur=0.12, at=1.5, gain=0.5)], dur=3.0, loop=0.3)
r("lugar_hospital", [sfx("heart_monitor", rate=60, dur=1.0)], dur=1.0, loop=0.02)
r("lugar_iglesia", [nota("tubular_bell", "G4", 3.0, vel=0.6)], fx=[rev(0.3, 0.8)], dur=3.5, loop=0.3)
r("lugar_mina", [sfx("pickaxe", hits=3)], fx=[rev(0.25, 0.6)], dur=3.0, loop=0.05)
r("lugar_ong", [sfx("coins", count=3, surface="metal", seed=4, gain=0.5), drum("ride_bell", at=0.9, gain=0.3, vel=0.4),
                sfx("knife_chop", chops=3, rate=6, at=1.6, gain=0.5)], fx=[rev(0.15, 0.4)], dur=3.0, loop=0.05)
r("lugar_periodico", [sfx("typewriter", at=0.0), sfx("typewriter", at=0.14), sfx("typewriter", at=0.3), sfx("typewriter", at=0.41),
                      sfx("typewriter", at=0.58), sfx("typewriter", at=1.1), sfx("typewriter", at=1.25)], dur=2.0, loop=0.05)
r("lugar_prision", [sfx("cell_door", size=0.8), sfx("siren", low=450, high=700, rate=0.5, dur=1.8, at=1.6, gain=0.25, fx=LEJOS)], dur=4.0, loop=0.1)
r("lugar_protectora", [sfx("bark", size=0.3, barks=2, seed=1), sfx("bark", size=0.8, barks=1, seed=2, at=1.6, gain=0.7)], fx=[rev(0.15, 0.5)], dur=4.0, loop=0.05)
r("lugar_proveedor", [sfx("air_brake", dur=0.35, seed=3, gain=0.5), sfx("air_brake", dur=0.35, seed=4, at=0.5, gain=0.5),
                      sfx("roller_shutter", dur=1.2, direction="up", at=1.2, gain=0.7)], dur=3.5, loop=0.05)
r("lugar_rio", [sfx("stream", dur=4.1, flow=0.4, seed=8)], dur=3.8, loop=0.3)
r("lugar_salida", [sfx("tire_roll", dur=3.3, speed=0.9),
                   sfx("whoosh", dur=0.9, low=150, high=1500, at=0.6, gain=0.6), sfx("whoosh", dur=0.8, low=120, high=1200, direction="down", at=2.0, gain=0.5)],
  dur=3.0, loop=0.3)
r("lugar_taller", [sfx("impact_wrench", dur=0.7, bursts=2)], dur=3.0, loop=0.05)
r("lugar_taxi", [sfx("car_horn", dur=0.15, honks=2, freq=470)], fx=[rev(0.15, 0.5)], dur=2.5, loop=0.05)
r("lugar_tienda", [drum("sleigh", gain=0.6, vel=0.7), nota("glockenspiel", "G6", 0.5, at=0.08, vel=0.4, gain=0.4)], fx=[rev(0.15, 0.4)], dur=3.2, loop=0.05)
r("lugar_tranvia", [sfx("bike_bell", rings=1, seed=3, fx=[{"type": "speed", "factor": 0.6}]), sfx("bike_bell", rings=1, seed=4, at=0.45, fx=[{"type": "speed", "factor": 0.6}])],
  fx=[rev(0.2, 0.5)], dur=2.4, loop=0.05)
r("lugar_tren", [sfx("train", dur=2.7, speed=0.15, seed=1, gain=0.7), sfx("air_brake", dur=0.7, seed=9, at=1.4, gain=0.5)], dur=2.4, loop=0.3)

# ================================================================== a pie
for k in (0, 1):
    r(f"paso_acera{k}", [sfx("footfall", surface="concrete", steps=1, weight=0.45, seed=10 + k)])
    r(f"paso_calzada{k}", [sfx("footfall", surface="concrete", steps=1, weight=0.6, seed=20 + k, fx=[lp(2500)]), sfx("noise", dur=0.06, color="brown", gain=0.2)])
    r(f"paso_hierba{k}", [sfx("footfall", surface="grass", steps=1, weight=0.5, seed=30 + k)])
    r(f"paso_arena{k}", [sfx("footfall", surface="sand", steps=1, weight=0.5, seed=40 + k)])
    r(f"paso_muelle{k}", [sfx("footfall", surface="wood", steps=1, weight=0.55, seed=50 + k)])
    r(f"paso_plaza{k}", [sfx("footfall", surface="concrete", steps=1, weight=0.35, seed=60 + k, fx=[hp(300)]), drum("clave", gain=0.15, vel=0.4)])
    r(f"paso_via{k}", [sfx("footfall", surface="gravel", steps=1, weight=0.5, seed=70 + k), sfx("steel_ball", surface="metal", force=0.8, seed=71 + k, gain=1.0)])
r("choque_pared", [sfx("punch", dur=0.15), sfx("knock", count=1, surface="wood", force=0.9, seed=3, gain=0.5)])
r("agacharse", [sfx("cloth", dur=0.25, weight=0.7, seed=1), sfx("footfall", surface="concrete", weight=0.2, seed=5, at=0.12, gain=0.3)])
r("levantarse", [sfx("footfall", surface="concrete", weight=0.2, seed=6, gain=0.3), sfx("cloth", dur=0.25, weight=0.5, seed=2, at=0.05)])
r("salpicadura", [sfx("splash", size=0.6, seed=1)])
r("brazada", [sfx("splash", size=0.15, seed=4), sfx("whoosh", dur=0.3, low=200, high=1200, gain=0.2)])
r("bajo_agua", [sfx("noise", dur=3.5, color="brown", gain=0.6), sfx("bubble", freq=300, at=0.4), sfx("bubble", freq=420, at=1.3), sfx("bubble", freq=260, at=2.2)],
  fx=[{"type": "underwater", "amount": 0.8}], dur=3.0, loop=0.3)

# ================================================================== conducir: motores (bucles) y lo que pasa al volante
r("motor_coche", [sfx("car_engine", rpm=1000, cylinders=4, load=0.35, dur=1.4, seed=7)], dur=1.0, loop=0.3)
r("motor_deportivo", [sfx("car_engine", rpm=1200, cylinders=8, load=0.5, rough=0.35, pipe=0.006, bright=0.2, dur=1.4, seed=3)], dur=1.0, loop=0.3)
r("motor_moto", [sfx("car_engine", rpm=1300, cylinders=1, load=0.6, rough=0.5, pipe=0.003, bright=0.25, dur=1.4, seed=5)], dur=1.0, loop=0.3)
r("motor_camion", [sfx("car_engine", rpm=470, cylinders=6, load=0.8, rough=0.6, pipe=0.011, dur=1.4, seed=9, fx=[lp(900)]), sfx("tone", freq=1300, dur=1.4, wave="sine", gain=0.03)], dur=1.0, loop=0.3)
r("motor_furgoneta", [sfx("car_engine", rpm=980, cylinders=5, load=0.4, rough=0.3, pipe=0.006, dur=1.4, seed=13), sfx("ball_roll", speed=0.3, dur=1.4, seed=6, gain=0.35)], dur=1.0, loop=0.3)
r("motor_tractor", [sfx("car_engine", rpm=450, cylinders=2, load=0.6, rough=0.6, pipe=0.008, dur=1.4, seed=17)], dur=1.0, loop=0.3)
r("motor_bici", [sfx("bike_chain", dur=1.4, speed=0.5)], dur=1.0, loop=0.3)
r("rodadura", [sfx("tire_roll", dur=1.8, speed=0.5)], dur=1.44, loop=0.3)
r("arranque", [sfx("car_engine", rpm=260, cylinders=4, load=0.3, rough=0.9, dur=0.45, seed=7), sfx("car_engine", rpm=2400, cylinders=4, load=0.6, dur=0.45, seed=7, at=0.45)])
r("puerta_coche", [sfx("door", gain=0.9), sfx("solenoid", size=0.3, metal=0.4, thump=0.6, seed=4, gain=0.4)])
r("claxon", [sfx("car_horn", dur=0.4, honks=1, freq=420)])
r("claxon_camion", [sfx("car_horn", dur=0.65, honks=1, freq=230)], fx=[rev(0.1, 0.4)])
r("claxon_bici", [sfx("bike_bell", rings=2)])
r("claxon_helados", [seq("music_box", "G5:0.18 C6:0.18 E6:0.18 G6:0.18 E6:0.18 C6:0.18 G5:0.35", vel=0.6)], fx=[rev(0.15, 0.4)])
r("frenazo", [sfx("tire_squeal", dur=0.9)])
r("choque", [sfx("hit", dur=0.4, tone=90, crunch=0.9), sfx("glass_break", size=0.3, seed=3, at=0.04, gain=0.4), drum("crash", at=0.0, gain=0.3, vel=0.6)])
r("choque_leve", [sfx("hit", dur=0.25, tone=140, crunch=0.3), sfx("steel_ball", surface="plastic", force=0.6, seed=6, gain=0.5)])
r("intermitente", [sfx("click", tone=1800), sfx("click", tone=1500, at=0.4)], dur=0.8, loop=0.01)
r("radio_cambio", [sfx("static", dur=0.25, color="white", fx=[bp(2000, 0.7)]), sfx("switch", state="on", seed=9, gain=0.5)])

# ================================================================== el taller y los imprevistos
r("pinchazo", [sfx("hit", dur=0.2, tone=120, crunch=0.6), sfx("air_brake", dur=1.1, seed=7, at=0.05, gain=0.8)])
r("reserva", [seq("marimba", "D5:0.12 A4:0.35", vel=0.7), sfx("click", tone=1200, gain=0.3)])
r("motor_seco", [sfx("car_engine", rpm=280, cylinders=4, load=0.2, rough=1.0, dur=0.9, seed=21)], dur=0.69, loop=0.1)
r("repostar", [sfx("pour", dur=1.6, kind="fuel")])
r("reparar", [drum("anvil", gain=0.5), sfx("reload", action="rack", seed=12, at=0.25, gain=0.5), sfx("impact_wrench", dur=0.25, bursts=1, at=0.45, gain=0.6)])
r("pintura", [sfx("spray", dur=1.2, shake=0.4)])
r("alarma", [sfx("alarm", freq=760, freq2=1020, rate=4.0, dur=1.1, wave="square")], dur=1.0, loop=0.02)
r("ganzua", [sfx("keys", dur=0.5, shakes=2, seed=4, gain=0.5), sfx("click", tone=3500, at=0.55), sfx("click", tone=3200, at=0.72), sfx("click", tone=3600, at=0.86)],
  dur=1.0, loop=0.02)
r("cristal", [sfx("glass_break", size=0.6, seed=2)])
r("fuego", [sfx("fire", dur=2.3, crackle=0.7, seed=2)], dur=1.94, loop=0.3)

# ================================================================== transporte
r("motor_lancha", [sfx("car_engine", rpm=1900, cylinders=2, load=0.7, rough=0.35, pipe=0.004, dur=1.4, seed=23), sfx("splash", size=0.2, seed=3, at=0.2, gain=0.5), sfx("splash", size=0.2, seed=4, at=0.8, gain=0.4)],
  dur=1.0, loop=0.3)
r("motor_barco", [sfx("car_engine", rpm=360, cylinders=6, load=0.5, rough=0.3, pipe=0.014, dur=1.4, seed=29, fx=[lp(700)]), sfx("stream", dur=1.4, flow=0.3, seed=5, gain=0.4)], dur=1.0, loop=0.3)
r("sirena_barco", [sfx("foghorn", dur=1.7, freq=110)], fx=[rev(0.3, 0.8)])
r("motor_helicoptero", [sfx("helicopter", dur=1.4, rate=11.0, whine=0.3, seed=1)], dur=1.0, loop=0.3)
r("motor_avioneta", [sfx("car_engine", rpm=2900, cylinders=4, load=0.8, rough=0.1, pipe=0.002, bright=0.3, dur=1.4, seed=31), sfx("wind", dur=1.4, gain=0.3)], dur=1.0, loop=0.3)
r("avion", [sfx("noise", dur=3.4, color="brown", gain=0.8, fx=[lp(500)]), sfx("tone", freq=220, dur=3.4, wave="sine", gain=0.05)], dur=3.0, loop=0.3)
r("avion_despegue", [sfx("airplane", dur=4.0, kind="jet", seed=2)])
r("tren", [sfx("train", dur=2.4, speed=0.6, seed=4)], dur=2.0, loop=0.3)
r("tren_silbato", [nota("flute", "A5 C#6 E6", 1.4, vel=0.8, breath=0.4)], fx=[rev(0.3, 0.7)])
r("tranvia", [sfx("tram", dur=2.4, speed=0.5)], dur=2.0, loop=0.3)
r("tranvia_campana", [sfx("bike_bell", rings=2, seed=7, fx=[{"type": "speed", "factor": 0.55}])], fx=[rev(0.15, 0.4)])
r("tono_altitud", [sfx("beep", freq=660, dur=0.11, wave="triangle")])
r("tono_alineacion", [sfx("click", tone=2200), sfx("click", tone=2200, at=0.06)])
r("turbulencia", [sfx("wind", dur=1.3), drum("vibraslap", at=0.2, gain=0.5)])
r("alarma_cabina", [sfx("beep", freq=1000, dur=0.08, wave="square", at=t) for t in (0.0, 0.15, 0.3, 0.45)])
r("aterrizaje", [sfx("hit", dur=0.25, tone=70, crunch=0.4), sfx("tire_squeal", dur=0.35, pitch=1.2, at=0.05, gain=0.6), sfx("tire_roll", dur=0.9, speed=0.6, at=0.3, gain=0.6)])

# ================================================================== disparos: cada arma, su estampido
r("disparo_pistola", [sfx("gunshot", kind="pistol", seed=1)])
r("disparo_revolver", [sfx("gunshot", kind="pistol", seed=4, fx=[{"type": "speed", "factor": 0.8}]), drum("kick", gain=0.4)])
r("disparo_silenciado", [sfx("noise", dur=0.06, color="pink", gain=0.8, fx=[bp(1200, 0.8)]), sfx("dry_fire", seed=2, at=0.03, gain=0.5)])
r("disparo_rafaga", [sfx("gunshot", kind="rifle", dist=0.2, seed=6, fx=[{"type": "speed", "factor": 1.3}])], dur=0.16)
r("disparo_subfusil", [sfx("gunshot", kind="pistol", dist=0.1, seed=8, fx=[{"type": "speed", "factor": 1.25}])], dur=0.2)
r("disparo_escopeta", [sfx("gunshot", kind="shotgun", seed=10)])
r("disparo_corredera", [sfx("gunshot", kind="shotgun", seed=12), sfx("reload", action="rack", seed=13, at=0.5)])
r("disparo_rifle", [sfx("gunshot", kind="rifle", seed=14, fx=[{"type": "speed", "factor": 0.85}]), sfx("gunshot", kind="rifle", dist=0.9, seed=15, at=0.25, gain=0.35)], fx=[rev(0.25, 0.8)])
r("disparo_palanca", [sfx("gunshot", kind="rifle", seed=16, dist=0.2), sfx("reload", action="rack", seed=17, at=0.5, fx=[{"type": "speed", "factor": 1.3}])])
r("disparo_fusil", [sfx("gunshot", kind="rifle", seed=18, fx=[{"type": "speed", "factor": 1.1}])], dur=0.3)
r("disparo_semiautomatico", [sfx("gunshot", kind="pistol", seed=20, fx=[{"type": "speed", "factor": 0.7}]), drum("taiko", gain=0.5)], fx=[rev(0.15, 0.5)], dur=0.42)
r("cohete", [sfx("whoosh", dur=0.9, low=200, high=3000, direction="up"), sfx("fire", dur=0.9, crackle=0.9, seed=4, gain=0.5), sfx("hit", dur=0.15, tone=150, gain=0.5)])
r("lanzagranadas", [drum("taiko", gain=0.7), sfx("pop", freq=180, gain=0.8), sfx("whoosh", dur=0.4, low=600, high=3000, at=0.08, gain=0.4)])
r("lanzar", [sfx("whoosh", dur=0.3, low=400, high=2500), sfx("cloth", dur=0.15, weight=0.4, seed=8, gain=0.4)])

# ================================================================== combate
r("tono_objetivo", [sfx("blip", freq=1700, dur=0.06)])
r("tono_apuntado", [sfx("blip", freq=620, dur=0.035)])
r("amartillar", [sfx("click", tone=2600), sfx("dry_fire", seed=7, at=0.12, gain=0.8)])
r("bala_silbido", [sfx("bullet_whiz", dur=0.18)])
r("bala_impacto", [sfx("ricochet", dur=0.12, seed=3), sfx("steel_ball", surface="metal", force=1.0, seed=8, gain=0.6)], dur=0.14)
r("recarga", [sfx("reload", action="mag", seed=2)])
r("sin_balas", [sfx("dry_fire", seed=1)])
r("recoger_municion", [sfx("reload", action="mag", seed=9, fx=[{"type": "speed", "factor": 1.4}])], dur=0.5)
r("golpe", [sfx("punch", dur=0.1)])
r("golpe_aire", [sfx("whoosh", dur=0.15, low=500, high=2500)])
r("navaja", [sfx("sword", action="swing", seed=3, fx=[{"type": "speed", "factor": 1.4}])], dur=0.14)
r("hacha", [sfx("sword", action="swing", seed=5, fx=[{"type": "speed", "factor": 0.8}]), sfx("wood_crack", size=0.3, seed=4, at=0.18, gain=0.7)])
r("explosion", [sfx("explosion", dur=1.8, boom=1.0), drum("taiko", gain=0.6)])
r("dolor", [sfx("punch", dur=0.15), sfx("breath", kind="out", dur=0.3, at=0.03, gain=0.7), drum("kick", gain=0.4)])
r("latido", [sfx("heartbeat", rate=1.0, dur=1.2)], dur=1.0, loop=0.02)
r("curar", [sfx("magic", dur=0.6, density=8, freq="C6", gain=0.5), seq("harp", "C5:0.1 E5:0.1 G5:0.4", vel=0.6)], fx=[rev(0.2, 0.4)])
r("dolor_npc", [sfx("grunt", voice="male", kind="pain", seed=7)])
r("dolor_mujer", [sfx("grunt", voice="female", kind="pain", seed=3)])
r("muerte_npc", [sfx("grunt", voice="male", kind="death", seed=2), sfx("footfall", surface="concrete", weight=1.0, seed=99, at=0.5, gain=0.6)])
r("hospital_despertar", [sfx("heart_monitor", rate=70, dur=2.6), nota("warm_pad", "C4 E4 G4", 2.4, vel=0.5, gain=0.5)], fx=[rev(0.2, 0.6)])

# ================================================================== la policía
r("estrella_sube", [sfx("chirp", start=500, end=1300, dur=0.35, wave="square", warble=0.0)], fx=[lp(3500)])
r("estrella_baja", [seq("marimba", "A5:0.12 F5:0.12 D5:0.4", vel=0.6)])
r("buscando", [sfx("beep", freq=180, dur=0.1, wave="triangle")])
r("policia_perdida", [seq("trumpet", "C5:0.15 E5:0.15 G5:0.15 C6:0.6", vel=0.6)], fx=[rev(0.2, 0.5)])
r("sirena", [sfx("siren", low=600, high=1300, rate=0.5, dur=2.4)], dur=2.0, loop=0.2)
r("sirena_ambulancia", [sfx("alarm", freq=660, freq2=880, rate=1.25, dur=1.9, wave="triangle")], dur=1.6, loop=0.05)
r("helicoptero_policia", [sfx("helicopter", dur=2.4, rate=12.0, whine=0.5, seed=4)], dur=2.0, loop=0.3)
r("megafono", [sfx("feedback", dur=0.7, freq=1900), sfx("static", dur=0.3, color="pink", at=0.7, gain=0.4)], fx=[{"type": "telephone"}])
r("esposas", [sfx("handcuffs", clicks=7)])
r("celda", [sfx("cell_door", size=0.9)], fx=[rev(0.25, 0.6)])
r("multa", [sfx("police_whistle", blasts=1, dur=0.6)])
r("emisora", [sfx("static", dur=0.12, color="white", fx=[bp(2200, 0.8)]), sfx("beep", freq=1300, dur=0.08, at=0.2), sfx("beep", freq=1650, dur=0.1, at=0.36)])

# ================================================================== la gente
r("paso_npc", [sfx("footfall", surface="concrete", steps=1, weight=0.3, seed=80)])
r("murmullo", [sfx("crowd", mood="murmur", size=0.05, dur=0.6, lang="es", seed=3)], dur=0.4)
r("grito", [sfx("scream", voice="male", fear=0.2, dur=0.7, vowel="e", seed=5)])
r("grito_hombre", [sfx("scream", voice="male", fear=0.8, dur=0.65, vowel="a", seed=9)])
r("grito_mujer", [sfx("scream", voice="female", fear=0.8, dur=0.7, vowel="a", seed=4)])
r("panico", [sfx("stampede", people=6, dur=2.2)])
r("evento", [seq("pizzicato", "D4:0.12 A4:0.12 D5:0.4", vel=0.7), drum("rim", gain=0.3)])
r("ladrido", [sfx("bark", size=0.5, barks=2, seed=4)])
r("perro_olfatea", [sfx("sniff", count=3)])

# ================================================================== en casa
r("comer", [sfx("paper", action="crumple", dur=0.25, seed=2, gain=0.3), sfx("gulp", seed=1, at=0.3)])
r("beber", [sfx("gulp", seed=5), sfx("gulp", seed=6, at=0.15, gain=0.7)])
r("nevera", [sfx("fridge", dur=1.0, door=1.0)])
r("cocina_cortar", [sfx("knife_chop", chops=6, rate=4.5)])
r("cocina_freir", [sfx("sizzle", dur=2.4, heat=0.9, seed=4)])
r("cocina_hervir", [sfx("boil", dur=2.4, rate=0.8)])
r("plato_servido", [sfx("steel_ball", surface="plastic", force=0.4, seed=2), drum("ride_bell", at=0.15, gain=0.25, vel=0.4), sfx("keys", dur=0.3, shakes=1, seed=8, at=0.4, gain=0.4)])
r("timbre", [sfx("doorbell", high="E5", low="C5", gap=0.55)])

# ================================================================== el dinero
r("dinero", [sfx("coins", count=5, surface="hand", seed=1)])
r("caja", [sfx("cash_register", bell=1.0)])
r("cesta", [sfx("steel_ball", surface="metal", force=0.3, seed=11), sfx("keys", dur=0.25, shakes=1, seed=2, gain=0.3)])
r("bolsa", [sfx("paper", action="turn", seed=4, gain=0.6), seq("marimba", "E5:0.08 B5:0.25", at=0.15, vel=0.6)])
r("recoger", [sfx("cloth", dur=0.12, weight=0.3, seed=7), sfx("pop", freq=700, at=0.05, gain=0.5)])

# ================================================================== avisos e interfaz: madera y mecánica, pocas notas
r("menu_mover", [drum("woodblock", vel=0.4)], dur=0.035)
r("menu_ok", [drum("woodblock", vel=0.6), seq("marimba", "C5:0.05 G5:0.18", at=0.02, vel=0.5)])
r("menu_atras", [drum("woodblock", vel=0.5), seq("marimba", "G4:0.05 C4:0.18", at=0.02, vel=0.5)])
r("menu_borde", [drum("log_drum", vel=0.6)], dur=0.1)
r("menu_ajuste", [drum("clave", vel=0.4)], dur=0.035)
r("error", [sfx("error", freq=170, dur=0.2)], fx=[lp(2500)])
r("notificacion", [seq("vibraphone", "A5:0.1 E6:0.4", vel=0.55)], fx=[rev(0.15, 0.3)])
r("movil", [sfx("phone_ring", dur=0.22, pattern="single", seed=6, gain=0.6), sfx("blip", freq=1600, dur=0.04, at=0.05, gain=0.4)])
r("dialogo", [drum("snap", vel=0.4)], dur=0.06)
r("guardado", [sfx("paper", action="turn", seed=9, gain=0.5), sfx("stamp", at=0.3)])
r("logro", [seq("brass", "C5:0.12 E5:0.12 G5:0.12 C6:0.6", vel=0.7), drum("crash", at=0.36, gain=0.25, vel=0.5)], fx=[rev(0.2, 0.5)])
r("nivel", [seq("harp", "C5:0.08 E5:0.08 G5:0.08 B5:0.08 C6:0.4", vel=0.7)], fx=[rev(0.2, 0.4)])
r("reloj", [sfx("clock_tick", rate=1.0, dur=0.05)], dur=0.04)
r("pasan_horas", [sfx("clock_tick", rate=6.0, dur=1.6), sfx("whoosh", dur=1.6, low=200, high=1500, gain=0.3)])
r("gallo", [sfx("rooster")])
r("buho", [sfx("owl", kind="tawny", seed=1)], fx=[rev(0.25, 0.7)])
r("campanadas", [nota("tubular_bell", "E4", 1.0, at=t, vel=0.6) for t in (0.0, 1.0, 2.0, 3.0)], fx=[rev(0.3, 0.8)])

# ================================================================== el trabajo: lo bueno sube, lo malo baja
r("mision_ok", [seq("trumpet", "G4:0.12 C5:0.12 E5:0.12 G5:0.7", vel=0.7), nota("french_horn", "C4 G4", 0.9, at=0.36, vel=0.5, gain=0.5)], fx=[rev(0.25, 0.6)])
r("mision_fallo", [seq("cello", "E3:0.3 C3:0.3 A2:0.9", vel=0.7), drum("taiko", gain=0.4)], fx=[rev(0.25, 0.6)])
r("jornada", [sfx("siren", low=300, high=520, rate=0.4, dur=1.4, gain=0.6), sfx("clock_tick", rate=5.0, dur=1.0, at=1.4, gain=0.6)], fx=[rev(0.2, 0.6)])
r("ascenso", [seq("brass", "D5:0.12 F#5:0.12 A5:0.12 D6:0.6", vel=0.7)], fx=[rev(0.2, 0.5)])
r("despido", [sfx("door", gain=1.0), seq("felt_piano", "A4:0.25 F4:0.25 D4:0.6", at=0.25, vel=0.6)], fx=[rev(0.2, 0.4)])
r("diploma", [sfx("paper", action="turn", seed=12, gain=0.5), nota("strings", "D4 F#4 A4 D5", 1.1, at=0.2, vel=0.6)], fx=[rev(0.25, 0.6)])
r("titulo", [seq("trumpet", "C5:0.1 C5:0.1 G5:0.4", vel=0.7), nota("strings", "C4 E4 G4 C5", 1.0, at=0.5, vel=0.6)], fx=[rev(0.25, 0.6)])
r("inspeccion", [sfx("knock", count=3, surface="wood", force=0.7, seed=4), sfx("paper", action="turn", seed=13, at=0.5, gain=0.6), sfx("stamp", at=0.85)])
r("factura", [sfx("receipt_printer", dur=0.6), nota("tuba", "C2", 0.35, at=0.6, vel=0.6, gain=0.6)])
r("donativo", [sfx("coins", count=7, surface="metal", seed=6)], fx=[rev(0.15, 0.4)])
r("prestigio", [seq("celesta", "G5:0.1 B5:0.1 D6:0.5", vel=0.6)], fx=[rev(0.2, 0.4)])
r("fama", [seq("muted_guitar", "E3:0.1 G3:0.1 B3:0.35", vel=0.8), drum("snap", at=0.2, gain=0.4)])
r("animo_sube", [seq("kalimba", "C5:0.1 G5:0.3", vel=0.6)])
r("animo_baja", [seq("kalimba", "G4:0.12 C4:0.35", vel=0.6)])

# ================================================================== los barrios
r("territorio", [drum("taiko", vel=0.9), seq("french_horn", "C4:0.25 G4:0.25 C5:0.9", at=0.15, vel=0.7)], fx=[rev(0.25, 0.7)])
r("amenaza_barrio", [drum("taiko", at=t, vel=0.7, gain=g) for t, g in ((0.0, 0.6), (0.35, 0.7), (0.6, 0.8), (0.78, 0.9), (0.9, 1.0))]
  + [seq("strings", "C#4:0.3 D4:0.4", at=0.5, vel=0.6, gain=0.6)], fx=[rev(0.2, 0.6)])
r("barrio_defendido", [drum("snare", at=t, vel=0.5, gain=0.5) for t in (0.0, 0.06, 0.12, 0.18, 0.24, 0.3)]
  + [seq("brass", "G4:0.12 B4:0.12 D5:0.6", at=0.36, vel=0.7)], fx=[rev(0.2, 0.5)])
r("barrio_perdido", [drum("gong", vel=0.6, gain=0.7), seq("cello", "D4:0.3 B3:0.3 G3:0.8", at=0.2, vel=0.6)], fx=[rev(0.3, 0.7)])

# ================================================================== jugar en línea: parejas que se reflejan
r("amigo_entra", [seq("glass", "C5:0.12 E5:0.12 G5:0.4", vel=0.6)], fx=[rev(0.15, 0.4)])
r("amigo_sale", [seq("glass", "G5:0.12 E5:0.12 C5:0.4", vel=0.6)], fx=[rev(0.15, 0.4)])
r("chat", [seq("xylophone", "D6:0.06 F6:0.18", vel=0.5)])
r("chat_personaje", [seq("felt_piano", "D4:0.2 A4:0.4", vel=0.6)], fx=[rev(0.15, 0.4)])
r("chat_fuera", [drum("woodblock", vel=0.6), drum("woodblock", at=0.12, vel=0.5)])
r("chat_accion", [sfx("cloth", dur=0.2, weight=0.4, seed=11), nota("kalimba", "A4", 0.25, at=0.18, vel=0.6)])
r("espera_servidor", [nota("warm_pad", "E4", 0.7, vel=0.4), nota("warm_pad", "B3", 0.8, at=0.8, vel=0.35)], fx=[rev(0.2, 0.5)])

# ================================================================== minijuegos
r("pesca_lanzar", [sfx("whoosh", dur=0.6, low=300, high=2500), sfx("bike_chain", dur=0.4, speed=1.0, at=0.05, gain=0.4), sfx("splash", size=0.15, seed=9, at=0.75)])
r("pez_pica", [sfx("splash", size=0.2, seed=12), sfx("bubble", freq=500, at=0.1), sfx("bubble", freq=650, at=0.25)])
r("carrete", [sfx("spinner", spins=14, rate=22, tone=1.4, seed=3)])
r("diana", [sfx("spring", action="release", tension=0.5, seed=4)], dur=0.3)
r("diana_ok", [sfx("steel_ball", surface="wood", force=1.0, seed=5), sfx("coin", freq="E6", gain=0.4)])
r("ruleta", [sfx("ball_roll", speed=0.8, dur=1.8, seed=2), sfx("spinner", spins=12, rate=14, tone=0.8, seed=6, at=1.6)])
r("dados", [sfx("dice", count=2, seed=4)])
r("campana_ring", [nota("bell", "C5", 0.3, at=t, vel=0.7, decay=0.6) for t in (0.0, 0.18, 0.36)], fx=[rev(0.15, 0.5)])
r("simon_0", [nota("steel_drum", "A5", 0.4, vel=0.7)])
r("simon_1", [nota("steel_drum", "F5", 0.4, vel=0.7)])
r("simon_2", [nota("steel_drum", "C5", 0.4, vel=0.7)])
r("simon_3", [nota("steel_drum", "D5", 0.4, vel=0.7)])

# ================================================================== ambientes: camas largas, en bucle y en estéreo
r("amb_ciudad", [sfx("tire_roll", dur=8.0, speed=0.4, gain=0.5, fx=LEJOS), sfx("crowd", mood="murmur", size=0.4, dur=8.0, lang="es", seed=5, gain=0.25, fx=[lp(2500)]),
                 sfx("car_horn", dur=0.25, honks=1, freq=380, at=3.1, gain=0.15, fx=LEJOS)], dur=7.7, loop=0.3, mono=False)
r("amb_residencial", [sfx("birds", dur=8.0, species="chirp", seed=2, gain=0.4), sfx("wind_howl", dur=8.0, gust=0.15, seed=1, gain=0.2),
                      sfx("bark", size=0.3, barks=2, seed=8, at=4.0, gain=0.15, fx=LEJOS)], dur=7.7, loop=0.3, mono=False)
r("amb_industrial", [sfx("forcefield", dur=6.0, seed=2, gain=0.3), sfx("impact_wrench", dur=0.5, bursts=1, at=1.5, gain=0.25, fx=LEJOS),
                     drum("anvil", at=3.5, gain=0.2, fx=LEJOS), sfx("noise", dur=6.0, color="brown", gain=0.4)], dur=5.7, loop=0.3, mono=False)
r("amb_parque", [sfx("birds", dur=10.0, species="song", seed=3, gain=0.6), sfx("birds", dur=10.0, species="chirp", seed=4, gain=0.3),
                 sfx("wind_howl", dur=10.0, gust=0.1, seed=2, gain=0.15)], dur=9.7, loop=0.3, mono=False)
r("amb_playa", [sfx("waves", dur=9.0, size=0.6, period=6.0, seed=1)], dur=8.7, loop=0.3, mono=False)
r("amb_puerto", [sfx("waves", dur=9.0, size=0.15, period=4.0, seed=4, gain=0.6), sfx("creak", dur=1.4, pitch=0.6, at=6.0, gain=0.3), sfx("foghorn", dur=2.0, freq=95, at=4.0, gain=0.3, fx=LEJOS),
                 sfx("seagull", calls=2, seed=3, at=1.5, gain=0.25, fx=LEJOS)], dur=8.7, loop=0.3, mono=False)
r("amb_mar", [sfx("waves", dur=10.0, size=0.9, period=8.0, seed=7, gain=0.8), sfx("wind_howl", dur=10.0, gust=0.5, seed=5, gain=0.4)], dur=9.7, loop=0.3, mono=False)
r("amb_campo", [sfx("birds", dur=10.0, species="trill", seed=6, gain=0.4), drum("agogo", at=2.0, gain=0.15, fx=LEJOS), drum("agogo", at=2.5, gain=0.12, fx=LEJOS),
                sfx("wind_howl", dur=10.0, gust=0.2, seed=8, gain=0.25)], dur=9.7, loop=0.3, mono=False)
r("amb_montana", [sfx("wind_howl", dur=10.0, gust=0.7, seed=9)], dur=9.7, loop=0.3, mono=False)
r("amb_noche", [sfx("crickets", dur=6.1, count=5, seed=2)], dur=5.8, loop=0.3, mono=False)
r("lluvia", [sfx("rain", dur=5.0, intensity=0.6, seed=3)], dur=4.7, loop=0.3, mono=False)
r("trueno", [sfx("thunder", dur=3.5)], mono=False)
r("viento_playa", [sfx("wind_howl", dur=8.7, gust=0.8, seed=11)], mono=False)
r("multitud", [sfx("crowd", mood="murmur", size=0.6, dur=6.0, lang="es", seed=7)], dur=5.7, loop=0.3)
r("gaviota", [sfx("seagull", calls=3, seed=1)], fx=[rev(0.2, 0.6)])
r("pajaro", [sfx("birds", dur=0.9, species="chirp", seed=9)])
r("martillo", [drum("anvil", at=t, gain=0.6) for t in (0.0, 0.4, 0.8)], fx=LEJOS)
r("claxon_lejano", [sfx("car_horn", dur=0.35, honks=1, freq=390, seed=3)], fx=LEJOS)
r("sirena_lejana", [sfx("siren", low=550, high=900, rate=0.6, dur=2.0)], fx=LEJOS)

# ================================================================== la vida social
r("afinidad_sube", [seq("harp", "E5:0.1 G#5:0.1 B5:0.1 E6:0.6", vel=0.6)], fx=[rev(0.2, 0.5)])
r("afinidad_baja", [seq("harp", "E5:0.15 C5:0.15 A4:0.9", vel=0.6)], fx=[rev(0.2, 0.5)])
r("cita", [seq("celesta", "C5:0.12 E5:0.12 A5:0.12 C6:0.8", vel=0.6), nota("warm_pad", "A3 C4 E4", 1.1, vel=0.4, gain=0.4)], fx=[rev(0.25, 0.6)])
r("regalo", [sfx("paper", action="tear", seed=5)])
r("pareja", [sfx("heartbeat", rate=1.6, dur=0.8), seq("harp", "C5:0.1 E5:0.1 G5:0.1 C6:0.6", at=0.7, vel=0.6)], fx=[rev(0.2, 0.5)])
r("noche_juntos", [nota("warm_pad", "F3 A3 C4 E4", 2.9, vel=0.5)], fx=[rev(0.3, 0.8), {"type": "fade", "out": 1.2}])
r("ruptura", [sfx("glass_break", size=0.2, seed=6, gain=0.5), seq("cello", "D4:0.4 C4:0.4 A3:1.5", at=0.3, vel=0.6)], fx=[rev(0.3, 0.7)])

# ================================================================== las sustancias
r("tomar_copa", [sfx("pour", dur=0.6, kind="water", seed=3), nota("glass", "A6", 0.4, at=0.75, vel=0.5, gain=0.5), nota("glass", "C7", 0.4, at=0.8, vel=0.4, gain=0.4)])
r("tomar_hierba", [sfx("lighter"), sfx("breath", kind="in", dur=0.5, at=0.6), sfx("breath", kind="out", dur=0.6, at=1.05)])
r("tomar_pastillas", [sfx("blister", pills=1), sfx("gulp", seed=9, at=0.6)])
r("tomar_polvo", [sfx("card", action="flip", seed=4, gain=0.5), sfx("breath", kind="in", dur=0.4, at=0.45)])
r("tomar_cristal", [sfx("fire", dur=1.5, crackle=1.0, seed=6, fx=[hp(1200)])])
r("bajon", [sfx("powerdown", freq="C5", steps=5, rate=0.12), nota("warm_pad", "C3 Eb3 G3", 1.4, vel=0.4, gain=0.5)], fx=[lp(2500), rev(0.25, 0.6)])
r("abstinencia", [nota("synth", "A2", 1.1, vel=0.6, wave="saw", cutoff=500), sfx("heartbeat", rate=2.0, dur=1.1, gain=0.6)], fx=[{"type": "tremolo", "rate": 9.0, "depth": 0.6}])
r("sobredosis", [sfx("heartbeat", rate=0.7, dur=1.6), sfx("heart_monitor", rate=40, dur=3.2, flatline=1.0, gain=0.8)])
r("trato", [sfx("paper", action="turn", seed=14, gain=0.6), sfx("cloth", dur=0.4, weight=0.6, seed=12, at=0.35)])
r("rechazo", [sfx("error", freq=230, dur=0.16)], fx=[lp(2000)])
r("paisano", [nota("brass", "C3 F#3", 0.9, vel=0.6), drum("taiko", gain=0.5)], fx=[rev(0.2, 0.5)])
r("precio_ganga", [seq("marimba", "C5:0.08 E5:0.08 G5:0.25", vel=0.6)])
r("precio_escasez", [seq("marimba", "G4:0.08 Eb4:0.08 C4:0.25", vel=0.6)])


# ------------------------------------------------------------------ las dos órdenes
def recetas(carpeta):
    from juego import sintesis
    nombres = set(sintesis.generar())
    falta = sorted(nombres - set(RECETAS))
    sobra = sorted(set(RECETAS) - nombres)
    if falta or sobra:
        raise SystemExit(f"Recetas que faltan: {falta}. Que sobran: {sobra}")
    os.makedirs(carpeta, exist_ok=True)
    lote = {"out_dir": os.path.join(carpeta, "wav"), "sounds": [RECETAS[n] for n in sorted(RECETAS)]}
    ruta = os.path.join(carpeta, "genny_lote.json")
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lote, f, ensure_ascii=False, indent=1)
    print(f"{len(RECETAS)} recetas en {ruta}")


def montar(carpeta, destino):
    """Los WAV de genny pasan a FLAC con el nombre de cada sonido del juego, más pack.json y CREDITOS.txt."""
    from juego import sintesis
    wav = os.path.join(carpeta, "wav")
    os.makedirs(destino, exist_ok=True)
    hechos = []
    for n in sorted(RECETAS):
        d = sintesis.leer_audio(os.path.join(wav, n + ".wav"), mono=False)
        sintesis.escribir_audio(os.path.join(destino, n), d)
        hechos.append(n)
    with open(os.path.join(destino, "pack.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"nombre": "Genny", "descripcion": "Todos los sonidos del juego hechos con genny, un generador de sonidos por síntesis: nada grabado, todo original.",
                   "licencia": "Sonidos generados para Puerto Bravo con genny", "grabaciones": 0, "originales_del_juego": 0, "sintetizados_con_genny": len(hechos),
                   "autor": "Generado para Puerto Bravo con genny (github.com/ogomez92/genny)", "igualar": True}, f, ensure_ascii=False, indent=2)
    lineas = ["PACK DE SONIDOS «GENNY» PARA PUERTO BRAVO", "",
              f"Los {len(hechos)} sonidos del juego, todos generados con genny, un generador de sonidos por síntesis.",
              "No hay grabaciones ni sonidos del juego: cada uno sale de una receta de genny (herramientas\\pack_genny.py).", "",
              "INSTALAR PARA PROBARLO", "  Copia esta carpeta entera dentro de data\\sonidos del juego y elígela en",
              "  Opciones, Sonido y música, Pack de sonidos.", "", "DE DÓNDE SALE", "  https://github.com/ogomez92/genny"]
    with open(os.path.join(destino, "CREDITOS.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"{len(hechos)} sonidos en {destino}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "recetas":
        recetas(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "montar":
        montar(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
