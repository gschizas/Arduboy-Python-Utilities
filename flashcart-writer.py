import os
import sys
import time
from getopt import getopt

from common import delayed_exit, BootLoader, manufacturers

try:
    from serial.tools.list_ports import comports
    from serial import Serial
except:
    print("The pySerial module is required but not installed!")
    print("Use 'python -m pip install pyserial' from the commandline to install.")
    sys.exit()

PAGESIZE = 256
BLOCKSIZE = 65536
PAGES_PER_BLOCK = BLOCKSIZE // PAGESIZE
MAX_PAGES = 65536

lcdBootProgram = b"\xD5\xF0\x8D\x14\xA1\xC8\x81\xCF\xD9\xF1\xAF\x20\x00"
verifyAfterWrite = False


################################################################################

def write_flash(pagenumber, flashdata):
    global verifyAfterWrite
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

    oldtime = time.time()
    # when starting partially in a block, preserve the beginning of old block data
    if pagenumber % PAGES_PER_BLOCK:
        blocklen = pagenumber % PAGES_PER_BLOCK * PAGESIZE
        blockaddr = pagenumber // PAGES_PER_BLOCK * PAGES_PER_BLOCK
        # read partial block data start
        bootloader.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        bootloader.read(1)
        bootloader.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF, ord("C")]))
        flashdata = bootloader.read(blocklen) + flashdata
        pagenumber = blockaddr

    # when ending partially in a block, preserve the ending of old block data
    if len(flashdata) % BLOCKSIZE:
        blocklen = BLOCKSIZE - len(flashdata) % BLOCKSIZE
        blockaddr = pagenumber + len(flashdata) // PAGESIZE
        # read partial block data end
        bootloader.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        bootloader.read(1)
        bootloader.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF, ord("C")]))
        flashdata += bootloader.read(blocklen)

    # write to flash cart
    blocks = len(flashdata) // BLOCKSIZE
    for block in range(blocks):
        if block & 1:
            bootloader.write(b"x\xC0")  # RGB LED OFF, buttons disabled
        else:
            bootloader.write(b"x\xC2")  # RGB LED RED, buttons disabled
        bootloader.read(1)
        sys.stdout.write(f"\rWriting block {block + 1}/{blocks}")
        blockaddr = pagenumber + block * BLOCKSIZE // PAGESIZE
        blocklen = BLOCKSIZE
        # write block
        bootloader.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        bootloader.read(1)
        bootloader.write(bytearray([ord("B"), (blocklen >> 8) & 0xFF, blocklen & 0xFF, ord("C")]))
        bootloader.write(flashdata[block * BLOCKSIZE: block * BLOCKSIZE + blocklen])
        bootloader.read(1)
        if verifyAfterWrite:
            bootloader.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
            bootloader.read(1)
            bootloader.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF, ord("C")]))
            if bootloader.read(blocklen) != flashdata[block * BLOCKSIZE: block * BLOCKSIZE + blocklen]:
                print(" verify failed!\n\nWrite aborted.")
                break

    # write complete
    bootloader.write(b"x\x44")  # RGB LED GREEN, buttons enabled
    bootloader.read(1)
    time.sleep(0.5)
    bootloader.exit()
    print(f"\n\nDone in {round(time.time() - oldtime, 2)} seconds")


################################################################################

def usage():
    print(f"\nUSAGE:\n\n{os.path.basename(sys.argv[0])} [pagenumber] flashdata.bin")
    print(f"{os.path.basename(sys.argv[0])} [-d datafile.bin] [-s savefile.bin | -z savesize]")
    print()
    print("[pagenumber]   Write flashdata.bin to flash starting at pagenumber. When no")
    print("               pagenumber is specified, page 0 is used instead.")
    print("-d --datafile  Write datafile to end of flash for development.")
    print("-s --savefile  Write savedata to end of flash for development.")
    print("-z --savesize  Creates blank savedata (all 0xFF) at end of flash for development")
    delayed_exit()


################################################################################

def main():
    global verifyAfterWrite
    try:
        opts, args = getopt(sys.argv[1:], "hd:s:z:", ["datafile=", "savefile=", "savesize="])
    except:
        usage()
    # verify each block after writing if script name contains verify
    verifyAfterWrite = os.path.basename(sys.argv[0]).find("verify") >= 0

    # handle development writing
    if len(opts) > 0:
        programdata = bytearray()
        savedata = bytearray()
        for o, a in opts:
            if o == '-d' or o == '--datafile':
                print(f'Reading program data from file "{a}"')
                f = open(a, "rb")
                programdata = bytearray(f.read())
                f.close()
            elif o == '-s' or o == '--savefile':
                print(f'Reading save data from file "{a}"')
                f = open(a, "rb")
                savedata = bytearray(f.read())
                f.close()
            elif (o == '-z') or (o == '--savesize'):
                savedata = bytearray(b'\xFF' * int(a))
            else:
                usage()
        if len(programdata) % PAGESIZE:
            programdata += b'\xFF' * (PAGESIZE - (len(programdata) % PAGESIZE))
        if len(savedata) % BLOCKSIZE:
            savedata += b'\xFF' * (BLOCKSIZE - (len(savedata) % BLOCKSIZE))
        savepage = (MAX_PAGES - (len(savedata) // PAGESIZE))
        programpage = savepage - (len(programdata) // PAGESIZE)
        write_flash(programpage, programdata + savedata)
        print("\nPlease use the following line in your program setup function:\n")
        if savepage < MAX_PAGES:
            print(f"  Cart::begin(0x{programpage:04X}, 0x{savepage:04X});\n")
        else:
            print(f"  Cart::begin(0x{programpage:04X});\n")
        print("\nor use defines at the beginning of your program:\n")
        print(f"#define PROGRAM_DATA_PAGE 0x{programpage:04X}")
        if savepage < MAX_PAGES:
            print(f"#define PROGRAM_SAVE_PAGE 0x{savepage:04X}")
        print("\nand use the following in your program setup function:\n")
        if savepage < MAX_PAGES:
            print("  Cart::begin(PROGRAM_DATA_PAGE, PROGRAM_SAVE_PAGE);\n")
        else:
            print("  Cart::begin(PROGRAM_DATA_PAGE);\n")

    # handle image writing ##
    else:
        if len(args) == 1:
            pagenumber = 0
            filename = args[0]
        elif len(args) == 2:
            pagenumber = int(args[0], base=0)
            filename = args[1]
        else:
            usage()

        # load and pad imagedata to multiple of PAGESIZE bytes
        if not os.path.isfile(filename):
            print(f"File not found. [{filename}]")
            delayed_exit()

        print(f'Reading flash image from file "{filename}"')
        f = open(filename, "rb")
        flashdata = bytearray(f.read())
        f.close()
        if len(flashdata) % PAGESIZE != 0:
            flashdata += b'\xFF' * (PAGESIZE - (len(flashdata) % PAGESIZE))

        # Apply patch for SSD1309 displays if script name contains 1309
        if os.path.basename(sys.argv[0]).find("1309") >= 0:
            print("Patching image for SSD1309 displays...\n")
            lcdBootProgram_addr = 0
            while lcdBootProgram_addr >= 0:
                lcdBootProgram_addr = flashdata.find(lcdBootProgram, lcdBootProgram_addr)
                if lcdBootProgram_addr >= 0:
                    flashdata[lcdBootProgram_addr + 2] = 0xE3
                    flashdata[lcdBootProgram_addr + 3] = 0xE3
        write_flash(pagenumber, flashdata)

    delayed_exit()


if __name__ == '__main__':
    print("\nArduboy flash cart writer v1.16 by Mr.Blinky May 2018 - Jun.2019\n")
    main()
