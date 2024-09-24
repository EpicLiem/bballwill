from flask import Flask
from flask import request
import datetime

app = Flask(__name__)

playerlist = []

@app.route("/player/register/<name>")
def register(name):
    # Get the UNIX timestamp from query parameters, or default to current UTC time
    time_str = request.args.get('time', None)
    
    if time_str:
        # Parse the provided UNIX timestamp
        try:
            ts = datetime.datetime.utcfromtimestamp(int(time_str))
        except ValueError:
            return "Invalid UNIX timestamp. Provide the time in seconds since epoch."
    else:
        # Use current UTC time if no time is provided
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

@app.route("/will/pretty")
def pretty_list():
    if not playerlist:
        return "<h1>No players registered yet.</h1>"
    
    import pytz
    from datetime import datetime

    eastern_tz = pytz.timezone('US/Eastern')
    
    def parse_time(time_str):
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                pass
        raise ValueError(f"Time data '{time_str}' does not match any known format")
    
    formatted_list = ""
    for index, player in enumerate(playerlist, 1):
        utc_time = parse_time(player['time'])
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
        eastern_time = utc_time.astimezone(eastern_tz)
        
        formatted_list += f"""
        <h2>Player {index}:</h2>
        <ul>
            <li><strong>Name:</strong> {player['name']}</li>
            <li><strong>Registration Time (ET):</strong> {eastern_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')}</li>
            <li><strong>User Agent:</strong> {player['useragent']}</li>
        </ul>
        <hr>
        """
    
    return f"""
    <html>
        <head>
            <title>Pretty Player List</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                }}
                ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                li {{
                    margin-bottom: 5px;
                }}
                hr {{
                    border: 0;
                    border-top: 1px solid #ddd;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <h1>Registered Players</h1>
            {formatted_list}
            <form action="/will/resetv2" method="post">
                <input type="submit" name="reset" value="Reset List" />
            </form>
        </body>
    </html>
    """

@app.route("/will/resetv2", methods = ['POST'])
def reset():
    playerlist.clear()
    return "wiped list"

if __name__ == "__main__":
    app.run(port=8080)