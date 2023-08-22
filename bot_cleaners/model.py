from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import numpy as np
import math


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
        self.state = 0  # 0: Rest #1: Moving #2: Hauling #3: Charging
        self.haul_sku = None
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

    def haul_package(self, package_sku):
        self.state = 2
        self.haul_sku = package_sku

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

        if self.state == 2:
            for neighbour in neighbours:
                if isinstance(neighbour, (Cell, ChargingStation, Conveyors)):
                    filtered_neighbours.append(neighbour)
        else:
            for neighbour in neighbours:
                if isinstance(neighbour, (Cell, ChargingStation, Conveyors, Shelves)):
                    filtered_neighbours.append(neighbour)

        self.move_to_target_pos(filtered_neighbours)



        if self.pos in self.charging_stations and self.charge_percentage < 99:
            self.charge(self.charge_percentage)
            self.next_position = self.pos
            return
        elif




class Conveyors(Agent):
    def __init__(self, unique_id, model, has_package: bool = False):
        super().__init__(unique_id, model)
        self.conveyor_id = None
        self.has_package = has_package


class Packages(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sku = unique_id
        self.state = 0 #0: In storage #1: Awaiting pickup #2: In transit #3: Sent
        self.peso = None


class Shelves(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.shelf_id = None
        self.current_packages = list()
        self.is_free = True
        self.current_package_skus = list()


class CentralSystem(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
