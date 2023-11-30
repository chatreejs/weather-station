import os
import json
import time

from dotenv import load_dotenv
from datetime import datetime
from models.temperature_update import TemperatureUpdate
from models.humidity_update import HumidityUpdate
from kafka import KafkaProducer
from sensor.dht22 import DHT22


def send_message(message: dict, header_type: str):
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

    dht22 = DHT22()

    while True:
        current_datetime = datetime.now().astimezone()
        temperature = dht22.read_temperature()
        humidity = dht22.read_humidity()

        if temperature is not None and previous_temperature != temperature:
            temperature_data = TemperatureUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME,
                type="temperature",
                temperature=temperature,
                time_of_event=current_datetime.isoformat()
            )
            message = temperature_data.to_dict()
            print(f"Temperature Update: {message}")
            send_message(message, "TemperatureUpdate")
            previous_temperature = temperature
        
        if humidity is not None and previous_humidity != humidity:
            humidity_data = HumidityUpdate(
                source=KAFKA_PRODUCER_SOURCE_NAME,
                type="humidity",
                humidity=humidity,
                time_of_event=current_datetime.isoformat()
            )
            message = humidity_data.to_dict()
            print(f"Humidity Update: {message}")
            send_message(message, "HumidityUpdate")
            previous_humidity = humidity

        time.sleep(int(SCRAP_INTERVAL))

if __name__ == "__main__":
    load_dotenv()
    KAFKA_PRODUCER_BOOTSTRAP_SERVERS=os.getenv("KAFKA_PRODUCER_BOOTSTRAP_SERVERS")
    KAFKA_PRODUCER_TOPIC=os.getenv("KAFKA_PRODUCER_TOPIC")
    KAFKA_PRODUCER_SOURCE_NAME=os.getenv("KAFKA_PRODUCER_SOURCE_NAME")
    SCRAP_INTERVAL=os.getenv("SCRAP_INTERVAL")

    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_PRODUCER_BOOTSTRAP_SERVERS],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        print("Connected to Kafka")
        print(f"Topic: {KAFKA_PRODUCER_TOPIC}")
        print(f"Source Name: {KAFKA_PRODUCER_SOURCE_NAME}")
        print(f"Scrap Interval: {SCRAP_INTERVAL}")
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        exit(1)

    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)