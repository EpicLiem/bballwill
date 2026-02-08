from flask import Flask
from flask import request
import datetime

app = Flask(__name__)

playerlist = []


def format_duration(seconds):
    """Format seconds as 'X days Y hours Z minutes W seconds', omitting zero parts."""
    secs = int(seconds)
    if secs < 0:
        return "0 seconds"
    days = secs // 86400
    secs %= 86400
    hours = secs // 3600
    secs %= 3600
    minutes = secs // 60
    secs %= 60
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs > 0 or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return " ".join(parts)

@app.route("/player/register/<name>")
def register(name):
    # Get the UNIX timestamp from query parameters, or default to epoch time (0)
    time_str = request.args.get('uid', '0')
    
    try:
        # Parse the provided or default UNIX timestamp
        time_sent = datetime.datetime.utcfromtimestamp(int(time_str))
    except ValueError:
        return "Invalid UNIX timestamp. Provide the time in seconds since epoch."

    # Use current UTC time for the actual registration time
    ts = datetime.datetime.utcnow()
    click_time_seconds = (ts - time_sent).total_seconds()
    if click_time_seconds < 0 or click_time_seconds > 86400 * 365:
        congrats_line = f"Congrats! You are now registered as {name}."
    else:
        congrats_line = f"Congrats! Your click time was {format_duration(click_time_seconds)}. You are now registered as {name}."

    playerlist.append({
        "name": name,
        "time": str(ts),
        "time_sent": str(time_sent),
        "useragent": request.headers.get('User-Agent')
    })
    
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
            <h1>{congrats_line}</h1>
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
    # Trim whitespace from the input name
    name = name.strip()
    
    # Find and remove the player by name from the playerlist
    for i, player in enumerate(playerlist):
        player_name = player['name'].strip()
        if player_name == name:
            playerlist.pop(i)
            return f"<h1>Removed {name}</h1>"
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
    
    # Compute time_clicked (seconds between registration and time_sent) per entry
    # and find each name's personal fastest (min time_clicked)
    time_clicked_seconds_list = []
    for player in playerlist:
        utc_time = parse_time(player['time']).replace(tzinfo=pytz.UTC)
        time_sent_str = player['time_sent']
        try:
            time_sent_utc = parse_time(time_sent_str).replace(tzinfo=pytz.UTC)
            delta = (utc_time - time_sent_utc).total_seconds()
            # Treat epoch (0) or negative or unreasonably large as N/A
            if delta < 0 or delta > 86400 * 365:
                time_clicked_seconds_list.append(None)
            else:
                time_clicked_seconds_list.append(delta)
        except (ValueError, TypeError):
            time_clicked_seconds_list.append(None)
    
    # Per-name fastest time_clicked (only among valid times)
    fastest_per_name = {}
    for player, secs in zip(playerlist, time_clicked_seconds_list):
        name = player['name'].strip()
        if secs is not None:
            if name not in fastest_per_name or secs < fastest_per_name[name]:
                fastest_per_name[name] = secs
    
    formatted_list = ""
    for index, player in enumerate(playerlist, 1):
        utc_time = parse_time(player['time'])
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
        eastern_time = utc_time.astimezone(eastern_tz)
        
        time_sent = player['time_sent']
        if time_sent != "N/A":
            try:
                time_sent_parsed = parse_time(time_sent)
                time_sent_parsed = time_sent_parsed.replace(tzinfo=pytz.UTC)
                time_sent_eastern = time_sent_parsed.astimezone(eastern_tz)
                time_sent_str = time_sent_eastern.strftime('%Y-%m-%d %I:%M:%S %p %Z')
            except (ValueError, TypeError):
                time_sent_str = "N/A"
        else:
            time_sent_str = "N/A"
        
        time_clicked_secs = time_clicked_seconds_list[index - 1]
        if time_clicked_secs is not None:
            time_clicked_str = format_duration(time_clicked_secs)
        else:
            time_clicked_str = "N/A"
        
        name_key = player['name'].strip()
        is_personal_fastest = (
            time_clicked_secs is not None
            and name_key in fastest_per_name
            and abs(time_clicked_secs - fastest_per_name[name_key]) < 0.001
        )
        fastest_badge = ' <span style="background:#2ecc71;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.85em;">Personal fastest</span>' if is_personal_fastest else ''
        
        formatted_list += f"""
        <h2>Player {index}:{fastest_badge}</h2>
        <ul>
            <li><strong>Name:</strong> {player['name']}</li>
            <li><strong>Registration Time (ET):</strong> {eastern_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')}</li>
            <li><strong>Time Sent (ET):</strong> {time_sent_str}</li>
            <li><strong>Time Clicked:</strong> {time_clicked_str}</li>
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
    app.run()
