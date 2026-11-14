"""Prueba real del motor de sonido envolvente: abre el dispositivo, hace sonar varias cosas alrededor y mide.

    .venv\\Scripts\\python.exe herramientas\\probar_motor_envolvente.py

Suena unos segundos, flojo, por la salida de sonido del equipo. No cambia nada del juego.
"""
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from juego import audio_al  # noqa: E402
from juego.audio import SR  # noqa: E402


def main():
    m = audio_al.MezcladorAL()
    print("binaural:", m.binaural, "| frecuencia:", m.frecuencia)
    t = np.arange(SR) / SR
    m.registrar("tono", (0.25 * np.sin(2 * np.pi * 440 * t) * np.exp(-3 * t)).astype(np.float32))
    m.registrar("motor", (0.15 * np.sign(np.sin(2 * np.pi * 90 * t))).astype(np.float32))
    m.registrar("fondo", np.stack([0.05 * np.sin(2 * np.pi * 200 * t), 0.05 * np.sin(2 * np.pi * 300 * t)], axis=1).astype(np.float32))
    m.vols["maestro"] = 0.25
    m.situar_oyente(0.0, 0.0, 0.0)
    fondo = m.sonar("fondo", bucle=True, cat="ambiente")
    motor = m.sonar("motor", bucle=True, xy=(20.0, 0.0), ref=6, maxd=80)
    errores = 0
    t0 = time.perf_counter()
    cuadros = 0
    cortos = []
    while time.perf_counter() - t0 < 4.0:
        a = (time.perf_counter() - t0) * math.pi / 2                 # el motor da una vuelta alrededor del oyente
        motor.mover(20 * math.sin(a), 20 * math.cos(a))
        motor.tono(0.8 + 0.2 * math.sin(a))
        if cuadros % 20 == 0:
            cortos.append(m.sonar("tono", xy=(-8.0, 3.0)))
        if cuadros == 60:
            m.hablando("Una frase para que baje el ambiente.")
        if cuadros == 90:
            m.mundo_pausado = True
        if cuadros == 110:
            m.mundo_pausado = False
        ta = time.perf_counter()
        m.actualizar()
        errores += 1 if m.al.alGetError() else 0
        coste = (time.perf_counter() - ta) * 1000
        cuadros += 1
        time.sleep(1 / 60)
    print(f"cuadros: {cuadros} | errores de OpenAL: {errores} | última actualización: {coste:.2f} ms | canales vivos: {len(m.canales)} | sonidos cortos lanzados: {len(cortos)}, terminados: {sum(c.fin for c in cortos)}")
    print("ambiente atenuado al hablar:", round(m.duck, 2))
    fondo.parar()
    motor.parar()
    for _ in range(30):
        m.actualizar()
        time.sleep(1 / 60)
    print("tras parar, canales vivos:", len(m.canales))
    # muchos sonidos a la vez: el coste de Python por fotograma
    fuentes = [m.sonar("motor", bucle=True, xy=(10.0 + k, 5.0), ref=6, maxd=200, vol=0.05) for k in range(48)]
    for _ in range(10):
        m.actualizar()
    ta = time.perf_counter()
    for _ in range(100):
        m.actualizar()
    print(f"con 48 sonidos a la vez: {(time.perf_counter() - ta) * 10:.2f} ms por fotograma | errores: {m.al.alGetError()} | con fuente: {sum(1 for c in fuentes if c._src)}")
    m.cerrar()
    print("RESULTADO: todo bien" if not errores else "RESULTADO: ha habido errores")


if __name__ == "__main__":
    main()
