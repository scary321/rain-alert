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

# ---- Load previous alert state ----
already_alerted = False
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        try:
            state = json.load(f)
            already_alerted = state.get("already_alerted", False)
        except json.JSONDecodeError:
            already_alerted = False

# ---- Decide whether to send ----
if will_rain and not already_alerted:
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body="Its going to rain today!,Remember to bring an ☂️",
        from_=whatsapp_from,
        to=whatsapp_to,
    )
    print(f"Alert sent — {message.status}")
    already_alerted = True
elif will_rain and already_alerted:
    print("Rain continues, but already alerted this cycle — staying quiet.")
else:
    if already_alerted:
        print("Rain has stopped — re-arming for the next event.")
    already_alerted = False

# ---- Save state back for the next run ----
with open(STATE_FILE, "w") as f:
    json.dump({"already_alerted": already_alerted}, f)

