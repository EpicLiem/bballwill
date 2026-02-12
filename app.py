from flask import Flask
from flask import request
import datetime
import json
import os
import re

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playerlist.json")
playerlist = []


def load_playerlist():
    """Load playerlist from disk. Call at startup."""
    global playerlist
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                playerlist = json.load(f)
        except (json.JSONDecodeError, OSError):
            playerlist = []
    else:
        playerlist = []


def save_playerlist():
    """Write playerlist to disk. Call after any change."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(playerlist, f, indent=2)
    except OSError:
        pass  # log in production if desired


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


BOT_PATTERNS = [
    r"Googlebot",
    r"snippet",
    r"facebookexternalhit",
    r"GoogleMessages",
    r"Mozilla/5.0 \(X11; Ubuntu; Linux i686; rv:24.0\) Gecko/20100101 Firefox/24.0",
]


def is_bot(user_agent):
    """True if user_agent matches any known bot pattern."""
    if not user_agent:
        return False
    ua = str(user_agent)
    for pattern in BOT_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            return True
    return False


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
    if click_time_seconds < 0:
        congrats_line = f"You are an Earlybird! Your spot is guaranteed. You are now registered as {name}."
    elif click_time_seconds > 86400 * 365:
        congrats_line = f"You are now registered as {name}."
    else:
        congrats_line = f"Your click time was {format_duration(click_time_seconds)}. You are now registered as {name}."

    playerlist.append({
        "name": name,
        "time": str(ts),
        "time_sent": str(time_sent),
        "useragent": request.headers.get('User-Agent')
    })
    save_playerlist()
    
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
            save_playerlist()
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
            # Store raw delta (including negative) so we can always show a duration
            time_clicked_seconds_list.append(delta)
        except (ValueError, TypeError):
            time_clicked_seconds_list.append(None)
    
    # Per-name fastest time_clicked (lowest time wins; more negative = faster; exclude bots)
    fastest_per_name = {}
    for player, secs in zip(playerlist, time_clicked_seconds_list):
        if is_bot(player.get('useragent') or ''):
            continue
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
            if time_clicked_secs < 0:
                time_clicked_str = "-" + format_duration(abs(time_clicked_secs))
            elif time_clicked_secs <= 86400 * 365:
                time_clicked_str = format_duration(time_clicked_secs)
            else:
                time_clicked_str = "N/A (over 1 year)"
        else:
            time_clicked_str = "N/A"
        
        name_key = player['name'].strip()
        user_agent = player.get('useragent') or ''
        is_bot_entry = is_bot(user_agent)
        is_personal_fastest = (
            not is_bot_entry
            and time_clicked_secs is not None
            and name_key in fastest_per_name
            and abs(time_clicked_secs - fastest_per_name[name_key]) < 0.001
        )
        fastest_badge = ' <span style="background:#2ecc71;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.85em;">Personal fastest</span>' if is_personal_fastest else ''
        bot_badge = ' <span style="background:#e74c3c;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.85em;">Bot</span>' if is_bot_entry else ''
        
        formatted_list += f"""
        <h2>Click {index}:{fastest_badge}{bot_badge}</h2>
        <table>
            <tr><td class="key">Name</td><td>{player['name']}</td></tr>
            <tr><td class="key">Registration Time (ET)</td><td>{eastern_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')}</td></tr>
            <tr><td class="key">Time Sent (ET)</td><td>{time_sent_str}</td></tr>
            <tr><td class="key">Time Clicked</td><td>{time_clicked_str}</td></tr>
            <tr><td class="key">User Agent</td><td>{player.get('useragent', '')}</td></tr>
        </table>
        <hr>
        """
    
    unique_player_count = len(fastest_per_name)
    
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
                h2.count {{
                    color: #2ecc71;
                    text-align: center;
                    font-size: 1.5em;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 10px;
                }}
                td {{
                    padding: 6px 10px;
                    border-bottom: 1px solid #eee;
                    vertical-align: top;
                }}
                td.key {{
                    font-weight: bold;
                    width: 180px;
                    color: #555;
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
            <h2 class="count">{unique_player_count} unique player{"s" if unique_player_count != 1 else ""}</h2>
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
    save_playerlist()
    return "wiped list"


load_playerlist()

if __name__ == "__main__":
    app.run()
