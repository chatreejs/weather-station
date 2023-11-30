import random


class DHT22:
    def read_temperature(self):
        return round(random.uniform(25.0, 32.0), 4)

    def read_humidity(self):
        return round(random.uniform(40.0, 60.0), 4)
