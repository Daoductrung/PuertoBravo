"""Pone en la compilación la numpy para procesadores antiguos, en lib_antiguo, junto a la oficial que va en lib.

    .venv\\Scripts\\python.exe herramientas\\poner_numpy_antiguo.py dist\\PuertoBravo

La saca de la rueda de terceros\\numpy_antiguo (se crea con herramientas\\compilar_numpy_antiguo.bat), quita lo
que el juego no usa (pruebas, f2py), la deja compilada a .pyc sin rutas de este equipo y comprueba que es de
la misma versión que la oficial y que de verdad no exige instrucciones modernas.
"""
import compileall
import glob
import os
import shutil
import subprocess
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOBRA = ("tests", "f2py", "testing", "_pyinstaller", "doc")


def poner(destino):
    ruedas = sorted(glob.glob(os.path.join(RAIZ, "terceros", "numpy_antiguo", "numpy-*-win_amd64.whl")))
    if not ruedas:
        print("  FALTA la numpy para procesadores antiguos. Créala con herramientas\\compilar_numpy_antiguo.bat")
        return False
    rueda = ruedas[-1]
    lib = os.path.join(destino, "lib_antiguo")
    shutil.rmtree(lib, ignore_errors=True)
    os.makedirs(lib)
    with zipfile.ZipFile(rueda) as z:
        z.extractall(lib, [n for n in z.namelist() if n.startswith("numpy/")])
    for base, dirs, _ in os.walk(os.path.join(lib, "numpy")):
        for d in list(dirs):
            if d in SOBRA or d == "__pycache__":
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)
                dirs.remove(d)
    # numpy anota en su ficha de compilación la ruta del Python con el que se compiló: fuera.
    ficha = os.path.join(lib, "numpy", "__config__.py")
    with open(ficha, encoding="utf-8") as f:
        texto = f.read()
    import re
    texto = re.sub(r'r?"[A-Za-z]:[\\/][^"\n]*python(?:w)?\.exe"', '"python.exe"', texto, flags=re.I)
    with open(ficha, "w", encoding="utf-8") as f:
        f.write(texto)
    # Compilada y sin los .py, como el resto del juego; -d fija la ruta que se guarda dentro, para que no sea la de este equipo.
    if not compileall.compile_dir(os.path.join(lib, "numpy"), ddir="numpy", legacy=True, quiet=2, optimize=1):
        print("  No se pudo compilar la numpy antigua.")
        return False
    for base, _, archivos in os.walk(os.path.join(lib, "numpy")):
        for a in archivos:
            if a.endswith(".py") or a.endswith(".pyi") or a.endswith(".pxd"):
                os.remove(os.path.join(base, a))
    prueba = ("import sys; sys.path.insert(0, sys.argv[1]); import numpy as n; c = n.show_config(mode='dicts'); "
              "print(n.__version__, '|', ','.join(c['SIMD Extensions'].get('baseline', [])) or 'sin exigencias', '|', float(n.arange(10, dtype='f4').sum()))")
    r = subprocess.run([sys.executable, "-I", "-c", prueba, lib], capture_output=True, text=True)
    import numpy
    if r.returncode != 0 or not r.stdout.startswith(numpy.__version__ + " | sin exigencias | 45.0"):
        print("  La numpy antigua no pasa la comprobación:", (r.stdout + r.stderr).strip()[-300:])
        return False
    megas = sum(os.path.getsize(os.path.join(b, a)) for b, _, fs in os.walk(lib) for a in fs) / 2 ** 20
    print(f"  numpy {numpy.__version__} para procesadores antiguos en lib_antiguo: {megas:.0f} megas, sin exigencias de procesador")
    return True


if __name__ == "__main__":
    sys.exit(0 if poner(sys.argv[1]) else 1)
