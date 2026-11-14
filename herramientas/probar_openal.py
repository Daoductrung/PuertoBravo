"""Comprueba que la biblioteca de sonido OpenAL Soft carga en este equipo y que activa el sonido binaural.

    .venv\\Scripts\\python.exe herramientas\\probar_openal.py

Escribe el resultado en pantalla y en adjuntos\\prueba_openal.txt. No cambia nada del juego.
"""
import ctypes
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLL = os.path.join(RAIZ, "terceros", "openal_soft", "soft_oal.dll")
lineas = []


def di(*a):
    t = " ".join(str(x) for x in a)
    lineas.append(t)
    print(t, flush=True)


def probar():
    di("Python", sys.version.split()[0], "| biblioteca:", os.path.getsize(DLL), "bytes")
    al = ctypes.CDLL(DLL)
    vp = ctypes.c_void_p
    al.alcOpenDevice.restype = vp
    al.alcOpenDevice.argtypes = [ctypes.c_char_p]
    al.alcGetString.restype = ctypes.c_char_p
    al.alcGetString.argtypes = [vp, ctypes.c_int]
    al.alcIsExtensionPresent.argtypes = [vp, ctypes.c_char_p]
    al.alcCreateContext.restype = vp
    al.alcCreateContext.argtypes = [vp, ctypes.POINTER(ctypes.c_int)]
    al.alcMakeContextCurrent.argtypes = [vp]
    al.alcGetIntegerv.argtypes = [vp, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    al.alcDestroyContext.argtypes = [vp]
    al.alcCloseDevice.argtypes = [vp]
    al.alGetString.restype = ctypes.c_char_p
    d = al.alcOpenDevice(None)
    di("dispositivo abierto:", bool(d))
    if not d:
        return
    for e in (b"ALC_SOFT_HRTF", b"ALC_EXT_EFX", b"ALC_SOFT_loopback", b"ALC_SOFT_output_mode", b"ALC_ENUMERATE_ALL_EXT"):
        di("  extensión", e.decode(), "sí" if al.alcIsExtensionPresent(d, e) else "no")
    atributos = (ctypes.c_int * 3)(0x1992, 1, 0)            # ALC_HRTF_SOFT = sí
    c = al.alcCreateContext(d, atributos)
    al.alcMakeContextCurrent(c)
    v = ctypes.c_int(0)
    al.alcGetIntegerv(d, 0x1993, 1, ctypes.byref(v))
    di("binaural (1 es activado):", v.value)
    al.alcGetIntegerv(d, 0x1994, 1, ctypes.byref(v))
    al.alcGetStringiSOFT.restype = ctypes.c_char_p
    al.alcGetStringiSOFT.argtypes = [vp, ctypes.c_int, ctypes.c_int]
    di("perfiles de oído disponibles:", [al.alcGetStringiSOFT(d, 0x1995, i).decode("utf-8", "replace") for i in range(v.value)])
    di("versión:", al.alGetString(0xB002).decode(), "|", al.alGetString(0xB003).decode())
    al.alcGetIntegerv(d, 0x1007, 1, ctypes.byref(v))
    di("frecuencia de salida:", v.value)
    al.alcMakeContextCurrent(None)
    al.alcDestroyContext(c)
    al.alcCloseDevice(d)
    di("RESULTADO: todo bien")


if __name__ == "__main__":
    try:
        probar()
    except Exception as e:
        di("RESULTADO: fallo:", type(e).__name__, e)
    os.makedirs(os.path.join(RAIZ, "adjuntos"), exist_ok=True)
    with open(os.path.join(RAIZ, "adjuntos", "prueba_openal.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
