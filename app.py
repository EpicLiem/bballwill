from flask import Flask
from flask import request
import datetime

app = Flask(__name__)

playerlist = []

@app.route("/player/register/<name>")
def register(name):
    ts = datetime.datetime.utcnow()
    playerlist.append({"name": name, "time": str(ts), "useragent": request.headers.get('User-Agent')})
    return f"""<h1>It worked. You have been registered as {name}.</h1><h1>The next step is to pay to lock in your spot.</h1><a href=\"https:\/\/venmo.com\/u\/will_luttrell\"><h1>Venmo</h1></a><a href=\"https:\/\/cash.app/$luttrellwill\"><h1>Cash App</h1></a>"""

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
