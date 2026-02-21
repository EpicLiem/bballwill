from flask import Flask, request, redirect
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
    r"github\.com",
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
    registered_line = f"You are now registered as {name}."
    clean_name = name.strip()

    # Count unique non-bot players (always shown, including earlybirds)
    unique_clickers = set()
    for p in playerlist:
        if not is_bot(p.get('useragent') or ''):
            unique_clickers.add(p['name'].strip())
    if clean_name not in unique_clickers:
        unique_clickers.add(clean_name)
    count_line = f"{len(unique_clickers)} player{'s have' if len(unique_clickers) != 1 else ' has'} clicked."

    # Find this player's all-time best (lowest) click time, including negative (earlybird)
    personal_best = None
    for p in playerlist:
        if p['name'].strip() == clean_name and not is_bot(p.get('useragent') or ''):
            try:
                p_time = datetime.datetime.strptime(p['time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                p_sent = datetime.datetime.strptime(p['time_sent'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                p_secs = (p_time - p_sent).total_seconds()
                if personal_best is None or p_secs < personal_best:
                    personal_best = p_secs
            except (ValueError, TypeError):
                pass
    # Include current click
    if personal_best is None or click_time_seconds < personal_best:
        personal_best = click_time_seconds

    # Player is an earlybird if their best-ever click time is negative
    is_earlybird = personal_best is not None and personal_best < 0

    congrats_line = ""
    fastest_line = ""
    if is_earlybird:
        congrats_line = "You are an Earlybird! Your spot is guaranteed."
        if click_time_seconds >= 0 and click_time_seconds <= 86400 * 365:
            congrats_line += f" This click time was {format_duration(click_time_seconds)}."
    elif click_time_seconds > 86400 * 365:
        pass
    else:
        congrats_line = f"This click time was {format_duration(click_time_seconds)}."
        # Only show fastest for non-earlybird, non-negative best times
        personal_fastest_positive = None
        for p in playerlist:
            if p['name'].strip() == clean_name and not is_bot(p.get('useragent') or ''):
                try:
                    p_time = datetime.datetime.strptime(p['time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    p_sent = datetime.datetime.strptime(p['time_sent'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    p_secs = (p_time - p_sent).total_seconds()
                    if p_secs >= 0 and (personal_fastest_positive is None or p_secs < personal_fastest_positive):
                        personal_fastest_positive = p_secs
                except (ValueError, TypeError):
                    pass
        if personal_fastest_positive is None or click_time_seconds < personal_fastest_positive:
            personal_fastest_positive = click_time_seconds
        if click_time_seconds <= 86400 * 365:
            fastest_line = f"Your fastest click time was {format_duration(personal_fastest_positive)}."

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
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    background-color: #1e1e1e;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }}
                .fastest {{
                    background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    padding: 20px 40px;
                    border-radius: 15px;
                    display: inline-block;
                    margin: 20px 0;
                }}
                .click-time {{
                    color: #bbb;
                    font-size: 20px;
                    margin: 8px 0;
                }}
                .info {{
                    color: #bbb;
                    font-size: 18px;
                    margin: 8px 0;
                }}
                .registered {{
                    color: #2ecc71;
                    font-size: 24px;
                    margin: 15px 0;
                }}
                .step {{
                    color: #888;
                    font-size: 18px;
                    margin: 30px 0 10px 0;
                }}
                .step-done {{
                    color: #2ecc71;
                }}
                .pay-prompt {{
                    color: white;
                    font-size: 22px;
                    margin: 10px 0 25px 0;
                }}
                .buttons {{
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                    max-width: 300px;
                    margin: 0 auto;
                }}
                .pay-btn {{
                    display: block;
                    padding: 18px 30px;
                    font-size: 20px;
                    font-weight: bold;
                    color: white;
                    text-decoration: none;
                    border-radius: 12px;
                }}
                .venmo {{ background: #008CFF; }}
                .cashapp {{ background: #00D632; }}
                .paypal {{ background: #003087; }}
                .applepay {{ background: #333; }}
            </style>
        </head>
        <body>
            <div class="registered">{registered_line}</div>

            {"<div class='fastest'>" + fastest_line + "</div>" if fastest_line else ""}
            {"<div class='click-time'>" + congrats_line + "</div>" if congrats_line else ""}
            <div class="info">{count_line}</div>

            <div class="step"><span class="step-done">Step 1: Registered ✓</span></div>
            <div class="step">Step 2: Pay $13.50</div>
            <div class="pay-prompt">Pay now to save your spot</div>

            <div class="buttons">
                <a href="https://venmo.com/u/will_luttrell" target="_blank" class="pay-btn venmo">Venmo</a>
                <a href="https://cash.app/$luttrellwill" target="_blank" class="pay-btn cashapp">Cash App</a>
                <a href="https://www.paypal.com/paypalme/paywillnowplease" target="_blank" class="pay-btn paypal">PayPal</a>
                <a href="sms:+12014460400" target="_blank" class="pay-btn applepay">Apple Pay</a>
            </div>
        </body>
    </html>
    """


@app.route("/will/remove/<int:click_number>", methods=['GET', 'POST'])
def remove_by_click(click_number):
    if click_number < 1 or click_number > len(playerlist):
        return f"<h1>Invalid click number. Must be 1-{len(playerlist)}</h1>"
    
    player = playerlist[click_number - 1]
    
    if request.method == 'GET':
        # Show confirmation form
        return f"""
        <html>
            <head><title>Confirm Removal</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
                <h1>Remove Click {click_number}?</h1>
                <h2>{player['name']}</h2>
                <form method="POST">
                    <button type="submit" style="background: #e74c3c; color: white; padding: 15px 30px; font-size: 18px; border: none; cursor: pointer; margin: 10px;">
                        Yes, Remove
                    </button>
                </form>
                <a href="/will/pretty" style="display: inline-block; padding: 15px 30px; font-size: 18px; margin: 10px;">Cancel</a>
            </body>
        </html>
        """
    
    # POST - actually remove, then redirect to prevent re-POST on refresh
    removed = playerlist.pop(click_number - 1)
    save_playerlist()
    return redirect(f"/will/pretty?removed={removed['name']}")

@app.route("/will/list")
def show_list():
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
    
    # Build sorted leaderboard table (fastest to slowest)
    sorted_players = sorted(fastest_per_name.items(), key=lambda x: x[1])
    leaderboard_rows = ""
    for rank, (name, secs) in enumerate(sorted_players, 1):
        if secs < 0:
            time_str = "-" + format_duration(abs(secs))
        elif secs <= 86400 * 365:
            time_str = format_duration(secs)
        else:
            time_str = "N/A"
        leaderboard_rows += f"<tr><td>{rank}</td><td>{name}</td><td>{time_str}</td></tr>\n"
    
    # Combine playerlist with time_clicked_seconds and original index, then reverse for newest first
    combined = list(zip(playerlist, time_clicked_seconds_list, range(1, len(playerlist) + 1)))
    combined.reverse()
    
    formatted_list = ""
    for player, time_clicked_secs, index in combined:
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
                .leaderboard {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 30px;
                }}
                .leaderboard h2 {{
                    margin-top: 0;
                    color: #333;
                }}
                .leaderboard table {{
                    width: 100%;
                }}
                .leaderboard th {{
                    text-align: left;
                    padding: 8px 10px;
                    border-bottom: 2px solid #ddd;
                    color: #555;
                }}
                .leaderboard td {{
                    padding: 8px 10px;
                    border-bottom: 1px solid #eee;
                }}
                .activity-log {{
                    margin-top: 30px;
                    border-top: 2px solid #333;
                    padding-top: 20px;
                }}
                hr {{
                    border: 0;
                    border-top: 1px solid #ddd;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            {"<h2 style='color:#e74c3c;text-align:center;'>Removed: " + request.args.get('removed') + "</h2>" if request.args.get('removed') else ""}
            <h1>Registered Players</h1>
            <h2 class="count">{unique_player_count} unique player{"s" if unique_player_count != 1 else ""}</h2>
            
            <div class="leaderboard">
                <h2>Leaderboard (Fastest Click Times)</h2>
                <table>
                    <thead>
                        <tr><th>#</th><th>Name</th><th>Click Time</th></tr>
                    </thead>
                    <tbody>
                        {leaderboard_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="activity-log">
                <h2>Activity Log</h2>
                {formatted_list}
            </div>
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
