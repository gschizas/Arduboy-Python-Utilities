from common import delayedExit, bootloaderStart, bootloaderExit, bootloader

print("\nArduboy EEPROM erase v1.0 by Mr.Blinky May 2018")

# requires pyserial to be installed. Use "pip install pyserial" on commandline

################################################################################

bootloaderStart()
print("Erasing EEPROM data...")
bootloader.write("A\x00\x00")
bootloader.read(1)
bootloader.write("B\x04\x00E")
bootloader.write(bytearray("\xFF" * 1024))
bootloader.read(1)
bootloaderExit()
print("Erase complete.")
delayedExit()
