# bme680-mqtt
Read a bme680 sensor and post to MQTT server

## Configuration

The application can be configured using environment variables. For local development, you can create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
# Edit .env with your MQTT broker settings
```

### Environment Variables

- `MQTT_HOST`: MQTT broker hostname or IP address (default: `localhost`)
- `MQTT_PORT`: MQTT broker port (default: `1883`)
- `MQTT_TOPIC_BASE`: Base topic for sensor data (default: `sensors/bme680`)
- `SENSOR_READ_INTERVAL`: Sensor read interval in seconds (default: `10`)

### Example .env file

```
MQTT_HOST=192.168.1.100
MQTT_PORT=1883
MQTT_TOPIC_BASE=sensors/bme680
SENSOR_READ_INTERVAL=10
```

## Installation

The application requires the following Python packages:
- `paho-mqtt`: MQTT client library
- `bme680`: BME680 sensor library
- `python-dotenv`: (Optional) For .env file support

Install dependencies:
```bash
pip install paho-mqtt bme680 python-dotenv
```

Note: `python-dotenv` is optional. If not installed, the application will still work using system environment variables.

## Usage

```bash
python3 main.py
```

The application will:
1. Read sensor data from the BME680 sensor at the configured interval (default: every 10 seconds)
2. Publish temperature, pressure, and humidity readings to the configured MQTT broker
3. Each reading is published to `{MQTT_TOPIC_BASE}/{sensor_type}` with a JSON payload
