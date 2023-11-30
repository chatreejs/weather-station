import os
import json
import time

from dotenv import load_dotenv
from datetime import datetime
from models import SensorUpdate
from kafka import KafkaProducer
from sensors import BME280


def send_message(message: dict, header_type: str):
    print(f"sending message: {message}")
    producer.send(
            topic=KAFKA_PRODUCER_TOPIC,
            key=bytes('data', 'utf-8'),
            value=message,
            headers=[("__TypeId__", bytes(header_type, "utf-8"))]
    )
    producer.flush()
    

def main():
    previous_temperature = None
    previous_humidity = None
    previous_pressure = None

    bme280 = BME280()

    while True:
        current_datetime = datetime.now().astimezone()
        temperature = bme280.get_temperature()
        humidity = bme280.get_humidity()
        pressure = bme280.get_pressure()

        if temperature is not None and previous_temperature != temperature:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                type="temperature",
                value=temperature,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_temperature = temperature
        
        if humidity is not None and previous_humidity != humidity:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                type="humidity",
                value=humidity,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_humidity = humidity
        
        if pressure is not None and previous_pressure != pressure:
            sensor_data = SensorUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME + "." + "bme280",
                type="pressure",
                value=pressure,
                time_of_event=current_datetime.isoformat()
            )
            message = sensor_data.to_dict()
            send_message(message, "SensorUpdate")
            previous_pressure = pressure

        time.sleep(int(SCRAP_INTERVAL))

if __name__ == "__main__":
    print("starting weather-station")
    print("loading env file")
    load_dotenv()
    KAFKA_PRODUCER_BOOTSTRAP_SERVERS=os.getenv("KAFKA_PRODUCER_BOOTSTRAP_SERVERS")
    KAFKA_PRODUCER_TOPIC=os.getenv("KAFKA_PRODUCER_TOPIC")
    KAFKA_PRODUCER_SOURCE_NAME=os.getenv("KAFKA_PRODUCER_SOURCE_NAME")
    SCRAP_INTERVAL=os.getenv("SCRAP_INTERVAL")

    config_msg = f"""configuration
        topic: {KAFKA_PRODUCER_TOPIC}
        source_name: {KAFKA_PRODUCER_SOURCE_NAME}
        scrap_interval: {SCRAP_INTERVAL}
    """
    print(config_msg)

    try:
        print("connecting to kafka")
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_PRODUCER_BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        print("connected to kafka")
        
    except Exception as e:
        print(f"[ERROR] cannot connect to Kafka: {e}")
        exit(1)

    try:
        main()
    except KeyboardInterrupt:
        print("exiting...")
        exit(0)
    except Exception as e:
        print(f"[ERROR] msg: {e}")
        exit(1)