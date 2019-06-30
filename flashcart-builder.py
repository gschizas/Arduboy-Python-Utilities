print("\nArduboy Flashcart image builder v1.04 by Mr.Blinky Jun 2018 - May 2019\n")

# requires PILlow. Use 'python -m pip install pillow' to install

import csv
import os
import sys
import time
from common import delayed_exit

try:
    from PIL import Image
except:
    print("The PILlow module is required but not installed!")
    print("Use 'python -m pip install pillow' from the commandline to install.")
    sys.exit()

ID_LIST = 0
ID_TITLE = 1
ID_TITLESCREEN = 2
ID_HEXFILE = 3
ID_DATAFILE = 4
ID_SAVEFILE = 5


def default_header():
    return bytearray("ARDUBOY".encode() + (b'\xFF' * 249))


def load_title_screen_data(screen_filename):
    if not os.path.isabs(screen_filename):
        screen_filename = path + screen_filename
    if not os.path.isfile(screen_filename):
        print(f"Error: Title screen '{screen_filename}' not found.")
        delayed_exit()
    img = Image.open(screen_filename).convert("1")
    width, height = img.size
    if (width != 128) or (height != 64):
        print(f"Error: Title screen '{screen_filename}' is not 128 x 64 pixels.")
        delayed_exit()
    pixels = list(img.getdata())
    buffer = bytearray(int((height // 8) * width))
    i = 0
    b = 0
    for y in range(0, height, 8):
        for x in range(0, width):
            for p in range(0, 8):
                b = b >> 1
                if pixels[(y + p) * width + x] > 0:
                    b |= 0x80
            buffer[i] = b
            i += 1
    return buffer


def load_hex_file_data(hex_filename):
    if not os.path.isabs(hex_filename):
        hex_filename = path + hex_filename
    if not os.path.isfile(hex_filename):
        return bytearray()
    f = open(hex_filename, "r")
    records = f.readlines()
    f.close()
    buffer = bytearray(b'\xFF' * 32768)
    flash_end = 0
    for rcd in records:
        if rcd == ":00000001FF": break
        if rcd[0] == ":":
            rcd_len = int(rcd[1:3], 16)
            rcd_typ = int(rcd[7:9], 16)
            rcd_addr = int(rcd[3:7], 16)
            rcd_sum = int(rcd[9 + rcd_len * 2:11 + rcd_len * 2], 16)
            if (rcd_typ == 0) and (rcd_len > 0):
                flash_addr = rcd_addr
                checksum = rcd_sum
                for i in range(1, 9 + rcd_len * 2, 2):
                    byte = int(rcd[i:i + 2], 16)
                    checksum = (checksum + byte) & 0xFF
                    if i >= 9:
                        buffer[flash_addr] = byte
                        flash_addr += 1
                        if flash_addr > flash_end:
                            flash_end = flash_addr
                if checksum != 0:
                    print(f"Error: Hex file '{hex_filename}' contains errors.")
                    delayed_exit()
    flash_end = int((flash_end + 255) / 256) * 256
    return buffer[0:flash_end]


def load_data_file(data_filename):
    if not os.path.isabs(data_filename):
        data_filename = path + data_filename
    if not os.path.isfile(data_filename):
        return bytearray()

    with open(data_filename, "rb") as file_handle:
        buffer = bytearray(file_handle.read())
        pagealign = bytearray(b'\xFF' * (256 - len(buffer) % 256))
        return buffer + pagealign


if len(sys.argv) != 2:
    print(f"\nUsage: {os.path.basename(sys.argv[0])} flashcart-index.csv\n")
    delayed_exit()

previouspage = 0xFFFF
currentpage = 0
nextpage = 0
csvfile = os.path.abspath(sys.argv[1])
path = os.path.dirname(csvfile) + os.sep
if not os.path.isfile(csvfile):
    print(f"Error: CSV-file '{csvfile}' not found.")
    delayed_exit()
TitleScreens = 0
Sketches = 0
filename = csvfile.lower().replace("-index", "").replace(".csv", "-image.bin")
with open(filename, "wb") as binfile:
    with open(csvfile, "r") as file:
        data = csv.reader(file, quotechar='"', delimiter=";")
        next(data, None)
        print(f"Building: {filename}\n")
        print("List Title                     Curr. Prev. Next  ProgSize DataSize SaveSize")
        print("---- ------------------------- ----- ----- ----- -------- -------- --------")
        for row in data:
            while len(row) < 7: row.append('')  # add missing cells
            header = default_header()
            title = load_title_screen_data(row[ID_TITLESCREEN])
            program = load_hex_file_data(row[ID_HEXFILE])
            programsize = len(program)
            datafile = load_data_file(row[ID_DATAFILE])
            datasize = len(datafile)
            slotsize = ((programsize + datasize) >> 8) + 5
            programpage = currentpage + 5
            datapage = programpage + (programsize >> 8)
            nextpage += slotsize
            header[7] = int(row[ID_LIST])  # list number
            header[8] = previouspage >> 8
            header[9] = previouspage & 0xFF
            header[10] = nextpage >> 8
            header[11] = nextpage & 0xFF
            header[12] = slotsize >> 8
            header[13] = slotsize & 0xFF
            header[14] = programsize >> 7  # program size in 128 byte pages
            if programsize > 0:
                header[15] = programpage >> 8
                header[16] = programpage & 0xFF
                if datasize > 0:
                    program[0x14] = 0x18
                    program[0x15] = 0x95
                    program[0x16] = datapage >> 8
                    program[0x17] = datapage & 0xFF
            if datasize > 0:
                header[17] = datapage >> 8
                header[18] = datapage & 0xFF
            binfile.write(header)
            binfile.write(title)
            binfile.write(program)
            binfile.write(datafile)
            if programsize == 0:
                print(f"{row[ID_LIST]:4} {row[ID_TITLE]:25} {currentpage:5} {previouspage:5} {nextpage:5}")
            else:
                print((f"{row[ID_LIST]:4}  {row[ID_TITLE][:24]:24} {currentpage:5} "
                       f"{previouspage:5} {nextpage:5} {programsize:8} {datasize:8} {0:8}"))
            previouspage = currentpage
            currentpage = nextpage
            if programsize > 0:
                Sketches += 1
            else:
                TitleScreens += 1
        print("---- ------------------------- ----- ----- ----- -------- -------- --------")
        print("                                Page  Page  Page    Bytes    Bytes    Bytes")

print((f"\nImage build complete with {TitleScreens} Title screens, {Sketches} Sketches, "
       f"{(nextpage + 3) / 4} Kbyte used."))
delayed_exit()
