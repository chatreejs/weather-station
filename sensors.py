import random


class BME280:
    def get_temperature(self):
        return round(random.uniform(25.0, 32.0), 4)

    def get_humidity(self):
        return round(random.uniform(40.0, 60.0), 4)
    
    def get_pressure(self):
        return round(random.uniform(980.0, 1100.0), 4)
    
    def get_altitude(self):
        return round(random.uniform(1.0, 5.0), 4)