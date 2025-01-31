# requires PILlow to be installed. Use "python -m pip install pillow" on commandline to install

import os
import sys

from common import delayed_exit

try:
    from PIL import Image
except:
    print("The PILlow module is not installed.")
    print("type 'python -m pip install pillow' on commandline to install")
    sys.exit()


def usage():
    print(f"\nUSAGE:\n\n{os.path.basename(sys.argv[0])} imagefile\n")
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

    delayed_exit()


def main():
    if len(sys.argv) < 2: usage()
    for filenumber in range(1, len(sys.argv)):  # support multiple files
        filename = sys.argv[filenumber]
        print(f"converting '{filename}'")
        # parse filename: FILENAME_[WxH]_[S].[EXT]"
        sprite_width = 0
        sprite_height = 0
        spacing = 0
        elements = os.path.basename(os.path.splitext(filename)[0]).lower().split("_")
        last_element = len(elements) - 1
        # get width and height from filename
        i = last_element
        while i > 0:
            if "x" in elements[i]:
                sprite_width = int(elements[i].split(b"x")[0])
                sprite_height = int(elements[i].split(b"x")[1])
                if i < last_element:
                    spacing = int(elements[i + 1])
                break
            else:
                i -= 1
        else:
            i = last_element
        # get sprite name (may contain underscores) from filename
        sprite_name_raw = elements[0]
        for j in range(1, i):
            sprite_name_raw += b"_" + elements[j]
        sprite_name = sprite_name_raw.decode()

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
        if sprite_width > 0:
            hframes = (img.size[0] - spacing) // (sprite_width + spacing)
        else:
            sprite_width = img.size[0] - 2 * spacing
            hframes = 1
        if sprite_height > 0:
            vframes = (img.size[1] - spacing) // (sprite_height + spacing)
        else:
            sprite_height = img.size[1] - 2 * spacing
            vframes = 1

        # create byte array for bin file
        size = (sprite_height + 7) // 8 * sprite_width * hframes * vframes
        if transparency:
            size += size
        buffer = bytearray([sprite_width >> 8, sprite_width & 0xFF, sprite_height >> 8, sprite_height & 0xFF])
        buffer += bytearray(size)
        i = 4
        b = 0
        m = 0
        with open(os.path.splitext(filename)[0] + ".h", "w") as headerfile:
            headerfile.write("\n")
            headerfile.write(f"constexpr uint8_t {sprite_name}_width = {sprite_width};\n")
            headerfile.write(f"constexpr uint8_t {sprite_name}_height = {sprite_height};\n")
            headerfile.write("\n")
            headerfile.write(f"const uint8_t PROGMEM {sprite_name}[] =\n")
            headerfile.write("{\n")
            headerfile.write(f"  {sprite_name}_width, {sprite_name}_height,\n")
            fy = spacing
            for v in range(vframes):
                fx = spacing
                for h in range(hframes):
                    for y in range(0, sprite_height, 8):
                        line = "  "
                        for x in range(0, sprite_width):
                            for p in range(0, 8):
                                b = b >> 1
                                m = m >> 1
                                if (y + p) < sprite_height:  # for heights that are not a multiple of 8 pixels
                                    if pixels[(fy + y + p) * img.size[0] + fx + x][1] > 64:
                                        b |= 0x80  # white pixel
                                    if pixels[(fy + y + p) * img.size[0] + fx + x][3] == 255:
                                        m |= 0x80  # transparent pixel
                            buffer[i] = b
                            line += f"0x{b:02X}, "
                            i += 1
                            if transparency:
                                buffer[i] = m
                                line += f"0x{b:02X}, "
                                i += 1
                        lastline = (v + 1 == vframes) and (h + 1 == hframes) and (y + 8 >= sprite_height)
                        if lastline:
                            line = line[:-2]
                        headerfile.write(line + "\n")
                    if not lastline:
                        headerfile.write("\n")
                    fx += sprite_width + spacing
                fy += sprite_height + spacing
            headerfile.write("};\n")
            headerfile.close()

        # save bytearray to file (temporary code for fx datafile creation)
        with open(os.path.splitext(filename)[0] + ".bin", "wb") as binfile:
            binfile.write(buffer)
            binfile.close()


if __name__ == '__main__':
    print("\nArduboy image include converter 1.01 by Mr.Blinky May - Jun.2019\n")
    main()
