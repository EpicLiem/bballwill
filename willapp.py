from flask import Flask
from flask import request
import datetime

app = Flask(__name__)

playerlist = []

@app.route("/player/register/<name>")
def register(name):
    ts = datetime.datetime.utcnow()
    playerlist.append({"name": name, "time": str(ts), "useragent": request.headers.get('User-Agent')})
    return f"""
    <html>
        <head>
            <title>Registration</title>
            <link rel="stylesheet"
          href="https://fonts.googleapis.com/css?family=Courier+Prime">

            <style>
            body {{
                    background-color: #1e1e1e;
                }}
                h1 {{
                    color: white;
                    font-family: 'Courier Prime', monospace;
                    text-align: center;
                }}
            </style>
        
        <body>      
            <h1>It worked. You are now registered as {name}.</h1>
            <h1>The next step is to pay to lock in your spot.</h1>
            <h1>CLICK ONE</h1>
            <a href=\"https:\/\/venmo.com\/u\/will_luttrell\" target="_blank"><h1>Venmo</h1></a>
            <a href=\"https:\/\/cash.app/$luttrellwill\"" target="_blank"><h1>Cash App</h1></a>
            <a href=\"https:\/\/www.paypal.com/paypalme/paywillnowplease\"" target="_blank"><h1>Paypal</h1></a>
            <a href=\"sms:+12014460400"" target="_blank"><h1>Apple Pay</h1></a>
        <body>
    <html>
    """


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
    return f"""{str(playerlist)}
    <form action="/will/resetv2" method="post">
        <input type="submit" name="reset" value="reset" />
    </form>

    """

@app.route("/will/resetv2", methods = ['POST'])
def reset():
    playerlist.clear()
    return "wiped list"

if __name__ == "__main__":
    app.run(port=8080, debug=True)

