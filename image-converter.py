print("\nArduboy image include converter 1.01 by Mr.Blinky May - Jun.2019\n")

# requires PILlow to be installed. Use "python -m pip install pillow" on commandline to install

import os
import sys
import time

try:
    from PIL import Image
except:
    print("The PILlow module is not installed.")
    print("type 'python -m pip install pillow' on commandline to install")
    sys.exit()


################################################################################

def delayedExit():
    time.sleep(2)
    sys.exit()


def usage():
    print("\nUSAGE:\n\n{} imagefile\n".format(os.path.basename(sys.argv[0])))
    print("Create a C++ include file containing the image data of a .bmp or .png file that")
    print("is suitable for Arduboy drawing functions. When an image contains transparency")
    print("the image data will also contain mask data.\n")
    print("A image file may contain multiple tiles or sprites in which case the width and")
    print("height must be specified in the filename as following:\n")
    print("filename_[width]x[height].png\n")
    print("where [width] and [height] should be replaced by their pixel values.")
    print("Tiles and sprites in a tilesheet may be seperated by some spacing. The")
    print("number of pixels surrounding the tile or sprite must be the same. The")
    print("spacing must be specified in the filename as following:\n")
    print("filename_[width]x[height]_[spacing].png\n")
    print("where [width], [height] and [spacing] should be replaced by their pixel values.")

    delayedExit()


################################################################################

if len(sys.argv) < 2: usage()
for filenumber in range(1, len(sys.argv)):  # support multiple files
    filename = sys.argv[filenumber]
    print("converting '{}'".format(filename))
    ## parse filename ## FILENAME_[WxH]_[S].[EXT]"
    spriteWidth = 0
    spriteHeight = 0
    spacing = 0
    elements = os.path.basename(os.path.splitext(filename)[0]).lower().split("_")
    lastElement = len(elements) - 1
    # get width and height from filename
    i = lastElement
    while i > 0:
        if "x" in elements[i]:
            spriteWidth = int(elements[i].split("x")[0])
            spriteHeight = int(elements[i].split("x")[1])
            if i < lastElement:
                spacing = int(elements[i + 1])
            break
        else:
            i -= 1
    else:
        i = lastElement
    # get sprite name (may contain underscores) from filename
    spriteName = elements[0]
    for j in range(1, i):
        spriteName += "_" + elements[j]

        # load image
    img = Image.open(sys.argv[1]).convert("RGBA")
    pixels = list(img.getdata())
    # check for transparency
    transparency = False
    for i in pixels:
        if i[3] < 255:
            transparency = True
            break

    # check for multiple frames/tiles
    if spriteWidth > 0:
        hframes = (img.size[0] - spacing) // (spriteWidth + spacing)
    else:
        spriteWidth = img.size[0] - 2 * spacing
        hframes = 1
    if spriteHeight > 0:
        vframes = (img.size[1] - spacing) // (spriteHeight + spacing)
    else:
        spriteHeight = img.size[1] - 2 * spacing
        vframes = 1

    # create byte array for bin file
    size = (spriteHeight + 7) // 8 * spriteWidth * hframes * vframes
    if transparency:
        size += size
    bytes = bytearray([spriteWidth >> 8, spriteWidth & 0xFF, spriteHeight >> 8, spriteHeight & 0xFF])
    bytes += bytearray(size)
    i = 4
    b = 0
    m = 0
    with open(os.path.splitext(filename)[0] + ".h", "w") as headerfile:
        headerfile.write("\n")
        headerfile.write("constexpr uint8_t {}_width = {};\n".format(spriteName, spriteWidth))
        headerfile.write("constexpr uint8_t {}_height = {};\n".format(spriteName, spriteHeight))
        headerfile.write("\n")
        headerfile.write("const uint8_t PROGMEM {}[] =\n".format(spriteName, ))
        headerfile.write("{\n")
        headerfile.write("  {}_width, {}_height,\n".format(spriteName, spriteName))
        fy = spacing
        for v in range(vframes):
            fx = spacing
            for h in range(hframes):
                for y in range(0, spriteHeight, 8):
                    line = "  "
                    for x in range(0, spriteWidth):
                        for p in range(0, 8):
                            b = b >> 1
                            m = m >> 1
                            if (y + p) < spriteHeight:  # for heights that are not a multiple of 8 pixels
                                if pixels[(fy + y + p) * img.size[0] + fx + x][1] > 64:
                                    b |= 0x80  # white pixel
                                if pixels[(fy + y + p) * img.size[0] + fx + x][3] == 255:
                                    m |= 0x80  # transparent pixel
                        bytes[i] = b
                        line += "0x{:02X}, ".format(b)
                        i += 1
                        if transparency:
                            bytes[i] = m
                            line += "0x{:02X}, ".format(b)
                            i += 1
                    lastline = (v + 1 == vframes) and (h + 1 == hframes) and (y + 8 >= spriteHeight)
                    if lastline:
                        line = line[:-2]
                    headerfile.write(line + "\n")
                if not lastline:
                    headerfile.write("\n")
                fx += spriteWidth + spacing
            fy += spriteHeight + spacing
        headerfile.write("};\n")
        headerfile.close()

    # save bytearray to file (temporary code for fx datafile creation)
    with open(os.path.splitext(filename)[0] + ".bin", "wb") as binfile:
        binfile.write(bytes)
        binfile.close
