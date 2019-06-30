import sys
import time

from serial import Serial
from serial.tools.list_ports import comports

compatibledevices = [
    # Arduboy Leonardo
    "VID:PID=2341:0036", "VID:PID=2341:8036",
    "VID:PID=2A03:0036", "VID:PID=2A03:8036",
    # Arduboy Micro
    "VID:PID=2341:0037", "VID:PID=2341:8037",
    "VID:PID=2A03:0037", "VID:PID=2A03:8037",
    # Genuino Micro
    "VID:PID=2341:0237", "VID:PID=2341:8237",
    # Sparkfun Pro Micro 5V
    "VID:PID=1B4F:9205", "VID:PID=1B4F:9206",
    # Adafruit ItsyBitsy 5V
    "VID:PID=239A:000E", "VID:PID=239A:800E",
]

manufacturers = {
    0x01: "Spansion",
    0x14: "Cypress",
    0x1C: "EON",
    0x1F: "Adesto(Atmel)",
    0x20: "Micron",
    0x37: "AMIC",
    0x9D: "ISSI",
    0xC2: "General Plus",
    0xC8: "Giga Device",
    0xBF: "Microchip",
    0xEF: "Winbond"
}


class BootLoader():
    def __init__(self):
        self._bootloader = None
        self._active = False

    def start(self):
        global bootloader
        # find and connect to Arduboy in bootloader mode
        port = self.get_com_port(True)
        if port is None: delayed_exit()
        if not self._active:
            print("Selecting bootloader mode...")
            bootloader = Serial(port, 1200)
            bootloader.close()
            time.sleep(0.5)
            # wait for disconnect and reconnect in bootloader mode
            while self.get_com_port(False) == port:
                time.sleep(0.1)
                if self._active: break
            while self.get_com_port(False) is None: time.sleep(0.1)
            port = self.get_com_port(True)

        sys.stdout.write("Opening port ...")
        sys.stdout.flush()
        for retries in range(20):
            try:
                time.sleep(0.1)
                bootloader = Serial(port, 57600)
                break
            except:
                if retries == 19:
                    print(" Failed!")
                    delayed_exit()
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(0.4)
        print()

    def get_com_port(self, verbose):
        devicelist = list(comports())
        for device in devicelist:
            for vidpid in compatibledevices:
                if vidpid in device[2]:
                    port = device[0]
                    self._active = (compatibledevices.index(vidpid) & 1) == 0
                    if verbose: print(f"Found {device[1]} at port {port}")
                    return port
        if verbose: print("Arduboy not found.")

    def exit(self):
        self._bootloader.write(b"E")
        self._bootloader.read(1)

    def get_version(self):
        self._bootloader.write(b"V")
        return int(self._bootloader.read(2))

    def get_jedec_id(self):
        self._bootloader.write(b"j")
        jedec_id = self._bootloader.read(3)
        time.sleep(0.5)
        self._bootloader.write(b"j")
        jedec_id2 = self._bootloader.read(3)
        if jedec_id2 != jedec_id or jedec_id == b'\x00\x00\x00' or jedec_id == b'\xFF\xFF\xFF':
            print("No flash cart detected.")
            delayed_exit()
        return bytearray(jedec_id)

    def write(self, data: bytes):
        return self._bootloader.write(data)

    def read(self, size):
        return self._bootloader.read(size)


def delayed_exit():
    time.sleep(2)
    sys.exit()
