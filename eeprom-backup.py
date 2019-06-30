from common import delayed_exit, BootLoader

print("\nArduboy EEPROM backup v1.0 by Mr.Blinky April 2018")

# requires pyserial to be installed. Use "pip install pyserial" on commandline

import time

################################################################################

bootloader = BootLoader()
bootloader.start()
filename = time.strftime("eeprom-backup-%Y%m%d-%H%M%S.bin", time.localtime())
print("Reading 1K EEPROM data...")
bootloader.write(b"A\x00\x00")
bootloader.read(1)
bootloader.write(b"g\x04\x00E")
eepromdata = bytearray(bootloader.read(1024))
print('saving 1K EEPROM data to "{}"'.format(filename))
f = open(filename, "wb")
f.write(eepromdata)
f.close()
print("Done")
bootloader.exit()
delayed_exit()
