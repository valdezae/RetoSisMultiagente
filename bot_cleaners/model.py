from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import numpy as np


class Ant(Agent):
    def __init__(self, unique_id, model, hauling: bool = False):
        super().__init__(unique_id, model)
        self.next_position = None
        self.hauling = hauling
        self.load_sku = None
        self.charge = 100


class Conveyors(Agent):
    def __init__(self, unique_id, model, has_package: bool = False):
        super().__init__(unique_id, model)
        self.conveyor_id = None
        self.has_package = has_package


class Packages(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sku = unique_id
        self.in_storage = False
        self.is_sent = False
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

