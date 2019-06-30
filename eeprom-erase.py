from common import delayed_exit, BootLoader


def main():
    bootloader = BootLoader()
    bootloader.start()
    print("Erasing EEPROM data...")
    bootloader.write(b"A\x00\x00")
    bootloader.read(1)
    bootloader.write(b"B\x04\x00E")
    bootloader.write(bytearray("\xFF" * 1024))
    bootloader.read(1)
    bootloader.exit()
    print("Erase complete.")
    delayed_exit()


if __name__ == '__main__':
    print("\nArduboy EEPROM erase v1.0 by Mr.Blinky May 2018")
    main()
