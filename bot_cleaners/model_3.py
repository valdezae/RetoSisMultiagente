from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import numpy as np
import math


class Celda(Agent):
    def __init__(self, unique_id, model, suciedad: bool = False):
        super().__init__(unique_id, model)
        self.sucia = suciedad


class Carga(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Mueble(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class RobotLimpieza(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sig_pos = None
        self.movimientos = 0
        self.carga = 100
        self.centros_de_carga = [(5, 5), (5, 15), (15, 5), (15, 15)]
        self.state = 0  # 0: Limpiando, 1: Cargando
        self.recargas = 0

    def mover_a_carga(self, lista_de_vecinos):
        menor_distancia_estacion = math.inf
        for centro in self.centros_de_carga:
            distancia_estacion = math.dist(self.pos, centro)
            if distancia_estacion < menor_distancia_estacion:
                menor_distancia_estacion = distancia_estacion
                estacion_cercana = centro

        menor_distancia = math.inf
        for vecino in lista_de_vecinos:
            distancia = math.dist(vecino.pos, estacion_cercana)
            if distancia < menor_distancia:
                menor_distancia = distancia
                self.sig_pos = vecino.pos

    def mover_a_sucia(self, lista_de_vecinos):
        menor_distancia_sucia = math.inf
        posicion_cercana_sucia = None
        for dirty_cell_pos in self.model.dirty_cells:
            distancia_a_sucia = math.dist(self.pos, dirty_cell_pos)

            if distancia_a_sucia < menor_distancia_sucia:
                menor_distancia_sucia = distancia_a_sucia
                posicion_cercana_sucia = dirty_cell_pos

        if posicion_cercana_sucia:
            best_next_step = min(lista_de_vecinos, key=lambda x: math.dist(x.pos, posicion_cercana_sucia))
            self.sig_pos = best_next_step.pos
        else:
            self.sig_pos = self.random.choice(lista_de_vecinos).pos

    def cargar(self, carga_actual):
        self.carga = min(carga_actual + 25, 100)

    def limpiar_una_celda(self, lista_de_celdas_sucias):
        celda_a_limpiar = self.random.choice(lista_de_celdas_sucias)
        celda_a_limpiar.sucia = False
        self.model.update_dirty_cells(celda_a_limpiar)
        self.sig_pos = celda_a_limpiar.pos

    def seleccionar_nueva_pos(self, lista_de_vecinos):
        self.sig_pos = self.random.choice(lista_de_vecinos).pos

    @staticmethod
    def buscar_celdas_sucia(lista_de_vecinos):
        # #Opción 1
        # return [vecino for vecino in lista_de_vecinos
        #                 if isinstance(vecino, Celda) and vecino.sucia]
        # #Opción 2
        celdas_sucias = list()
        for vecino in lista_de_vecinos:
            if isinstance(vecino, Celda) and vecino.sucia:
                celdas_sucias.append(vecino)
        return celdas_sucias

    def step(self):
        vecinos = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False)

        vecinos_filtrado = list()
        for vecino in vecinos:
            if isinstance(vecino, (Celda, Carga)):
                vecinos_filtrado.append(vecino)

        celdas_sucias = self.buscar_celdas_sucia(vecinos_filtrado)

        if self.pos in self.centros_de_carga and self.carga == 99:
            self.recargas += 1

        # En centro de carga
        if self.pos in self.centros_de_carga and self.carga < 99:
            self.cargar(self.carga)
            self.sig_pos = self.pos
            self.state = 1
            return

        # se dirige a estacion de carga
        elif self.carga <= 25:
            self.state = 0
            self.mover_a_carga(vecinos_filtrado)

        # celdas sucias vecinas, limpiarlas
        elif celdas_sucias:
            self.state = 0
            self.limpiar_una_celda(celdas_sucias)

        # moverse a celdas sucias
        else:
            self.state = 0
            self.mover_a_sucia(vecinos_filtrado)

    def advance(self):
        if self.pos != self.sig_pos:
            self.movimientos += 1

        if self.carga > 0:
            self.carga -= 1
            self.model.grid.move_agent(self, self.sig_pos)


class Habitacion(Model):
    def __init__(self, M: int, N: int,
                 num_agentes: int = 5,
                 porc_celdas_sucias: float = 0.6,
                 porc_muebles: float = 0.1,
                 modo_pos_inicial: str = 'Fija',
                 ):

        self.num_agentes = num_agentes
        self.porc_celdas_sucias = porc_celdas_sucias
        self.porc_muebles = porc_muebles
        self.dirty_cells = list()
        self.current_steps = 0
        self.final_steps = 0

        self.grid = MultiGrid(M, N, False)
        self.schedule = SimultaneousActivation(self)

        posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        posiciones_estaciones = [(5, 5), (5, 15), (15, 5), (15, 15)]
        for id, pos in enumerate(posiciones_estaciones):
            estacion = Carga(int(f"{num_agentes}0{id}") + 1, self)
            self.grid.place_agent(estacion, pos)
            posiciones_disponibles.remove(pos)

        # Posicionamiento de muebles
        num_muebles = int(M * N * porc_muebles)
        posiciones_muebles = self.random.sample(posiciones_disponibles, k=num_muebles)

        for id, pos in enumerate(posiciones_muebles):
            mueble = Mueble(int(f"{num_agentes}0{id}") + 1, self)
            self.grid.place_agent(mueble, pos)
            posiciones_disponibles.remove(pos)

        # Posicionamiento de celdas sucias
        self.num_celdas_sucias = int(M * N * porc_celdas_sucias)
        posiciones_celdas_sucias = self.random.sample(
            posiciones_disponibles, k=self.num_celdas_sucias)

        for id, pos in enumerate(posiciones_disponibles):
            suciedad = pos in posiciones_celdas_sucias
            celda = Celda(int(f"{num_agentes}{id}") + 1, self, suciedad)
            self.grid.place_agent(celda, pos)

        # Posicionamiento de agentes robot
        if modo_pos_inicial == 'Aleatoria':
            pos_inicial_robots = self.random.sample(posiciones_disponibles, k=num_agentes)
        else:  # 'Fija'
            pos_inicial_robots = [(1, 1)] * num_agentes

        for id in range(num_agentes):
            robot = RobotLimpieza(id, self)
            self.grid.place_agent(robot, pos_inicial_robots[id])
            self.schedule.add(robot)

        self.datacollector = DataCollector(
            model_reporters={"Grid": get_grid, "Cargas": get_cargas,
                             "CeldasSucias": get_sucias, "Movimientos": get_movimientos,
                             "Recargas": get_recargas},
        )

        self.dirty_cells = get_pos_sucias(self)

        self.current_steps = + 1

        if len(self.dirty_cells) == 0:
            self.final_steps = self.current_steps

    def update_dirty_cells(self, cell):
        if cell.sucia:
            self.dirty_cells.append(cell.pos)
        else:
            self.dirty_cells.remove(cell.pos)

    def step(self):
        self.datacollector.collect(self)

        self.schedule.step()

    def todoLimpio(self):
        for (content, x, y) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, Celda) and obj.sucia:
                    return False
        return True


def get_grid(model: Model) -> np.ndarray:
    """
    Método para la obtención de la grid y representarla en un notebook
    :param model: Modelo (entorno)
    :return: grid
    """
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        x, y = pos
        for obj in cell_content:
            if isinstance(obj, RobotLimpieza):
                grid[x][y] = 2
            elif isinstance(obj, Celda):
                grid[x][y] = int(obj.sucia)
    return grid


def get_cargas(model: Model):
    return [(agent.unique_id, agent.carga) for agent in model.schedule.agents]


def get_sucias(model: Model) -> int:
    """
    Método para determinar el número total de celdas sucias
    :param model: Modelo Mesa
    :return: número de celdas sucias
    """
    sum_sucias = 0
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        for obj in cell_content:
            if isinstance(obj, Celda) and obj.sucia:
                sum_sucias += 1
    return sum_sucias / model.num_celdas_sucias


def get_pos_sucias(model: Model) -> list:
    pos_sucias = list()
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        for obj in cell_content:
            if isinstance(obj, Celda) and obj.sucia:
                pos_sucias.append(obj.pos)
    return pos_sucias


def get_recargas(model: Model):
    sum_recargas = 0
    for agent in model.schedule.agents:
        sum_recargas += agent.recargas
    return sum_recargas


def get_movimientos(model: Model) :
    sum_movimientos = 0
    for agent in model.schedule.agents:
        sum_movimientos += agent.movimientos
    return sum_movimientos
