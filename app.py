from flask import Flask
import datetime

app = Flask(__name__)

playerlist = []

@app.route("/player/register/<name>")
def register(name):
    ts = datetime.datetime.utcnow()
    playerlist.append({"name": name, "time": str(ts)})
    return f"<h1>Registered as {name}</h1>"

@app.route("/player/remove/<name>")
def remove(name):
    try:
        index = playerlist.index(name)
        playerlist.pop(index)
        return f"<h1>Removed {name}</h1>"
    except:
        return "<h1>Player not found</h1>"

@app.route("/will/list")
def list():
    return str(playerlist)

@app.route("/will/reset")
def reset():
    playerlist.clear()
    return "wiped list"

if __name__ == "__main__":
    app.run()