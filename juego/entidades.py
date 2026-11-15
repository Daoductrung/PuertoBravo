"""Entidades del mundo: jugador, vehículos, personas y objetos."""
import math


class Jugador:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.rumbo = 0.0
        self.salud = 100.0
        self.salud_max = 100.0
        self.mapa = "puerto_bravo"
        self.banco = 0
        self.barcos = []            # [{"modelo", "salud", "nombre", "en": id del embarcadero}]
        self.barco_actual = None    # barco con el que has zarpado (None si es alquilado o robado)
        self.pescado = []           # [{"nombre", "valor"}]
        self.loteria = 0            # día del boleto comprado
        self.ropa = "ropa de calle"
        self.guardaespaldas = 0
        self.hab = {"conduccion": 0.0, "punteria": 0.0, "resistencia": 0.0, "pesca": 0.0}
        self.logros = []
        self.marcadores = []
        self.perro = ""
        self.animo = 55.0
        self.personaje = "dani"
        self.nombre = "Dani"
        self.apellido = "Roca"
        self.ciudadania = 20.0
        self.jornada_dia = 0
        self.curso_dia = 0
        self.voluntario_dia = 0
        self.reputacion = 0.0
        self.relaciones = {}
        self.conocidos = []          # gente de la calle que te ha dado su número
        self.intimos = {}            # artículos íntimos (contenido para adultos): preservativos, velas...
        self.its = 0                 # día en que te contagiaste, o 0
        self.semilla = 0             # la suerte propia de esta partida: precios y cómo viene cada día
        self.hambre = 0.0            # vida realista: de 0 a 100
        self.sueno = 0.0
        self.pareja = ""
        self.sustancias = {}
        self.efectos = []
        self.adiccion = {}
        self.ultima_dosis = {}
        self.territorios = []
        self.banda = 0               # cuánta gente tienes en tu banda
        self.banda_nombre = ""
        self.ciclo = 0               # cuántas veces has vuelto a empezar conservando lo ganado
        self.amenaza = None          # una banda rival ataca un territorio tuyo: {"territorio", "banda", "dia"}
        self.oferta_pacto = None     # una banda te ofrece un pacto: {"banda", "precio", "dia"}
        self.pacto_hasta = 0         # día hasta el que dura el pacto
        self.redada = None           # la policía te aprieta: {"precio", "dia"}
        self.rep_bandas = {}         # cómo te llevas con cada banda: de -100 a 100
        self.foco = 100.0            # medidor del tiempo lento
        self.dia_nevera = -1         # último día que comiste de la nevera de casa
        self.acciones = {}
        self.bolsa = {}
        self.gimnasio_dia = 0
        self.blindaje = 0.0
        self.dinero = 50
        self.armas = {"punos": {"cargador": 0, "reserva": 0}}
        self.arma = "punos"
        self.objetos = {"botiquin": 1, "ganzua": 0}
        self.puntos_busqueda = 0.0
        self.estrellas = 0
        self.veh = None
        self.agachado = False
        self.t_ataque = 0.0
        self.propiedades = ["casa_abuela"]
        self.garajes = {}
        self.casetes = []
        self.visitados = []
        self.barrios_vistos = []
        self.stats = {"muertes": 0, "detenciones": 0, "enemigos": 0, "vehiculos_robados": 0,
                      "metros_pie": 0.0, "metros_coche": 0.0, "dinero_ganado": 0, "misiones": 0,
                      "carreras_taxi": 0, "pizzas": 0, "carreras": [], "tiempo": 0.0, "vendidos": 0}

    def a_dict(self):
        d = dict(self.__dict__)
        d.pop("veh", None)
        d.pop("t_ataque", None)
        return d

    def de_dict(self, d):
        base = Jugador()
        for k, v in d.items():
            if k in base.__dict__ and k not in ("veh",):
                setattr(self, k, v)
        for k, v in base.stats.items():
            self.stats.setdefault(k, v)
        self.veh = None


class Vehiculo:
    n = 0

    def __init__(self, modelo, x, y, d=0, ia=None):
        Vehiculo.n += 1
        self.id = Vehiculo.n
        self.modelo = modelo
        self.nombre = modelo["nombre"]
        self.x = x
        self.y = y
        self.dir = d
        self.rumbo = d * 90.0
        self.vel = 0.0
        self.salud = float(modelo["salud"])
        self.salud_max = float(modelo["salud"])
        self.ia = ia                # None, 'trafico', 'policia', 'huida', 'aparcado'
        self.giro = 0               # -1 izquierda, 1 derecha, 2 media vuelta
        self.lat = 0.0
        self.canal = None
        self.sirena = None
        self.alarma = None
        self.fuego = None
        self.cerrado = False
        self.con_alarma = False
        self.tag = None
        self.plaza = None
        self.ocupado = False
        self.desplegado = False
        self.t_parado = 0.0
        self.t_choque = 0.0
        self.t_giro = 0.0
        self.t_claxon = 0.0
        self.ardiendo = -1.0
        self.muerto = False
        self.hostil = False
        self.aviso_cruce = None
        self.vel_obj = 11.0

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def callar(self):
        for c in (self.canal, self.sirena, self.alarma, self.fuego):
            if c is not None:
                c.parar()
        self.canal = self.sirena = self.alarma = self.fuego = None


class Persona:
    n = 0

    def __init__(self, tipo, x, y, nombre=None):
        Persona.n += 1
        self.id = Persona.n
        self.tipo = tipo            # civil, banda, policia, enemigo
        self.nombre = nombre or {"civil": "Peatón", "banda": "Calavera", "policia": "Policía"}.get(tipo, "Enemigo")
        self.x = x
        self.y = y
        self.salud = 50.0
        self.arma = None
        self.hostil = False
        self.estado = "pasea"       # pasea, huye, ataca, quieto
        self.tag = None
        self.muerto = False
        self.bloque = None
        self.u = 0.0
        self.sentido = 1
        self.vel = 1.3
        self.t_paso = 0.0
        self.t_disparo = 1.0
        self.t_aviso = 0.0
        self.avisado = False
        self.t_estado = 0.0
        self.t_voz = 0.0
        self.t_arresto = 0.0
        self.activo = True

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)


class Objeto:
    n = 0

    def __init__(self, tipo, nombre, x, y, sonido="loc_objeto"):
        Objeto.n += 1
        self.id = Objeto.n
        self.tipo = tipo            # mision, casete, botiquin, dinero
        self.nombre = nombre
        self.x = x
        self.y = y
        self.sonido = sonido
        self.canal = None
        self.tag = None
        self.valor = 0

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)
