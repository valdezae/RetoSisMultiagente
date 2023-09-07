from flask import Flask, jsonify, request
from model import Warehouse, Ant, Shelves, Conveyors, Packages

app = Flask(__name__)
model = None  # Global variable to hold the model

@app.route('/api/init', methods=['POST'])
def init_model():
    global model
    model = Warehouse(M = 47, N = 20)  # Initialize Mesa model
    return jsonify({"status": "Model initialized"}), 200

@app.route('/api/state', methods=['GET'])
def get_state():
    global model
    if model is None:
        return jsonify({"error": "Model not initialized"}), 400
    
    agents_state = []

    for agent in model.schedule.agents:
        if isinstance(agent, (Ant, Shelves, Conveyors, Warehouse, Packages)):
            agent_data = {"id": agent.unique_id, "position": agent.pos, "type": type(agent).__name__}
            for attr, value in agent.__dict__.items():
                if attr not in ["unique_id", "pos"]:
                    if isinstance(value, Warehouse):
                        agent_data[attr] = str(value)
                    else:
                        agent_data[attr] = value
            agents_state.append(agent_data)

    return jsonify(agents_state), 200

@app.route('/api/step', methods=['POST'])
def step_model():
    global model
    if model is None:
        return jsonify({"error": "Model not initialized"}), 400

    model.step()  # Call the step method of your Mesa model
    return jsonify({"status": "Model stepped"}), 200

if __name__ == '__main__':
    app.run(port=5000)
