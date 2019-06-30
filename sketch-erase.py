from common import delayedExit, bootloaderStart, bootloaderExit, bootloader

print("\nArduboy python sketch eraser v1.0 by Mr.Blinky May 2018")

# requires pyserial to be installed. Use "pip install pyserial" on commandline

# rename this script filename to 'uploader-1309.py' to patch uploads on the fly
# for use with SSD1309 displays

caterina_overwrite = False

flash_addr = 0
flash_data = bytearray(chr(0xFF) * 32768)
flash_page = 1
flash_page_count = 0
flash_page_used = [False] * 256

################################################################################

bootloaderStart()

## Erase ##
print("\nErasing sketch startup page")
bootloader.write("A\x00\x00")  # select page 0
bootloader.read(1)
bootloader.write("B\x00\x00F")  # writing 0 length block will erase page only
bootloader.read(1)
bootloader.write("A\x00\x00")  # select page 0
bootloader.read(1)
bootloader.write("g\x00\x80F")  # read 128 byte page
if bytearray(bootloader.read(128)) == bytearray("\xff" * 128):
    print("\nErase successful")
else:
    print("\nErase failed")
bootloaderExit()
delayedExit()
