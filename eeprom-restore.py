from common import delayed_exit, BootLoader

print("\nArduboy EEPROM restore v1.0 by Mr.Blinky April 2018")

# requires pyserial to be installed. Use "pip install pyserial" on commandline

import os
import sys

################################################################################

if len(sys.argv) != 2:
    print("\nUsage: {} eepromfile.bin\n".format(os.path.basename(sys.argv[0])))
    delayed_exit()

filename = sys.argv[1]
if not os.path.isfile(filename):
    print("File not found. [{}]".format(filename))
    delayed_exit()

print('Reading EEPROM data from file "{}"'.format(filename))
f = open(filename, "rb")
eepromdata = bytearray(f.read())
f.close

if len(eepromdata) != 1024:
    print("File does not contain 1K (1024 bytes) of EEPROM data\nRestore aborted")
    delayed_exit()

## restore ##
bootloader = BootLoader()
bootloader.start()
print("Restoring EEPROM data...")
bootloader.write("A\x00\x00")
bootloader.read(1)
bootloader.write("B\x04\x00E")
bootloader.write(eepromdata)
bootloader.read(1)
bootloader.exit()
print("Done")
delayed_exit()
