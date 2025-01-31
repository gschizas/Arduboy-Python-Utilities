import sys
import time

from common import delayed_exit, BootLoader, manufacturers

# requires pyserial to be installed. Use "python -m pip install pyserial" on commandline

try:
    from serial.tools.list_ports import comports
    from serial import Serial
except:
    print("The pySerial module is required but not installed!")
    print("Use 'python -m pip install pyserial' from the commandline to install.")
    sys.exit()

PAGESIZE = 256
BLOCKSIZE = 65536


def main():
    bootloader = BootLoader()
    bootloader.start()

    # check version
    if bootloader.get_version() < 13:
        print("Bootloader has no flash cart support\nWrite aborted!")
        delayed_exit()

    # detect flash cart
    jedec_id = bootloader.get_jedec_id()
    if jedec_id[0] in manufacturers.keys():
        manufacturer = manufacturers[jedec_id[0]]
    else:
        manufacturer = "unknown"
    capacity = 1 << jedec_id[2]
    print(f"\nFlash cart JEDEC ID    : {jedec_id[0]:02X}{jedec_id[1]:02X}{jedec_id[2]:02X}")
    print(f"Flash cart Manufacturer: {manufacturer}")
    print(f"Flash cart capacity    : {capacity // 1024} Kbyte\n")

    filename = time.strftime("flashcart-backup-image-%Y%m%d-%H%M%S.bin", time.localtime())
    print(f'Writing flash image to file: "{filename}"\n')

    oldtime = time.time()
    blocks = capacity // BLOCKSIZE
    with open(filename, "wb") as binfile:
        for block in range(0, blocks):
            if block & 1:
                bootloader.write(b"x\xC0")  # RGB BLUE OFF, buttons disabled
            else:
                bootloader.write(b"x\xC1")  # RGB BLUE RED, buttons disabled
            bootloader.read(1)
            sys.stdout.write(f"\rReading block {block + 1}/{blocks}")

            blockaddr = block * BLOCKSIZE // PAGESIZE

            bootloader.write(b"A")
            bootloader.write(bytearray([blockaddr >> 8, blockaddr & 0xFF]))
            bootloader.read(1)

            blocklen = BLOCKSIZE

            bootloader.write(b"g")
            bootloader.write(bytearray([(blocklen >> 8) & 0xFF, blocklen & 0xFF]))

            bootloader.write(b"C")
            contents = bootloader.read(blocklen)
            binfile.write(contents)

    bootloader.write(b"x\x44")  # RGB LED GREEN, buttons enabled
    bootloader.read(1)
    time.sleep(0.5)
    bootloader.exit()
    print(f"\n\nDone in {round(time.time() - oldtime, 2)} seconds")
    delayed_exit()


if __name__ == '__main__':
    print("\nArduboy flash cart backup v1.13 by Mr.Blinky May 2018 jun.2019\n")
    main()
