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


class PM1006:
    """
    LED Particle Sensor with Dust Correction PM1006

    Datasheet: https://cdn-learn.adafruit.com/assets/assets/000/122/217/original/PM1006_LED_PARTICLE_SENSOR_MODULE_SPECIFICATIONS-1.pdf?1688148991
    """
    def __init__(self):
        self.port = "/dev/ttyS0"

    def open_connection(self):
        self.__serial_device = serial.Serial(
            port=self.port,
            baudrate=9600,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )

    def close_connection(self):
        self.__serial_device.close()

    def get_pm25(self):
        bytes_data = self.__serial_device.read(20)
        hex_array = [hex(byte) for byte in bytes_data]
        if not self.check_valid_msg(bytes_data):
            return None
        value = (bytes_data[5] * 256) + bytes_data[6]

        # flush serial
        self.__serial_device.flushOutput()

        return hex_array, value
    
    def check_valid_msg(self, bytes_data):
        first_byte = bytes_data[0]
        second_byte = bytes_data[1]
        third_byte = bytes_data[2]

        if first_byte == 0x16 and second_byte == 0x11 and third_byte == 0x0b:
            return True
        else:
            return False



