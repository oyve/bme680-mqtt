#!/usr/bin/env python3

import os
import time
import json
import paho.mqtt.client as mqtt
import bme680

# Load configuration from environment variables
# For local development, create a .env file based on .env.example
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables only
    pass

# MQTT broker settings from environment variables with defaults
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "sensors/bme680")

# Initialize BME680 sensor
sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

# Configure oversampling and filtering
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)

# Connect to MQTT broker
client = mqtt.Client()
client.connect(MQTT_HOST, MQTT_PORT, 60)

def publish_reading(path, value, unit):
    payload = {
        "path": path,
        "value": round(value, 2),
        "unit": unit
    }
    topic = f"{MQTT_TOPIC_BASE}/{path}"
    client.publish(topic, json.dumps(payload))
    #print(f"Published to {topic}: {payload}")

try:
    while True:
        if sensor.get_sensor_data():
            publish_reading("temperature", sensor.data.temperature, "C")
            publish_reading("pressure", sensor.data.pressure, "hPa")
            publish_reading("humidity", sensor.data.humidity, "%")
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopped by user.")
    client.disconnect()


