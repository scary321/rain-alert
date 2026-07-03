import os
import json
import requests
from twilio.rest import Client

# ---- Secrets & config (never hardcode these — pulled from GitHub Secrets) ----
api_key = os.environ["OWM_API_KEY"]
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
whatsapp_from = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
whatsapp_to = os.environ["TWILIO_WHATSAPP_TO"]

lat = os.environ.get("LAT", "28.670185")
lon = os.environ.get("LON", "77.444550")

STATE_FILE = "state.json"
REMINDER_GAP_HOURS = 4   # send a reminder every N hourly checks while it keeps raining

omw_endpoint = "https://api.openweathermap.org/data/2.5/forecast"

weather_params = {
    "lat": lat,
    "lon": lon,
    "appid": api_key,
    "cnt": 4,
}

response = requests.get(omw_endpoint, params=weather_params)
response.raise_for_status()
weather_data = response.json()

will_rain = False
for hour_data in weather_data["list"]:
    condition_code = hour_data["weather"][0]["id"]
    if int(condition_code) < 700:
        will_rain = True

print(f"Checked forecast — rain expected: {will_rain}")

# ---- Load previous state ----
already_alerted = False
hours_since_alert = 0
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        try:
            state = json.load(f)
            already_alerted = state.get("already_alerted", False)
            hours_since_alert = state.get("hours_since_alert", 0)
        except json.JSONDecodeError:
            already_alerted = False
            hours_since_alert = 0


def send_alert(is_reminder):
    client = Client(account_sid, auth_token)
    body = (
        "🌧️ Still raining — remember your ☂️ if you're heading out!"
        if is_reminder
        else "Its going to rain today!,Remember to bring an ☂️"
    )
    message = client.messages.create(body=body, from_=whatsapp_from, to=whatsapp_to)
    print(f"{'Reminder' if is_reminder else 'Alert'} sent — {message.status}")


# ---- Decide whether to send ----
if will_rain:
    if not already_alerted:
        send_alert(is_reminder=False)
        already_alerted = True
        hours_since_alert = 0
    else:
        hours_since_alert += 1
        if hours_since_alert >= REMINDER_GAP_HOURS:
            send_alert(is_reminder=True)
            hours_since_alert = 0
        else:
            print(f"Still raining — next reminder in {REMINDER_GAP_HOURS - hours_since_alert} check(s).")
else:
    if already_alerted:
        print("Rain has stopped — re-arming for the next event.")
    already_alerted = False
    hours_since_alert = 0

# ---- Save state back for the next run ----
with open(STATE_FILE, "w") as f:
    json.dump({"already_alerted": already_alerted, "hours_since_alert": hours_since_alert}, f)
