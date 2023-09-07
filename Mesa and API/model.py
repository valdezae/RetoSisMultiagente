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
        self.is_shelf = False


class Ant(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.next_position = None
        self.state = 0  # 0: Rest #1: Picking Up(Conveyor) #2: Picking Up(Shelves) #3: Delivering #4: Charging
        self.haul_sku = None
        self.haul_destination_pos = None
        self.has_package = None
        self.package = None
        self.charge_percentage = 100
        self.target_pos = (1, 1)
        self.charging_stations = [(46, 8), (46, 9), (46, 10), (46, 11)]
        self.neighbour_list = list()

    def move_to_target_pos(self, neighbour_list):
        if self.target_pos is None:
            print("No target pos")
            return

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
        self.state = 4
        self.charge_percentage = min(current_charge + 25, 100)

    def step(self):

        neighbours = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=True)
        filtered_neighbours = list()
        shelve_pos = list()

        if self.has_package:
            for neighbour in neighbours:
                if isinstance(neighbour, (ChargingStation, Conveyors)):
                    filtered_neighbours.append(neighbour)
                if isinstance(neighbour, Cell) and not neighbour.is_shelf:
                    filtered_neighbours.append(neighbour)
                if neighbour.pos == self.target_pos:
                    filtered_neighbours.append(neighbour)
        else:
            for neighbour in neighbours:
                if isinstance(neighbour, (Cell, ChargingStation, Conveyors)):
                    filtered_neighbours.append(neighbour)

        print(self.state, self.target_pos)
        print(filtered_neighbours)

        for cell in self.model.grid.coord_iter():
            cell_content, pos = cell
            for obj in cell_content:
                # from receiving conveyor to shelves
                if isinstance(obj, Conveyors) and obj.pos == self.pos and self.state == 1:
                    self.target_pos = self.haul_destination_pos
                    self.state = 3
                # from shelves and to exit conveyor
                elif isinstance(obj,
                                Shelves) and obj.pos == self.pos and self.state == 2 and self.pos == self.target_pos:
                    self.has_package = True
                    obj.is_free = True
                    self.target_pos = self.haul_destination_pos
                    self.state = 3
                    self.package.state = 2
                # leaving at exit conveyor
                elif isinstance(obj, Conveyors) and obj.pos == self.pos and self.state == 3:
                    print("exit")
                    self.state = 0
                    self.package.state = 3
                    self.has_package = False
                    self.target_pos = (1, 0)
                    self.package = None
                elif isinstance(obj, Shelves) and obj.pos == self.pos and self.state == 3 and obj.is_free:
                    obj.is_free = False
                    obj.is_locked = False
                    self.state = 0
                    self.target_pos = (1, 0)
                    self.has_package = False
                    self.package.state = 0
                    self.package.is_locked = False
                    self.package = None


        if self.charge_percentage <= 25 and not self.has_package:
            self.state = 4
            self.target_pos = self.charging_stations[random.randint(0, 3)]

        current_cell_content = self.model.grid.get_cell_list_contents(self.pos)
        for content in current_cell_content:
            if isinstance(content, Packages) and self.pos == (46, 6):
                self.package = content
                self.has_package = True
            elif isinstance(content, Conveyors) and self.pos == (46, 6):
                content.has_package = False

        for content in current_cell_content:
            if isinstance(content, Packages) and self.pos == self.target_pos:
                self.package = content
                self.has_package = True
            elif isinstance(content, Shelves) and self.pos == self.target_pos:
                content.is_free = True

        if self.pos not in self.charging_stations:
            self.charge_percentage -= .25

        print(self.state, self.next_position)

        print(self.haul_destination_pos)

        self.move_to_target_pos(filtered_neighbours)

        if self.pos in self.charging_stations and self.charge_percentage < 99 and not self.has_package:
            self.charge(self.charge_percentage)
            self.target_pos = self.pos
            return

        if self.pos in self.charging_stations and self.charge_percentage >= 99 and not self.has_package:
            self.charge(self.charge_percentage)
            self.target_pos = (1, 1)
            self.state = 0
            return

    def advance(self):
        self.model.grid.move_agent(self, self.next_position)
        if self.has_package == True:
            self.model.grid.move_agent(self.package, self.next_position)


class Conveyors(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.has_package = False
        self.state = 0  # 1 Entrance, 2 Exit


class Packages(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sku = unique_id
        self.state = 0  # 0: In storage #1: Awaiting pickup #2: In transit #3: Sent
        self.is_locked = False


class Shelves(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_free = True
        self.is_locked = False


class CentralSystem(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.package_counter = 0
        self.entrance_position = (46, 6)
        self.exit_position = (46, 13)

    def entrance_pos(self):
        cell_content = self.model.grid.get_cell_list_contents([self.entrance_position])
        # print(cell_content)
        for obj in cell_content:
            if isinstance(obj, Packages) and obj.state == 1:
                return None
            if isinstance(obj, Packages) and obj.state == 0:
                obj.state = 1
            if isinstance(obj, Conveyors) and obj.state == 1 and obj.has_package:
                return self.entrance_position

    def find_closest_agent_to_objective(self, objective):
        least_distance_to_objective = math.inf
        closest_agent = None
        for cell in self.model.grid.coord_iter():
            for obj in cell:
                for agent in obj:
                    if isinstance(agent, Ant) and agent.state == 0:
                        distance_to_objective = math.dist(agent.pos, objective)
                        if distance_to_objective < least_distance_to_objective:
                            least_distance_to_objective = distance_to_objective
                            closest_agent = agent
        return closest_agent

    def exit_pos(self):
        for cell in self.model.grid.coord_iter():
            cell_content, pos = cell
            for obj in cell_content:
                if isinstance(obj, Conveyors) and obj.state == 2:
                    return pos

    def free_shelf(self, entrance):  # This function finds a free space in a shelf for a new package

        neighbours = entrance.model.grid.get_neighbors(
            entrance.pos, moore=True, include_center=True, radius=50)
        nearest_neighbour_pos = None
        least_distance = math.inf
        for neighbour in neighbours:
            if isinstance(neighbour, Shelves) and neighbour.is_free:
                distance = math.dist(neighbour.pos, entrance.pos)
                if distance < least_distance:
                    least_distance = distance
                    nearest_neighbour_pos = neighbour.pos
        if nearest_neighbour_pos is not None:
            return nearest_neighbour_pos
        return None  # If no free spaces are found (make ant stay at rest?)

    def generate_exit_mission_package(self):
        if self.free_shelf() is None:
            for cell in self.model.grid.coord_iter():
                cell_content, pos = cell
                for obj in cell_content:
                    if isinstance(obj, Packages):
                        return pos  # Returns the first free space found

    def step(self):
        # creates mission for entry conveyor
        # print(self.entrance_pos())
        if self.entrance_pos() is not None:
            for obj in self.model.grid.get_cell_list_contents((46, 6)):
                if isinstance(obj, Packages):
                    entrance_package = obj
                if isinstance(obj, Conveyors) and obj.state == 1:
                    entrance_conveyor = obj
            if not entrance_package.is_locked:
                closest_ant = self.find_closest_agent_to_objective(self.entrance_pos())
                if closest_ant is not None:
                    closest_ant.state = 1
                    closest_ant.target_pos = self.entrance_pos()
                    posdest = self.free_shelf(entrance_conveyor)
                    destination = self.model.grid.get_cell_list_contents(posdest)
                    for contents in destination:
                        if isinstance(contents, Shelves):
                            contents.is_locked = True
                    closest_ant.haul_destination_pos = posdest
                    entrance_package.is_locked = True
                else:
                    print("no ant found")

        exit_mission_pos = 0
        paquete = None

        for cell in self.model.grid.coord_iter():
            cell_content, pos = cell
            for obj in cell_content:
                if isinstance(obj, Shelves) and not obj.is_free:
                    exit_mission_pos = obj.pos

                if isinstance(obj, Packages):
                    paquete = obj
        # creates package exit mission
        chance = random.randint(1, 100)
        print(exit_mission_pos)
        if exit_mission_pos != 0 and not paquete.is_locked and chance < 75:
            package_pos = exit_mission_pos
            closest_ant = self.find_closest_agent_to_objective(package_pos)
            if closest_ant is not None:
                closest_ant.state = 2
                closest_ant.target_pos = package_pos
                closest_ant.haul_destination_pos = self.exit_position
                closest_ant.package = paquete
                paquete.is_locked = True



class Warehouse(Model):
    def __init__(self, M: int = 47, N: int = 20,
                 num_agentes: int = 1,
                 porc_shelves: float = 0.2,
                 modo_pos_inicial: str = 'Fija',
                 ):

        self.entrance_conveyor = None
        self.num_agentes = num_agentes
        self.porc_shelves = porc_shelves

        self.grid = MultiGrid(M, N, False)
        self.schedule = SimultaneousActivation(self)

        central_system = CentralSystem(unique_id="central_system", model=self)
        self.schedule.add(central_system)

        posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        uniqueID = 0

        for (idc, pos) in enumerate(posiciones_disponibles):
            cell = Cell(int(f"{num_agentes}{idc}") + 1, self)
            uniqueID += 1
            self.grid.place_agent(cell, pos)
            self.schedule.add(cell)

        entrance_conveyor = Conveyors(int(f"{num_agentes}") + 1, self)
        self.grid.place_agent(entrance_conveyor, (46, 6))  # Bottom left
        entrance_conveyor.state = 1  # Entrance conveyor
        uniqueID += 1
        self.schedule.add(entrance_conveyor)
        entrance_conveyor.has_package = True
        self.entrance_conveyor = entrance_conveyor

        sample_package = Packages(uniqueID, model=self)
        self.grid.place_agent(sample_package, (46, 6))
        uniqueID += 1
        self.schedule.add(sample_package)

        exit_conveyor = Conveyors(unique_id="exit_conveyor", model=self)
        exit_conveyor.state = 2  # Exit conveyor
        self.grid.place_agent(exit_conveyor, (46, 13))  # Top right
        uniqueID += 1
        self.schedule.add(exit_conveyor)


        posiciones_estaciones = [(46, 8), (46, 9), (46, 10), (46, 11)]
        for id, pos in enumerate(posiciones_estaciones):
            x, y = pos
            if x < 0 or x >= M or y < 0 or y >= N:
                print(f"ChargingStation position {pos} is out of grid dimensions.")
                continue


            if pos not in posiciones_disponibles:
                print(f"ChargingStation position {pos} is not available in posiciones_disponibles.")
                continue

            estacion = ChargingStation(int(f"{num_agentes}0{id}") + 1, self)
            self.grid.place_agent(estacion, pos)
            uniqueID += 1
            posiciones_disponibles.remove(pos)


        num_shelves = 5

        posiciones_shelves = [(2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12),
                              (2, 13), (2, 14), (2, 15), (2, 16),
                              # (3,3), (3,4), (3,5), (3,6), (3,7), (3,8), (3,9), (3,10), (3,11), (3,12), (3,13), (3,14), (3,15), (3,16),
                              (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12),
                              (6, 13), (6, 14), (6, 15), (6, 16),
                              # (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12),
                              # (7, 13), (7, 14), (7, 15), (7, 16),
                              (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8), (10, 9), (10, 10), (10, 11),
                              (10, 12),
                              (10, 13), (10, 14), (10, 15), (10, 16),
                              # (11, 3), (11, 4), (11, 5), (11, 6), (11, 7), (11, 8), (11, 9), (11, 10), (11, 11),
                              # (11, 12),
                              # (11, 13), (11, 14), (11, 15), (11, 16),
                              (14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9), (14, 10), (14, 11),
                              (14, 12),
                              (14, 13), (14, 14), (14, 15), (14, 16),
                              # (15, 3), (15, 4), (15, 5), (15, 6), (15, 7), (15, 8), (15, 9), (15, 10), (15, 11),
                              # (15, 12),
                              # (15, 13), (15, 14), (15, 15), (15, 16),
                              (18, 3), (18, 4), (18, 5), (18, 6), (18, 7), (18, 8), (18, 9), (18, 10), (18, 11),
                              (18, 12),
                              (18, 13), (18, 14), (18, 15), (18, 16),
                              # (19, 3), (19, 4), (19, 5), (19, 6), (19, 7), (19, 8), (19, 9), (19, 10), (19, 11),
                              # (19, 12),
                              # (19, 13), (19, 14), (19, 15), (19, 16),
                              (22, 3), (22, 4), (22, 5), (22, 6), (22, 7), (22, 8), (22, 9), (22, 10), (22, 11),
                              (22, 12),
                              (22, 13), (22, 14), (22, 15), (22, 16),
                              # (23, 3), (23, 4), (23, 5), (23, 6), (23, 7), (23, 8), (23, 9), (23, 10), (23, 11),
                              # (23, 12),
                              # (23, 13), (23, 14), (23, 15), (23, 16),
                              (26, 3), (26, 4), (26, 5), (26, 6), (26, 7), (26, 8), (26, 9), (26, 10), (26, 11),
                              (26, 12),
                              (26, 13), (26, 14), (26, 15), (26, 16),
                              # (27, 3), (27, 4), (27, 5), (27, 6), (27, 7), (27, 8), (27, 9), (27, 10), (27, 11),
                              # (27, 12),
                              # (27, 13), (27, 14), (27, 15), (27, 16),
                              (30, 3), (30, 4), (30, 5), (30, 6), (30, 7), (30, 8), (30, 9), (30, 10), (30, 11),
                              (30, 12),
                              (30, 13), (30, 14), (30, 15), (30, 16),
                              # (31, 3), (31, 4), (31, 5), (31, 6), (31, 7), (31, 8), (31, 9), (31, 10), (31, 11),
                              # (31, 12),
                              # (31, 13), (31, 14), (31, 15), (31, 16),
                              (34, 3), (34, 4), (34, 5), (34, 6), (34, 7), (34, 8), (34, 9), (34, 10), (34, 11),
                              (34, 12),
                              (34, 13), (34, 14), (34, 15), (34, 16),
                              # (35, 3), (35, 4), (35, 5), (35, 6), (35, 7), (35, 8), (35, 9), (35, 10), (35, 11),
                              # (35, 12),
                              # (35, 13), (35, 14), (35, 15), (35, 16),
                              (38, 3), (38, 4), (38, 5), (38, 6), (38, 7), (38, 8), (38, 9), (38, 10), (38, 11),
                              (38, 12),
                              (38, 13), (38, 14), (38, 15), (38, 16),
                              # (39, 3), (39, 4), (39, 5), (39, 6), (39, 7), (39, 8), (39, 9), (39, 10), (39, 11),
                              # (39, 12),
                              # (39, 13), (39, 14), (39, 15), (39, 16),
                              (42, 3), (42, 4), (42, 5), (42, 6), (42, 7), (42, 8), (42, 9), (42, 10), (42, 11),
                              (42, 12),
                              (42, 13), (42, 14), (42, 15), (42, 16),
                              # (43, 3), (43, 4), (43, 5), (43, 6), (43, 7), (43, 8), (43, 9), (43, 10), (43, 11),
                              # (43, 12),
                              # (43, 13), (43, 14), (43, 15), (43, 16),
                              (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0),
                              (11, 0), (12, 0), (13, 0), (14, 0), (15, 0), (16, 0), (17, 0), (18, 0), (19, 0), (20, 0),
                              (21, 0), (22, 0), (23, 0), (24, 0), (25, 0), (26, 0), (27, 0), (28, 0), (29, 0), (30, 0),
                              (31, 0), (32, 0), (33, 0), (34, 0),
                              (35, 0), (36, 0), (37, 0), (38, 0), (39, 0), (40, 0), (41, 0), (42, 0), (43, 0), (44, 0),
                              (45, 0), (46, 0),
                              (0, 19), (1, 19), (2, 19), (3, 19), (4, 19), (5, 19), (6, 19), (7, 19), (8, 19), (9, 19),
                              (10, 19),
                              (11, 19), (12, 19), (13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (19, 19),
                              (20, 19),
                              (21, 19), (22, 19), (23, 19), (24, 19), (25, 19), (26, 19), (27, 19), (28, 19), (29, 19),
                              (30, 19),
                              (31, 19), (32, 19), (33, 19), (34, 19),
                              (35, 19), (36, 19), (37, 19), (38, 19), (39, 19), (40, 19), (41, 19), (42, 19), (43, 19),
                              (44, 19),
                              (45, 19), (46, 19),
                              ]

        for id, pos in enumerate(posiciones_shelves):
            x, y = pos
            if x < 0 or x >= M or y < 0 or y >= N:
                print(f"ChargingStation position {pos} is out of grid dimensions.")
                continue


            if pos not in posiciones_disponibles:
                print(f"ChargingStation position {pos} is not available in posiciones_disponibles.")
                continue

            shelf = Shelves(int(f"{num_agentes}0{id}") + 1, self)
            self.grid.place_agent(shelf, pos)
            self.schedule.add(shelf)
            contents = self.grid.get_cell_list_contents(pos)
            for content in contents:
                if isinstance(content, Cell):
                    content.is_shelf = True
            uniqueID += 1
            posiciones_disponibles.remove(pos)

        # Posicionamiento de agentes
        if modo_pos_inicial == 'Aleatoria':
            pos_inicial_robots = self.random.sample(posiciones_disponibles, k=num_agentes)
        else:  # 'Fija'
            pos_inicial_robots = [(1, 1)] * num_agentes

        for id in range(num_agentes):
            robot = Ant(id, self)
            self.grid.place_agent(robot, pos_inicial_robots[id])
            uniqueID += 1
            self.schedule.add(robot)
            robot.state = 0

        self.datacollector = DataCollector(
            model_reporters={"Grid": get_grid},
        )

    def step(self):
        chance = random.randint(1, 100)
        chanceID = random.randint(1, 1000000)
        if chance < 15:
            sample_package = Packages(f"package_{chanceID}", model=self)
            self.grid.place_agent(sample_package, (46, 6))
            self.schedule.add(sample_package)
            self.entrance_conveyor.has_package = True

        for cell in self.grid.coord_iter():
            cell_content, pos = cell
            for obj in cell_content:
                if isinstance(obj, Packages) and obj.state == 3:
                    print("remove")
                    self.grid.remove_agent(obj)
                    self.schedule.remove(obj)

        self.datacollector.collect(self)
        self.schedule.step()


def get_grid(model: Model) -> np.ndarray:

    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        x, y = pos
        for obj in cell_content:
            if isinstance(obj, Ant):
                grid[x][y] = 2
    return grid