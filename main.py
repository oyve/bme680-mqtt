#!/usr/bin/env python3

import os
import time
import json
import logging
import paho.mqtt.client as mqtt
import bme680

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

# Connection retry settings
MAX_RETRY_DELAY = 300  # Maximum delay of 5 minutes
INITIAL_RETRY_DELAY = 1  # Start with 1 second
retry_delay = INITIAL_RETRY_DELAY
mqtt_connected = False

# Initialize BME680 sensor
sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

# Configure oversampling and filtering
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    global mqtt_connected, retry_delay
    if rc == 0:
        logging.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        mqtt_connected = True
        retry_delay = INITIAL_RETRY_DELAY  # Reset retry delay on successful connection
    else:
        logging.error(f"Failed to connect to MQTT broker, return code: {rc}")
        mqtt_connected = False

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        logging.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")
    else:
        logging.info("Disconnected from MQTT broker")

# Connect to MQTT broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect

def connect_mqtt():
    """Attempt to connect to MQTT broker with exponential backoff"""
    global retry_delay
    
    while not mqtt_connected:
        try:
            logging.info(f"Attempting to connect to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_start()  # Start network loop in background thread
            
            # Wait a bit to see if connection succeeds
            time.sleep(2)
            
            if mqtt_connected:
                break
            else:
                raise ConnectionError("Connection callback not received")
                
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {e}")
            logging.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
            # Exponential backoff with maximum limit
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

# Initial connection
connect_mqtt()

def publish_reading(path, value, unit):
    """Publish sensor reading to MQTT broker"""
    if not mqtt_connected:
        logging.warning("Not connected to MQTT broker, skipping publish")
        return
        
    payload = {
        "path": path,
        "value": round(value, 2),
        "unit": unit
    }
    topic = f"{MQTT_TOPIC_BASE}/{path}"
    try:
        client.publish(topic, json.dumps(payload))
    except Exception as e:
        logging.error(f"Failed to publish to {topic}: {e}")

try:
    while True:
        # Check if we're connected, if not, attempt to reconnect
        if not mqtt_connected:
            logging.warning("Lost connection to MQTT broker, attempting to reconnect...")
            connect_mqtt()
        
        if sensor.get_sensor_data():
            publish_reading("temperature", sensor.data.temperature, "C")
            publish_reading("pressure", sensor.data.pressure, "hPa")
            publish_reading("humidity", sensor.data.humidity, "%")
        time.sleep(10)
except KeyboardInterrupt:
    logging.info("Stopped by user")
    client.loop_stop()
    client.disconnect()


