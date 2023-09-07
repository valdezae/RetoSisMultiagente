import mesa

from model import Warehouse, Ant, ChargingStation, Cell, Conveyors, Packages, Shelves, CentralSystem

MAX_NUMBER_ROBOTS = 20


def agent_portrayal(agent):
    if isinstance(agent, Ant):
        return {"Shape": "circle", "Filled": "false", "Color": "Cyan", "Layer": 1, "r": 0.9,
                "text": f"{agent.charge}", "text_color": "black"}
    elif isinstance(agent, Shelves):
        return {"Shape": "rect", "Filled": "true", "Color": "black", "Layer": 0,
                "w": 0.9, "h": 0.9}
    elif isinstance(agent, Packages):
        return {"Shape": "rect", "Filled": "true", "Color": "brown", "Layer": 0,
                "w": 0.9, "h": 0.9}
    elif isinstance(agent, Cell):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9}
        portrayal["Color"] = "white"
        return portrayal
    elif isinstance(agent, Conveyors):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9}
        if agent.state == 1:  # Entrance
            portrayal["Color"] = "green"
        elif agent.state == 2:  # Exit
            portrayal["Color"] = "red"
        return portrayal
    elif isinstance(agent, ChargingStation):
        return {"Shape": "rect", "Filled": "true", "Color": "yellow", "Layer": 0,
                "w": 0.9, "h": 0.9}


M = 47
N = 20

grid = mesa.visualization.CanvasGrid(
    agent_portrayal, M, N, 700, 400)

model_params = {
    "M": mesa.visualization.Slider(
        "Width",
        47,
        5,
        50,
        1,
        description="Grid width",
    ),
    "N": mesa.visualization.Slider(
        "Height",
        20,
        5,
        50,
        1,
        description="Grid height",
    ),
}

server = mesa.visualization.ModularServer(
    Warehouse, [grid],
    "Warehouse Model", model_params, 8008
)
