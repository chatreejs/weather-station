import json
import os
import platform
import signal
import sys
import threading
import time
from datetime import datetime

from autopylogger import init_logging
from dotenv import load_dotenv
from kafka import KafkaProducer
from models import SensorUpdate
from sensors import BME280, PM1006

APP_VERSION = "0.1.0"
MOCK_PROBE_ID = "TH-10-0001"

exit_flag = False


def exit_handler(sig, frame):
    global exit_flag
    exit_flag = True
    logger.info("Send exit signal to threads")
    sys.exit(0)


def get_boolean_from_string(value: str):
    value_capitalize = value.lower().capitalize()
    if value_capitalize in ["True", "False"]:
        return value_capitalize == "True"
    else:
        raise ValueError(f"Invalid value: {value}")


def send_message(message: dict, header_type: str):
    logger.info(f"Sending message: {message}")
    producer.send(
        topic=KAFKA_PRODUCER_TOPIC,
        key=bytes("data", "utf-8"),
        value=message,
        headers=[("__TypeId__", bytes(header_type, "utf-8"))],
    )
    producer.flush()


def weather_sensor_loop():
    logger.info("Starting weather sensor loop")
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
    logger.info("Starting particle sensor loop")
    pm1006 = PM1006()

    previous_pm25 = None
    while not exit_flag:
        current_datetime = datetime.now().astimezone()
        pm1006.open_connection()
        sensor_msg, pm25 = pm1006.get_pm25()
        logger.debug(f"sensor_msg: {sensor_msg}")
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

    log_format = "%(asctime)s %(levelname)s - [%(filename)s] %(funcName)s: %(message)s"
    logger = init_logging(
        log_directory="logs",
        log_name="weather-station",
        log_format=log_format,
        log_level="DEBUG",
        rotation_criteria="time",
        rotate_when="d",
        rotate_interval=1,
    )

    logger.info("Starting Weather Station Application v%s", APP_VERSION)
    logger.info("Loading .env file")
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
        logger.error(f"Cannot parse .env file: {e}")
        raise

    config_msg = f"""configuration
        -- metadata --
        device_name: {DEVICE_NAME}
        device_manufacturer: {DEVICE_MANUFACTURER}

        -- kafka producer --
        topic: {KAFKA_PRODUCER_TOPIC}
        source_name: {KAFKA_PRODUCER_SOURCE_NAME}
        
        -- sensors --
        scrap_interval: {SCRAP_INTERVAL}
        enable_temperature: {ENABLE_TEMPERATURE}
        enable_humidity: {ENABLE_HUMIDITY}
        enable_pressure: {ENABLE_PRESSURE}
        enable_pm25: {ENABLE_PM25}
    """

    logger.info(config_msg)

    try:
        logger.info("Connecting to kafka")
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_PRODUCER_BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )
        logger.info("Connected to kafka")

    except Exception as e:
        logger.error(f"Cannot connect to Kafka: {e}")
        raise

    try:
        thread_1 = threading.Thread(target=weather_sensor_loop)
        thread_2 = threading.Thread(target=particle_sensor_loop)

        # Start the threads
        logger.info("Starting sensor threads")
        thread_1.start()
        thread_2.start()
        # Keep the main thread alive to handle Ctrl+C
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(e)
        raise
