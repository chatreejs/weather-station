import json
import os
import platform
import signal
import sys
import time

from autopylogger import init_logging
from datetime import datetime
from dotenv import load_dotenv
from kafka import KafkaProducer
from models import SensorUpdate
from lora import LoRaReceiver

APP_VERSION = "0.1.0"
MOCK_PROBE_ID = "TH-10-0001"


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


def main():
    logger.info("Listening for LoRa messages...")
    lora.start()
    while True:
        if lora.received_message:
            logger.info(lora.received_message)
            lora.received_message = None
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

    config_msg = f"""Application Configuration
    -- metadata --
    device_name: {DEVICE_NAME}
    device_manufacturer: {DEVICE_MANUFACTURER}

    -- kafka producer --
    topic: {KAFKA_PRODUCER_TOPIC}
    source_name: {KAFKA_PRODUCER_SOURCE_NAME}
        
    -- sensors --
    enable_temperature: {ENABLE_TEMPERATURE}
    enable_humidity: {ENABLE_HUMIDITY}
    enable_pressure: {ENABLE_PRESSURE}
    enable_pm25: {ENABLE_PM25}
    """

    logger.info(config_msg)

    try:
        logger.info("Initializing lora")
        lora = LoRaReceiver(verbose=True)
        lora.set_pa_config(pa_select=1)
        logger.info(lora)
    except Exception as e:
        logger.error(f"Cannot initialize LoRa: {e}")
        raise

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
        logger.info("Starting main threads")
        main()
    except Exception as e:
        logger.error(e)
        raise
    finally:
        lora.teardown()
