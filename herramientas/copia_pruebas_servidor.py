"""Prepara en adjuntos una copia del juego para PROBAR el servidor en línea con varias instancias a la vez.

    .venv\\Scripts\\python.exe herramientas\\copia_pruebas_servidor.py puertobravo://192.168.1.150:47820 "Servidor de pruebas"

Parte de la compilación de dist\\PuertoBravo (hay que compilar antes) y le añade lo que NO lleva la que se reparte:
- data\\config\\varias_instancias.txt: deja abrir el juego varias veces, cada una con su perfil;
- data\\config\\servidor_pruebas.txt: el servidor ya apuntado en la lista;
- un .bat por jugador, cada uno con su perfil: identidad, nombre y opciones propias.

Esta copia no se reparte: la que se publica solo deja abrir el juego una vez, y así cada persona lleva un personaje.
"""
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    direccion = sys.argv[1] if len(sys.argv) > 1 else "puertobravo://127.0.0.1:47820"
    nombre = sys.argv[2] if len(sys.argv) > 2 else "Servidor de pruebas"
    origen = os.path.join(RAIZ, "dist", "PuertoBravo")
    destino = os.path.join(RAIZ, "adjuntos", "prueba_servidor")
    if not os.path.exists(os.path.join(origen, "PuertoBravo.exe")):
        print("No hay compilación en dist\\PuertoBravo. Ejecuta antes compilar.bat")
        return 1
    juego = os.path.join(destino, "PuertoBravo")
    if os.path.isdir(juego):
        shutil.rmtree(juego)
    os.makedirs(destino, exist_ok=True)
    shutil.copytree(origen, juego)
    cfg = os.path.join(juego, "data", "config")
    os.makedirs(cfg, exist_ok=True)
    with open(os.path.join(cfg, "varias_instancias.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("Con este archivo, el juego se puede abrir varias veces, cada una con su perfil.\nSolo para pruebas: la copia que se reparte no lo lleva.\n")
    with open(os.path.join(cfg, "servidor_pruebas.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(f"{nombre} | {direccion}\n")
    for n in range(1, 5):
        with open(os.path.join(destino, f"Jugador {n}.bat"), "w", encoding="ascii", newline="\r\n") as f:
            f.write(f'@echo off\nrem Abre el juego como el jugador {n}, con su propia identidad, su nombre y sus opciones.\ncd /d "%~dp0PuertoBravo"\nstart "" PuertoBravo.exe --perfil={n}\n')
    with open(os.path.join(destino, "LEEME.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write(f"""COPIA DE PRUEBAS DEL SERVIDOR EN LINEA

Esta carpeta es para probar el servidor con varios jugadores desde un solo ordenador.
No se reparte: la que se publica solo deja abrir el juego una vez.

Como se usa
- Abre «Jugador 1.bat». Se abre el juego como el jugador 1.
- Abre «Jugador 2.bat». Se abre otro juego, como el jugador 2. Hay hasta el 4.
- En cada uno: menu principal, Jugar en un servidor. El servidor ya esta en la lista:
  {nombre}, {direccion}
- Pulsa Intro sobre el. La primera vez eliges personaje.

Cada jugador tiene su identidad, su nombre (Jugador 1, Jugador 2...) y sus opciones, aparte de los demas.
El nombre se cambia en Jugar en un servidor, Tu nombre de jugador, antes de entrar por primera vez.

Para oir a cada jugador por separado conviene poner a uno la voz del lector y a otro la voz de Windows,
en Opciones, Voz, o bajar el volumen de uno. Con Alt Tabulador se pasa de una ventana a otra.

El primero que entra en un servidor recien creado es su administrador.
""")
    print("Copia de pruebas lista en", destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
