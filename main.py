import os
import json
import time
import threading
import signal
import sys

from autopylogger import init_logging
from dotenv import load_dotenv
from datetime import datetime
from models import SensorUpdate
from kafka import KafkaProducer
from sensors import BME280, PM1006K


exit_flag = False


def exit_handler(sig, frame):
    global exit_flag
    exit_flag = True
    logger.info("exiting ...")
    sys.exit(0)


def get_boolean_from_string(value: str):
    value_capitalize = value.lower().capitalize()
    if value_capitalize in ["True", "False"]:
        return value_capitalize == "True"
    else:
        raise Exception(f"invalid value: {value}")


def send_message(message: dict, header_type: str):
    logger.info(f"sending message: {message}")
    producer.send(
            topic=KAFKA_PRODUCER_TOPIC,
            key=bytes('data', 'utf-8'),
            value=message,
            headers=[("__TypeId__", bytes(header_type, "utf-8"))]
    )
    producer.flush()


def weather_sensor_loop():
    bme280 = BME280()

    previous_temperature = None
    previous_humidity = None
    previous_pressure = None

    while not exit_flag:
        current_datetime = datetime.now().astimezone()
        temperature = bme280.get_temperature()
        humidity = bme280.get_humidity()
        pressure = bme280.get_pressure()

        if temperature is not None and previous_temperature != temperature and ENABLE_TEMPURATURE:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                type="temperature",
                value=temperature,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_temperature = temperature
        
        if humidity is not None and previous_humidity != humidity and ENABLE_HUMIDITY:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                type="humidity",
                value=humidity,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_humidity = humidity
        
        if pressure is not None and previous_pressure != pressure and ENABLE_PRESSURE:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                type="pressure",
                value=pressure,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_pressure = pressure

        time.sleep(5)
    pass


def particle_sensor_loop():
    pm1006k = PM1006K()

    previous_pm25 = None
    while not exit_flag:
        current_datetime = datetime.now().astimezone()
        raw, pm25 = pm1006k.get_pm25()
        logger.debug(f"raw value: {raw}")
        # logger.debug(f"D3 = {raw[5]}, D4 = {raw[6]}")
        if pm25 is not None and previous_pm25 != pm25 and ENABLE_PM25:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "pm1006k",
                type="pm25",
                value=pm25,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_pm25 = pm25

        # fixed delay to UART buffer
        time.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)

    log_format = "%(asctime)s %(levelname)s - [%(filename)s] %(funcName)s: %(message)s"
    logger = init_logging(log_directory="logs",
                      log_name="weather-station",
                      log_format=log_format,
                      log_level="DEBUG",
                      rotation_criteria="time",
                      rotate_when="d",
                      rotate_interval=1
        )

    logger.info("starting weather-station")
    logger.info("loading env file")
    load_dotenv()

    try:
        KAFKA_PRODUCER_BOOTSTRAP_SERVERS=os.getenv("KAFKA_PRODUCER_BOOTSTRAP_SERVERS")
        KAFKA_PRODUCER_TOPIC=os.getenv("KAFKA_PRODUCER_TOPIC")
        KAFKA_PRODUCER_SOURCE_NAME=os.getenv("KAFKA_PRODUCER_SOURCE_NAME")
        ENABLE_TEMPURATURE=get_boolean_from_string(os.getenv("ENABLE_TEMPURATURE"))
        ENABLE_HUMIDITY=get_boolean_from_string(os.getenv("ENABLE_HUMIDITY"))
        ENABLE_PRESSURE=get_boolean_from_string(os.getenv("ENABLE_PRESSURE"))
        ENABLE_PM25=get_boolean_from_string(os.getenv("ENABLE_PM25"))
    except Exception as e:
        logger.error(f"cannot parse .env: {e}")
        sys.exit(1)

    config_msg = f"""configuration
        topic: {KAFKA_PRODUCER_TOPIC}
        source_name: {KAFKA_PRODUCER_SOURCE_NAME}

        enable_tempurature: {ENABLE_TEMPURATURE}
        enable_humidity: {ENABLE_HUMIDITY}
        enable_pressure: {ENABLE_PRESSURE}
        enable_pm25: {ENABLE_PM25}
    """

    logger.info(config_msg)

    try:
        logger.info("connecting to kafka")
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_PRODUCER_BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        logger.info("connected to kafka")
        
    except Exception as e:
        logger.error(f"cannot connect to Kafka: {e}")
        sys.exit(1)

    try:
        thread_1 = threading.Thread(target=weather_sensor_loop)
        thread_2 = threading.Thread(target=particle_sensor_loop)

        # Start the threads
        logger.info("starting threads")
        thread_1.start()
        thread_2.start()
        # Keep the main thread alive to handle Ctrl+C
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
