import time

from common import delayed_exit, BootLoader


def main():
    bootloader = BootLoader()
    bootloader.start()
    filename = time.strftime("eeprom-backup-%Y%m%d-%H%M%S.bin", time.localtime())
    print("Reading 1K EEPROM data...")
    bootloader.write(b"A\x00\x00")
    bootloader.read(1)
    bootloader.write(b"g\x04\x00E")
    eepromdata = bytearray(bootloader.read(1024))
    print(f'saving 1K EEPROM data to "{filename}"')
    f = open(filename, "wb")
    f.write(eepromdata)
    f.close()
    print("Done")
    bootloader.exit()
    delayed_exit()


if __name__ == '__main__':
    print("\nArduboy EEPROM backup v1.0 by Mr.Blinky April 2018")
    main()
