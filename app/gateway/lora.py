from log4py import Logger
from SX127x.board_config import BOARD
from SX127x.LoRa import *

BOARD.setup()
BOARD.reset()


@Logger.class_logger()
class LoRaReceiver(LoRa):
    def __init__(self, verbose=False):
        self.logger.info("Initializing LoRa Receiver")
        super(LoRaReceiver, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_freq(433)
        self.set_coding_rate(CODING_RATE.CR4_5)
        self.set_spreading_factor(10)
        self.set_preamble(8)
        self.set_pa_config(pa_select=1)
        self.set_rx_crc(True)
        self.set_dio_mapping([0, 0, 0, 0, 0, 0])
        self.received_message = None

    def on_rx_done(self):
        BOARD.blink(0.1, 1)
        payload = self.read_payload(nocheck=True)
        self.received_message = bytes(payload).decode("utf-8", "ignore")
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def start(self):
        self.set_mode(MODE.RXCONT)

    def teardown(self):
        self.set_mode(MODE.SLEEP)
        BOARD.teardown()
