import os
import sys
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

if will_rain:
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body="Its going to rain today!,Remember to bring an ☂️",
        from_=whatsapp_from,
        to=whatsapp_to,
    )
    print(message.status)
else:
    print("No rain expected in this check — no message sent.")

