import json
import os
import platform
import signal
import sys
import threading
import time
from datetime import datetime

from dotenv import load_dotenv
from kafka import KafkaProducer
from log4py import Logger
from models import SensorUpdate
from sensors import BME280, PM1006

Logger.set_level("DEBUG")

APP_VERSION = "0.1.0"
MOCK_PROBE_ID = "TH-10-0001"

exit_flag = False


def exit_handler(sig, frame):
    global exit_flag
    exit_flag = True
    log.info("Send exit signal to threads")
    sys.exit(0)


def get_boolean_from_string(value: str):
    value_capitalize = value.lower().capitalize()
    if value_capitalize in ["True", "False"]:
        return value_capitalize == "True"
    else:
        raise ValueError(f"Invalid value: {value}")


def send_message(message: dict, header_type: str):
    log.info(f"Sending message: {message}")
    producer.send(
        topic=KAFKA_PRODUCER_TOPIC,
        key=bytes("data", "utf-8"),
        value=message,
        headers=[("__TypeId__", bytes(header_type, "utf-8"))],
    )
    producer.flush()


def weather_sensor_loop():
    log.info("Starting weather sensor loop")
    bme280 = BME280()

    previous_temperature = None
    previous_humidity = None
    previous_pressure = None

    while not exit_flag:
        current_datetime = datetime.now().astimezone()
        temperature = bme280.get_temperature()
        humidity = bme280.get_humidity()
        pressure = bme280.get_pressure()

        if (
            temperature is not None
            and previous_temperature != temperature
            and ENABLE_TEMPERATURE
        ):
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                probe_id=MOCK_PROBE_ID,
                type="temperature",
                value=temperature,
                time_of_event=current_datetime.isoformat(),
                device=DEVICE_NAME,
                manufacturer=DEVICE_MANUFACTURER,
                platform=platform.platform(),
                app_version=APP_VERSION,
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_temperature = temperature

        if humidity is not None and previous_humidity != humidity and ENABLE_HUMIDITY:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                probe_id=MOCK_PROBE_ID,
                type="humidity",
                value=humidity,
                time_of_event=current_datetime.isoformat(),
                device=DEVICE_NAME,
                manufacturer=DEVICE_MANUFACTURER,
                platform=platform.platform(),
                app_version=APP_VERSION,
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_humidity = humidity

        if pressure is not None and previous_pressure != pressure and ENABLE_PRESSURE:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                probe_id=MOCK_PROBE_ID,
                type="pressure",
                value=pressure,
                time_of_event=current_datetime.isoformat(),
                device=DEVICE_NAME,
                manufacturer=DEVICE_MANUFACTURER,
                platform=platform.platform(),
                app_version=APP_VERSION,
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_pressure = pressure

        time.sleep(SCRAP_INTERVAL)


def particle_sensor_loop():
    log.info("Starting particle sensor loop")
    pm1006 = PM1006()

    previous_pm25 = None
    while not exit_flag:
        current_datetime = datetime.now().astimezone()
        pm1006.open_connection()
        sensor_msg, pm25 = pm1006.get_pm25()
        log.debug(f"sensor_msg: {sensor_msg}")
        if pm25 is not None and previous_pm25 != pm25 and ENABLE_PM25:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "pm1006",
                probe_id=MOCK_PROBE_ID,
                type="pm25",
                value=pm25,
                time_of_event=current_datetime.isoformat(),
                device=DEVICE_NAME,
                manufacturer=DEVICE_MANUFACTURER,
                platform=platform.platform(),
                app_version=APP_VERSION,
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_pm25 = pm25

        pm1006.close_connection()
        time.sleep(SCRAP_INTERVAL)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)

    config = {
        "handlers": {
            "stream_handler": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file_handler": {
                "class": "logging.FileHandler",
                "filename": "weather-station.log",
            },
        },
        "loggers": {
            "__main__": {
                "level": "INFO",
                "handlers": ["stream_handler", "file_handler"],
                "propagate": False,
            }
        },
    }
    Logger.configure(**config)
    log = Logger.get_logger(__name__)

    splash = """
$$\      $$\                      $$\     $$\\
$$ | $\  $$ |                     $$ |    $$ |
$$ |$$$\ $$ | $$$$$$\   $$$$$$\ $$$$$$\   $$$$$$$\   $$$$$$\   $$$$$$\\
$$ $$ $$\$$ |$$  __$$\  \____$$\\\\_$$  _|  $$  __$$\ $$  __$$\ $$  __$$\\
$$$$  _$$$$ |$$$$$$$$ | $$$$$$$ | $$ |    $$ |  $$ |$$$$$$$$ |$$ |  \__|
$$$  / \$$$ |$$   ____|$$  __$$ | $$ |$$\ $$ |  $$ |$$   ____|$$ |
$$  /   \$$ |\$$$$$$$\ \$$$$$$$ | \$$$$  |$$ |  $$ |\$$$$$$$\ $$ |
\__/     \__| \_______| \_______|  \____/ \__|  \__| \_______|\__|
:: Weather Gateway ::                                (v{version})
    """.format(
        version=APP_VERSION
    )
    print(splash)
    log.info("Loading .env file")
    load_dotenv()

    try:
        DEVICE_NAME = os.getenv("DEVICE_NAME")
        DEVICE_MANUFACTURER = os.getenv("DEVICE_MANUFACTURER")
        KAFKA_PRODUCER_BOOTSTRAP_SERVERS = os.getenv("KAFKA_PRODUCER_BOOTSTRAP_SERVERS")
        KAFKA_PRODUCER_TOPIC = os.getenv("KAFKA_PRODUCER_TOPIC")
        KAFKA_PRODUCER_SOURCE_NAME = os.getenv("KAFKA_PRODUCER_SOURCE_NAME")
        SCRAP_INTERVAL = int(os.getenv("SCRAP_INTERVAL"))
        ENABLE_TEMPERATURE = get_boolean_from_string(os.getenv("ENABLE_TEMPERATURE"))
        ENABLE_HUMIDITY = get_boolean_from_string(os.getenv("ENABLE_HUMIDITY"))
        ENABLE_PRESSURE = get_boolean_from_string(os.getenv("ENABLE_PRESSURE"))
        ENABLE_PM25 = get_boolean_from_string(os.getenv("ENABLE_PM25"))
    except Exception as e:
        log.error(f"Cannot parse .env file: {e}")
        raise

    config_msg = "Application Configuration:\n"
    config_msg += " app_version             %s\n" % APP_VERSION
    config_msg += " device_name             %s\n" % DEVICE_NAME
    config_msg += " device_manufacturer     %s\n" % DEVICE_MANUFACTURER
    config_msg += " device_platform         %s\n" % platform.platform()
    config_msg += " kafka_bootstrap_server  %s\n" % KAFKA_PRODUCER_BOOTSTRAP_SERVERS
    config_msg += " kafka_topic             %s\n" % KAFKA_PRODUCER_TOPIC
    config_msg += " kafka_source_name       %s\n" % KAFKA_PRODUCER_SOURCE_NAME
    config_msg += " enabled_temperature     %s\n" % ENABLE_TEMPERATURE
    config_msg += " enabled_humidity        %s\n" % ENABLE_HUMIDITY
    config_msg += " enabled_pressure        %s\n" % ENABLE_PRESSURE
    config_msg += " enabled_pm25:           %s\n" % ENABLE_PM25

    log.info(config_msg)

    try:
        log.info("Connecting to kafka")
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_PRODUCER_BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )
        log.info("Connected to kafka")

    except Exception as e:
        log.error(f"Cannot connect to Kafka: {e}")
        raise

    try:
        thread_1 = threading.Thread(target=weather_sensor_loop)
        thread_2 = threading.Thread(target=particle_sensor_loop)

        # Start the threads
        log.info("Starting sensor threads")
        thread_1.start()
        thread_2.start()
        # Keep the main thread alive to handle Ctrl+C
        while True:
            time.sleep(1)
    except Exception as e:
        log.error(e)
        raise
