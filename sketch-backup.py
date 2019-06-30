from common import delayed_exit, bootloaderStart, bootloaderExit, bootloader

print("\nArduboy sketch backup v1.0 by Mr.Blinky April 2018")

# requires pyserial to be installed. Use "pip install pyserial" on commandline

import time

################################################################################

bootloaderStart()
filename = time.strftime("sketch-backup-%Y%m%d-%H%M%S.bin", time.localtime())
print("Reading sketch...")
bootloader.write("A\x00\x00")
bootloader.read(1)
bootloader.write("g\x70\x00F")
backupdata = bytearray(bootloader.read(0x7000))
print('saving sketch to "{}"'.format(filename))
f = open(filename, "wb")
f.write(backupdata)
f.close
print("Done")
bootloaderExit()
delayed_exit()
