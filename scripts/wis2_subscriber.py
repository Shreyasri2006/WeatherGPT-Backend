"""Optional WIS2/MQTT subscriber scaffold.

Install first:
    pip install -r requirements-wis2.txt

Then configure WIS2_BROKER, WIS2_PORT and WIS2_TOPIC in .env.
This scaffold logs incoming notifications only. Your SIH team should add a
proper parser/persistence layer after selecting the WIS2 collections you use.
"""

import json
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()
BROKER = os.getenv("WIS2_BROKER", "")
PORT = int(os.getenv("WIS2_PORT", "8883"))
TOPIC = os.getenv("WIS2_TOPIC", "")

if not BROKER or not TOPIC:
    raise SystemExit("Set WIS2_BROKER and WIS2_TOPIC in .env before running this worker.")


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected:", reason_code)
    client.subscribe(TOPIC)


def on_message(client, userdata, message):
    text = message.payload.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
        print(json.dumps(payload, indent=2)[:5000])
    except json.JSONDecodeError:
        print(text[:5000])


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.tls_set()
client.connect(BROKER, PORT)
client.loop_forever()
