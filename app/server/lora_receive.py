from SX127x.LoRa import *
from SX127x.board_config import BOARD
import time

# Setup for the Raspberry Pi GPIO
BOARD.setup()

class LoRaReceiver(LoRa):
    def __init__(self, verbose=False):
        super(LoRaReceiver, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_freq(433)  # Set to 433 MHz to match the Arduino

        # Set the same LoRa parameters as in the Arduino code
        self.set_coding_rate(CODING_RATE.CR4_5)
        self.set_spreading_factor(10)
        self.set_preamble(8)
        self.set_rx_crc(True)

        # Configure DIO0 interrupt for receiving
        self.set_dio_mapping([0,0,0,0,0,0])  # DIO0 set for RxDone

    def on_rx_done(self):
        # This function will be called when a packet is received
        payload = self.read_payload(nocheck=True)
        print(payload)
        # Convert the byte array to a string
        message = ''.join(chr(byte) for byte in payload)

        print("Received message:", message)
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)  # Set back to continuous RX mode

# Instantiate the receiver class
lora = LoRaReceiver(verbose=True)
lora.set_pa_config(pa_select=1)

print(lora)

lora.set_mode(MODE.RXCONT)  # Start in continuous receive mode

try:
    print("Listening for LoRa messages...")
    while True:
        time.sleep(1)  # Keeps the program running
except KeyboardInterrupt:
    print("Process interrupted by user")
finally:
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()