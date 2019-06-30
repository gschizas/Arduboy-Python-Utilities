import time

from common import delayed_exit, BootLoader


def main():
    bootloader = BootLoader()
    bootloader.start()
    filename = time.strftime("sketch-backup-%Y%m%d-%H%M%S.bin", time.localtime())
    print("Reading sketch...")
    bootloader.write(b"A\x00\x00")
    bootloader.read(1)
    bootloader.write(b"g\x70\x00F")
    backupdata = bytearray(bootloader.read(0x7000))
    print('saving sketch to "{}"'.format(filename))
    f = open(filename, "wb")
    f.write(backupdata)
    f.close()
    print("Done")
    bootloader.exit()
    delayed_exit()


if __name__ == '__main__':
    print("\nArduboy sketch backup v1.0 by Mr.Blinky April 2018")
    main()
