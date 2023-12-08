import random
import serial


class BME280:
    def get_temperature(self):
        return round(random.uniform(25.0, 32.0), 4)

    def get_humidity(self):
        return round(random.uniform(40.0, 60.0), 4)
    
    def get_pressure(self):
        return round(random.uniform(980.0, 1100.0), 4)
    
    def get_altitude(self):
        return round(random.uniform(1.0, 5.0), 4)


class PM1006K:
    """
    LED Particle Sensor with Dust Correction PM1006K

    Datasheet: https://en.gassensor.com.cn/Product_files/Specifications/LED%20Particle%20Sensor%20PM1006K%20Specification.pdf
    """
    def __init__(self):
        self.__serial_device = serial.Serial(
            port="/dev/ttyS0",
            baudrate=9600,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )

    def get_pm25(self):
        byte_data = self.__serial_device.read(20)
        value = (byte_data[5] << 8) | byte_data[6]
        self.__serial_device.flushOutput()
        return value


