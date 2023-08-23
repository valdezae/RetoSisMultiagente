from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import numpy as np
import math
import random


class ChargingStation(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Cell(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Ant(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.next_position = None
        self.state = 0  # 0: Rest #1: Picking Up(Conveyor) #2: Picking Up(Shelves) #3: Delivering #4: Charging
        self.haul_sku = None
        self.haul_destination_pos = None
        self.charge_percentage = 100
        self.target_pos = None
        self.charging_stations = [(5, 5), (5, 15), (15, 5), (15, 15)]

    def move_to_target_pos(self, neighbour_list):
        least_distance_to_target = math.inf
        target_position = self.target_pos
        for neighbour in neighbour_list:
            distance = math.dist(neighbour.pos, target_position)
            if distance < least_distance_to_target:
                least_distance_to_target = distance
                self.next_position = neighbour.pos

    def deliver_package(self):
        self.state = 1
        self.haul_sku = None

    def charge(self, current_charge):
        self.state = 3
        self.charge_percentage = min(current_charge + 25, 100)

    def step(self):
        neighbours = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False)

        filtered_neighbours = list()

        if self.state == 3:
            for neighbour in neighbours:
                if isinstance(neighbour, (Cell, ChargingStation, Conveyors)):
                    filtered_neighbours.append(neighbour)
        else:
            for neighbour in neighbours:
                if isinstance(neighbour, (Cell, ChargingStation, Conveyors, Shelves)):
                    filtered_neighbours.append(neighbour)

        for cell in self.model.grid.coord_iter():
            cell_content, pos = cell
            for obj in cell_content:
                # from receiving conveyor to shelves
                if isinstance(obj, Conveyors) and obj.pos == self.pos and self.state == 1:
                    self.target_pos = self.haul_destination_pos
                    self.state = 3
                # from shelves and to exit conveyor
                elif isinstance(obj, Shelves) and obj.pos == self.pos and self.state == 2:
                    self.target_pos = self.haul_destination_pos
                    self.state = 3
                # leaving at exit conveyor
                elif isinstance(obj, Conveyors) and obj.pos == self.pos and self.state == 3:
                    self.state = 0
                    self.target_pos = (0, 0)

        if self.charge_percentage <= 25:
            self.state = 4
            self.target_pos = self.charging_stations[random.randint(0, 3)]

        if self.pos in self.charging_stations and self.charge_percentage < 99:
            self.charge(self.charge_percentage)
            self.target_pos = self.pos
            return

        self.move_to_target_pos(filtered_neighbours)


class Conveyors(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.has_package = False


class Packages(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sku = unique_id
        self.state = 0  # 0: In storage #1: Awaiting pickup #2: In transit #3: Sent
        self.peso = None
        self.target_pos = None
        self.next_position = None

    def move_to_target_pos(self, neighbour_list):
        least_distance_to_target = math.inf
        target_position = self.target_pos
        for neighbour in neighbour_list:
            distance = math.dist(neighbour.pos, target_position)
            if distance < least_distance_to_target:
                least_distance_to_target = distance
                self.next_position = neighbour.pos

    def step(self):
        neighbours = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=True)

        filtered_neighbours = list()

        for neighbour in neighbours:
            if isinstance(neighbour, (Ant, Cell, ChargingStation, Conveyors)) and neighbour.haul_sku == self.sku:
                filtered_neighbours.append(neighbour)

        if self.state == 1:
            for cell in self.model.grid.coord_iter():
                cell_content, pos = cell
                for obj in cell_content:
                    if isinstance(obj, Ant) and obj.pos == self.pos:
                        self.target_pos = filtered_neighbours[0].target_pos
                        self.state = 2
        if self.state == 2:  # Si está en tránsito
            for neighbour in filtered_neighbours:
                if isinstance(neighbour, Shelves) and neighbour.pos == self.pos:
                    neighbour.current_packages.append(self)  # Agregar el paquete a la lista de paquetes del estante
                    self.state = 3  # Cambia a estado enviado

    # Nueva parte para detectar estar en un Conveyor de salida
        for neighbour in filtered_neighbours:
            if isinstance(neighbour, Conveyors) and neighbour.has_package:  # Se agrega esta condición
                self.state = 3  # Cambia a estado enviado


class Shelves(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.current_packages = list()
        self.is_free = True
        self.current_package_skus = list()


class CentralSystem(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
