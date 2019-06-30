import os
import sys

from common import delayed_exit, BootLoader


def main():
    if len(sys.argv) != 2:
        print(f"\nUsage: {os.path.basename(sys.argv[0])} eepromfile.bin\n")
        delayed_exit()

    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print(f"File not found. [{filename}]")
        delayed_exit()

    print(f'Reading EEPROM data from file "{filename}"')
    f = open(filename, "rb")
    eepromdata = bytearray(f.read())
    f.close()

    if len(eepromdata) != 1024:
        print("File does not contain 1K (1024 bytes) of EEPROM data\nRestore aborted")
        delayed_exit()

    # restore
    bootloader = BootLoader()
    bootloader.start()
    print("Restoring EEPROM data...")
    bootloader.write(b"A\x00\x00")
    bootloader.read(1)
    bootloader.write(b"B\x04\x00E")
    bootloader.write(eepromdata)
    bootloader.read(1)
    bootloader.exit()
    print("Done")
    delayed_exit()


if __name__ == '__main__':
    print("\nArduboy EEPROM restore v1.0 by Mr.Blinky April 2018")
    main()
