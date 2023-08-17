from flask import Flask
from flask import request
import datetime

app = Flask(__name__)

playerlist = [{'name': 'Tes Ayele', 'time': '2023-08-16 19:10:42.879411'}, {'name': 'Tyler Rohrbaugh', 'time': '2023-08-16 19:11:08.159057'}, {'name': 'Tes Ayele', 'time': '2023-08-16 19:11:18.897180'}, {'name': 'Duane Gordon', 'time': '2023-08-16 19:11:19.864433'}, {'name': 'Tyler Rohrbaugh', 'time': '2023-08-16 19:11:59.767156'}, {'name': 'Tyler Rohrbaugh', 'time': '2023-08-16 19:12:14.991887'}, {'name': 'Avery Brown', 'time': '2023-08-16 19:12:33.302438'}, {'name': 'Avery Brown', 'time': '2023-08-16 19:13:30.625543'}, {'name': 'Avery Brown', 'time': '2023-08-16 19:14:01.218343'}, {'name': 'Avery Brown', 'time': '2023-08-16 19:14:15.190170'}, {'name': 'Caleb Mactavesh', 'time': '2023-08-16 19:17:24.409250'}, {'name': 'Alex Cehak', 'time': '2023-08-16 19:27:14.648587'}, {'name': 'Stephen Stewart', 'time': '2023-08-17 04:10:32.038474'}]

@app.route("/player/register/<name>")
def register(name):
    ts = datetime.datetime.utcnow()
    playerlist.append({"name": name, "time": str(ts), "useragent": request.headers.get('User-Agent')})
    return f"<h1>It worked. You have been registered as {name}. The next step is to pay to lock in your spot.</h1>"

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
