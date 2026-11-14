"""Elección de la biblioteca de cálculo según el procesador, aviso si no hay ninguna que sirva y rutas fuera del registro."""
import os
import sys

from juego import procesador as P, registro

TODO = {"SSE3": True, "CX16": True, "SSSE3": True, "SSE4.1": True, "SSE4.2": True, "AVX": True, "AVX2": True}
VIEJO = dict(TODO, **{"SSSE3": False, "SSE4.1": False, "SSE4.2": False, "AVX": False, "AVX2": False})


def _compilado(monkeypatch, tmp_path, ins):
    """Finge un juego compilado con las dos bibliotecas y un procesador con las instrucciones dadas."""
    os.makedirs(tmp_path / "lib_antiguo" / "numpy")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "PuertoBravo.exe"))
    monkeypatch.setattr(P, "instrucciones", lambda: dict(ins))
    monkeypatch.delenv("PUERTOBRAVO_NUMPY", raising=False)
    monkeypatch.setattr(sys, "path", list(sys.path))
    # en las pruebas no se descarga la numpy de verdad, que es la del entorno: solo los módulos de pega
    monkeypatch.setattr(P, "_olvidar_numpy", lambda: [sys.modules.pop(m) for m in list(sys.modules) if m.startswith("numpy.medio")])
    return str(tmp_path / "lib_antiguo")


def test_procesador_actual_y_procesador_antiguo(monkeypatch, tmp_path):
    assert P.moderno(TODO) and not P.moderno(VIEJO) and not P.moderno({})        # si Windows no sabe contestar, se va a lo seguro
    antigua = _compilado(monkeypatch, tmp_path, TODO)
    cargas = []
    assert P.preparar(lambda: cargas.append(antigua in sys.path))
    assert cargas == [False] and P.estado["numpy"] == "oficial" and antigua not in sys.path
    monkeypatch.setattr(P, "instrucciones", lambda: dict(VIEJO))
    cargas.clear()
    assert P.preparar(lambda: cargas.append(sys.path[0] == antigua))
    assert cargas == [True] and P.estado["numpy"] == "antigua" and "faltan instrucciones" in P.estado["motivo"]
    assert "SSE4.2 no" in P.resumen()["instrucciones del procesador"] and "antigua" in P.resumen()["biblioteca de cálculo"]


def test_si_la_elegida_no_carga_se_prueba_la_otra(monkeypatch, tmp_path):
    antigua = _compilado(monkeypatch, tmp_path, TODO)          # Windows dice que el procesador vale, pero la oficial falla al cargar

    def cargar():
        if antigua not in sys.path:
            sys.modules["numpy.medio_cargado"] = object()
            raise ImportError("DLL load failed while importing _multiarray_umath")
    assert P.preparar(cargar)
    assert P.estado["numpy"] == "antigua" and "oficial: ImportError" in P.estado["motivo"] and "numpy.medio_cargado" not in sys.modules
    # se puede forzar una para probar
    monkeypatch.setenv("PUERTOBRAVO_NUMPY", "antigua")
    vistas = []
    assert P.preparar(lambda: vistas.append(sys.path[0] == antigua)) and vistas == [True] and "forzada" in P.estado["motivo"]


def test_si_no_carga_ninguna_lo_dice_y_no_se_cae(monkeypatch, tmp_path):
    antigua = _compilado(monkeypatch, tmp_path, VIEJO)

    def cargar():
        raise ImportError("DLL load failed")
    assert not P.preparar(cargar) and P.estado["numpy"] == "ninguna" and antigua not in sys.path
    dicho, cuadros = [], []

    class VozDePega:
        def decir(self, texto, interrumpir=False):
            dicho.append(texto)
    import ctypes
    import juego.voz
    monkeypatch.setattr(juego.voz, "Voz", VozDePega)
    monkeypatch.setattr(ctypes.windll.user32, "MessageBoxW", lambda *a: cuadros.append(a[1]), raising=False)
    registro.iniciar("juego", str(tmp_path / "logs"), "0.0", graves=False)
    try:
        P.avisar_incompatible(registro)
        carpeta = registro.carpeta_sesion()
    finally:
        registro.cerrar()
    assert dicho == [P.AVISO] and cuadros == [P.AVISO] and "procesador es demasiado antiguo" in P.AVISO
    errores = open(os.path.join(carpeta, "errores.log"), encoding="utf-8").read()
    assert "El procesador no es compatible" in errores and "SSE4.2" in errores


def test_en_el_codigo_fuente_no_se_elige_nada(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert P.preparar() and P.estado["numpy"] == "oficial" and P.estado["motivo"] == "no hay otra"
    import numpy
    assert numpy.arange(4).sum() == 6


def test_el_registro_no_guarda_rutas_de_ningun_equipo(tmp_path):
    casos = {r'File "D:\Antigravity\JuegoGTA\.venv\Lib\site-packages\numpy\_core\__init__.py", line 24': 'File "__init__.py", line 24',
             r'File "E:\Mis cosas\Juegos de Ana\x.py", line 3': 'File "x.py", line 3',
             r"from 'C:/Trabajo/Proyectos/juego/app.py'": "from 'app.py'",
             "son las 12:30 y C: no es una ruta": "son las 12:30 y C: no es una ruta",
             r"numpy\_core\multiarray.py": r"numpy\_core\multiarray.py"}
    for sucio, limpio in casos.items():
        assert registro.limpiar(sucio) == limpio
    # el archivo del fallo grave, que Python escribe sin pasar por el filtro, se limpia al cerrar y al abrir la sesión siguiente
    raiz = str(tmp_path / "logs")
    registro.iniciar("juego", raiz, "0.0", graves=True)
    carpeta = registro.carpeta_sesion()
    registro.cerrar()
    vieja = os.path.join(raiz, "2026-01-01_00-00-00_juego")
    os.makedirs(vieja)
    for c in (carpeta, vieja):
        with open(os.path.join(c, "fallo_grave.log"), "w", encoding="utf-8") as f:
            f.write('Windows fatal exception: code 0xc000001d\n  File "D:\\OtroEquipo\\Proyecto\\main.py", line 14 in main\n')
    registro.iniciar("juego", raiz, "0.0", graves=False)
    registro.cerrar()
    for c in (carpeta, vieja):
        texto = open(os.path.join(c, "fallo_grave.log"), encoding="utf-8").read()
        assert "OtroEquipo" not in texto and 'File "main.py", line 14 in main' in texto and "0xc000001d" in texto
