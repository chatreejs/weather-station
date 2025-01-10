import json
import os
import platform
import re
import time
from datetime import datetime

from autopylogger import init_logging
from dotenv import load_dotenv
from kafka import KafkaProducer
from lora import LoRaReceiver
from models import SensorUpdate

APP_VERSION = "0.1.0"


def get_boolean_from_string(value: str):
    value_capitalize = value.lower().capitalize()
    if value_capitalize in ["True", "False"]:
        return value_capitalize == "True"
    else:
        raise ValueError(f"Invalid value: {value}")


def send_message(message: dict, header_type: str):
    logger.debug(f"Sending message: {message}")
    producer.send(
        topic=KAFKA_PRODUCER_TOPIC,
        key=bytes("data", "utf-8"),
        value=message,
        headers=[("__TypeId__", bytes(header_type, "utf-8"))],
    )
    producer.flush()


def validate_lora_message(message: str):
    if message is None:
        return False, "Message is None"
    message = message.split("|")
    if len(message) != 3:
        return False, "Message does not have 3 parts"
    try:
        float(message[2])
    except ValueError:
        return False, "Cannot parse value as float"

    if re.match(r"^[A-Z]{2}-[0-9]{2}-[0-9]{4}$", message[0]) is None:
        return False, "Invalid probe ID format"
    return True, None


def main():
    logger.info("Starting weather sensor loop")
    lora.start()

    previous_temperature = None
    previous_humidity = None
    # previous_pressure = None
    previous_pm25 = None

    while True:
        if lora.received_message:
            logger.info(
                f"Received message from probe: '{lora.received_message}', RSSI: {lora.get_rssi_value()} dBm"
            )
            is_valid, error = validate_lora_message(lora.received_message)
            if is_valid is False:
                logger.error("Invalid message format: %s", error)
                lora.received_message = None
                continue
            message = lora.received_message.split("|")
            lora.received_message = None

            current_datetime = datetime.now().astimezone()
            probe_id = message[0]
            sensor_type = message[1]
            value = float(message[2])

            if sensor_type == "PM25" and previous_pm25 != value and ENABLE_PM25:
                sensor_data = SensorUpdate(
                    source=KAFKA_PRODUCER_SOURCE_NAME + "." + "pm1006",
                    probe_id=probe_id,
                    type="pm25",
                    value=value,
                    time_of_event=current_datetime.isoformat(),
                    device=DEVICE_NAME,
                    manufacturer=DEVICE_MANUFACTURER,
                    platform=platform.platform(),
                    app_version=APP_VERSION,
                )
                message = sensor_data.to_dict()
                send_message(message, "SensorUpdate")
                previous_pm25 = value

            if (
                sensor_type == "TEMP"
                and previous_temperature != value
                and ENABLE_TEMPERATURE
            ):
                sensor_data = SensorUpdate(
                    source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                    probe_id=probe_id,
                    type="temperature",
                    value=value,
                    time_of_event=current_datetime.isoformat(),
                    device=DEVICE_NAME,
                    manufacturer=DEVICE_MANUFACTURER,
                    platform=platform.platform(),
                    app_version=APP_VERSION,
                )
                message = sensor_data.to_dict()
                send_message(message, "SensorUpdate")
                previous_temperature = value

            if sensor_type == "HUMI" and previous_humidity != value and ENABLE_HUMIDITY:
                sensor_data = SensorUpdate(
                    source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                    probe_id=probe_id,
                    type="humidity",
                    value=value,
                    time_of_event=current_datetime.isoformat(),
                    device=DEVICE_NAME,
                    manufacturer=DEVICE_MANUFACTURER,
                    platform=platform.platform(),
                    app_version=APP_VERSION,
                )
                message = sensor_data.to_dict()
                send_message(message, "SensorUpdate")
                previous_humidity = value

        time.sleep(1)


if __name__ == "__main__":
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
        ENABLE_TEMPERATURE = get_boolean_from_string(os.getenv("ENABLE_TEMPERATURE"))
        ENABLE_HUMIDITY = get_boolean_from_string(os.getenv("ENABLE_HUMIDITY"))
        ENABLE_PRESSURE = get_boolean_from_string(os.getenv("ENABLE_PRESSURE"))
        ENABLE_PM25 = get_boolean_from_string(os.getenv("ENABLE_PM25"))
    except Exception as e:
        logger.error(f"Cannot parse .env file: {e}")
        raise

    config_msg = "Application Configuration:\n"
    config_msg += " device_name         %s\n" % DEVICE_NAME
    config_msg += " device_manufacturer %s\n" % DEVICE_MANUFACTURER
    config_msg += " device_platform     %s\n" % platform.platform()
    config_msg += " topic               %s\n" % KAFKA_PRODUCER_TOPIC
    config_msg += " source_name         %s\n" % KAFKA_PRODUCER_SOURCE_NAME
    config_msg += " enabled_temperature %s\n" % ENABLE_TEMPERATURE
    config_msg += " enabled_humidity    %s\n" % ENABLE_HUMIDITY
    config_msg += " enabled_pressure    %s\n" % ENABLE_PRESSURE
    config_msg += " enabled_pm25:       %s\n" % ENABLE_PM25

    logger.info(config_msg)

    try:
        logger.info("Initializing LoRa Gateway")
        lora = LoRaReceiver(verbose=False)
        if lora.get_mode() != 0x80 and lora.get_mode() != 0x81:
            raise Exception("LoRa is not in SLEEP or STDBY mode. Check wiring")
        logger.info(lora)
    except Exception as e:
        logger.error(f"Cannot initialize LoRa: {e}")
        raise

    try:
        logger.info("Connecting to Kafka")
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_PRODUCER_BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )
        logger.info("Connected to Kafka")

    except Exception as e:
        logger.error(f"Cannot connect to Kafka: {e}")
        raise

    try:
        logger.info("Starting main threads")
        main()
    except Exception as e:
        logger.error(e)
        raise
    finally:
        lora.teardown()
