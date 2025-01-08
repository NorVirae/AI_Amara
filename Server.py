from flask import Flask
from app.agent import Agent
from flask import request

app = Flask(__name__)

@app.get("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/send", methods=['POST'])
def sendChat():
    if request.method == 'POST':
        # Parse JSON data
        data = request.get_json()
        if not data or "message" not in data:
            return {"error": "Bad Request - 'message' field is required"}, 400

        # Process the message
        agent = Agent("Amara")
        return agent.callAgent(data["message"])
    