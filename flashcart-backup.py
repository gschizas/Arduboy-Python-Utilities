from common import delayed_exit, bootloaderStart, bootloaderExit, bootloader, manufacturers, getVersion, getJedecID

print("\nArduboy flash cart backup v1.13 by Mr.Blinky May 2018 jun.2019\n")

# requires pyserial to be installed. Use "python -m pip install pyserial" on commandline

import sys
import time

try:
    from serial.tools.list_ports import comports
    from serial import Serial
except:
    print("The pySerial module is required but not installed!")
    print("Use 'python -m pip install pyserial' from the commandline to install.")
    sys.exit()

PAGESIZE = 256
BLOCKSIZE = 65536

################################################################################

bootloaderStart()

# check version
if getVersion() < 13:
    print("Bootloader has no flash cart support\nWrite aborted!")
    delayed_exit()

## detect flash cart ##
jedec_id = getJedecID()
if jedec_id[0] in manufacturers.keys():
    manufacturer = manufacturers[jedec_id[0]]
else:
    manufacturer = "unknown"
capacity = 1 << jedec_id[2]
print("\nFlash cart JEDEC ID    : {:02X}{:02X}{:02X}".format(jedec_id[0], jedec_id[1], jedec_id[2]))
print("Flash cart Manufacturer: {}".format(manufacturer))
print("Flash cart capacity    : {} Kbyte\n".format(capacity // 1024))

filename = time.strftime("flashcart-backup-image-%Y%m%d-%H%M%S.bin", time.localtime())
print('Writing flash image to file: "{}"\n'.format(filename))

oldtime = time.time()
blocks = capacity // BLOCKSIZE
with open(filename, "wb") as binfile:
    for block in range(0, blocks):
        if block & 1:
            bootloader.write(b"x\xC0")  # RGB BLUE OFF, buttons disabled
        else:
            bootloader.write(b"x\xC1")  # RGB BLUE RED, buttons disabled
        bootloader.read(1)
        sys.stdout.write("\rReading block {}/{}".format(block + 1, blocks))

        blockaddr = block * BLOCKSIZE // PAGESIZE

        bootloader.write("A".encode())
        bootloader.write(bytearray([blockaddr >> 8, blockaddr & 0xFF]))
        bootloader.read(1)

        blocklen = BLOCKSIZE

        bootloader.write("g".encode())
        bootloader.write(bytearray([(blocklen >> 8) & 0xFF, blocklen & 0xFF]))

        bootloader.write("C".encode())
        contents = bootloader.read(blocklen)
        binfile.write(contents)

bootloader.write(b"x\x44")  # RGB LED GREEN, buttons enabled
bootloader.read(1)
time.sleep(0.5)
bootloaderExit()
print("\n\nDone in {} seconds".format(round(time.time() - oldtime, 2)))
delayed_exit()
