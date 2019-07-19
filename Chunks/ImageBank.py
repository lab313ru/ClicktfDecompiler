import os
from math import ceil
from typing import Dict

from PIL import Image

from CTF_ByteIO import ByteIO
from Loader import DataLoader
from ProgressBar import ProgressBar
from bitdict import BitDict

POINT_MODE = 4  # 16 million colors
FIFTEENPOINT_MODE = 6  # 32768 colors

IMAGE_FLAGS = BitDict(
    'RLE',
    'RLEW',
    'RLET',
    'LZX',
    'Alpha',
    'ACE',
    'Mac'
)


class BasePoint:
    pass


class IndexPoint(BasePoint):
    def __init__(self):
        self.size = 1

    def read(self, data, position) -> int:
        return data[position]


class Point(BasePoint):
    def __init__(self):
        self.size = 3

    def read(self, data, position):
        b = data[position]
        g = data[position + 1]
        r = data[position + 2]
        # return r | g << 8 | b << 16
        return r, g, b


class FifteenPoint(BasePoint):
    def __init__(self):
        self.size = 2

    def read(self, data, position):
        newShort = (data[position] |
                    data[position + 1] << 8)
        r = (newShort & 31744) >> 10
        g = (newShort & 992) >> 5
        b = (newShort & 31)
        r = r << 3
        g = g << 3
        b = b << 3
        return r, g, b


class SixteenPoint(BasePoint):
    def __init__(self):
        self.size = 2

    def read(self, data, position):
        # print(self.__class__,"input data len:",len(data),"possition:",position)
        newShort = (data[position] |
                    data[position + 1] << 8)
        r = (newShort & 63488) >> 11
        g = (newShort & 2016) >> 5
        b = (newShort & 31)
        r = r << 3
        g = g << 2
        b = b << 3
        # r,g,b =r , g << 8 , b << 16
        return r, g, b


index_point = IndexPoint()
point_instance = Point()
fifteen_point = FifteenPoint()
sixteen_point = SixteenPoint()


def get_padding(width, pointClass, bytes=2):
    pad = bytes - ((width * pointClass.size) % bytes)
    if pad == bytes:
        pad = 0
    return ceil(pad / pointClass.size)


def read_rle(data, width, height, pointClass):
    pad = get_padding(width, pointClass)
    currentPosition = 0
    i = 0
    pos = 0
    points = [None] * width * height * 4
    while 1:
        command = data[currentPosition]
        currentPosition += 1

        if command == 0:
            break

        if command > 128:
            command -= 128
            for n in range(command):
                if pos % (width + pad) < width:
                    points[i] = pointClass.read(data, currentPosition)
                    i += 1
                pos += 1
                currentPosition += pointClass.size
        else:
            newPoint = pointClass.read(data, currentPosition)
            for n in range(command):
                if pos % (width + pad) < width:
                    points[i] = newPoint
                    i += 1
                pos += 1
            currentPosition += pointClass.size
    return points, currentPosition


def read_rgb(data, width, height, pointClass):
    n = 0
    i = 0
    points = []
    pad = get_padding(width, pointClass)
    for y in range(height):
        for x in range(width):
            points.extend(pointClass.read(data, n))
            n += pointClass.size
            i += 1
        n += pad * pointClass.size
    return points, n


def read_alpha(data, width, height, position):
    pad = get_padding(width, index_point, 4)
    points = [None] * width * height
    n = i = 0
    for y in range(height):
        for x in range(width):
            points[i] = data[n + position]
            n += 1
            i += 1
        n += pad
    return points


class AGMIBank(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []
        self.itemDict = {}
        self.graphic_mode = 0
        self.palette_version = 0
        self.palette_entries = 0
        self.palette = 0

    def read(self):
        reader = self.reader
        self.graphic_mode = self.reader.read_int32()
        self.palette_version = self.reader.read_uint16()
        self.palette_entries = self.reader.read_uint16()
        self.palette = [[self.reader.read_uint8() for _ in range(4)]
                        for _ in range(256)]
        count = self.reader.read_int32()
        for _ in range(count):
            item = ImageItem(self.reader)
            self.items.append(item)
            self.itemDict[item.handle] = item


class ImageItem(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = IMAGE_FLAGS.copy()
        self.handle = 0
        self.position = 0
        self.checksum = 0
        self.references = 0
        self.width = 0
        self.height = 0
        self.graphic_mode = 0
        self.x_hotspot = 0
        self.y_hotspot = 0
        self.action_x = 0
        self.action_y = 0
        self.transparent = []
        self.indexed = 0
        self.image = bytes()
        self.alpha = bytes()

    def read(self):
        reader = self.reader
        self.handle = reader.read_int32()
        self.position = self.reader.tell()
        self.load()
        self.save()

    def load(self):
        reader = self.reader
        reader.seek(self.position)
        old = self.settings.get('old', False)
        if old:
            # image_data = onepointfive.decompress(reader)
            return
        else:
            image_data = reader.auto_decompress(True)
        start = image_data.tell()
        self.checksum = image_data.read_int32()
        self.references = image_data.read_int32()
        size = image_data.read_uint32()
        self.width = image_data.read_int16()
        self.height = image_data.read_int16()
        self.graphic_mode = image_data.read_int8()
        self.flags.setFlags(image_data.read_uint8())
        if not old:
            image_data.skip(2)  # imgNotUsed
        self.x_hotspot = image_data.read_int16()
        self.y_hotspot = image_data.read_int16()
        self.action_x = image_data.read_int16()
        self.action_y = image_data.read_int16()
        # if self.settings.get('VERBOSE', False):
        #     print('Found image!')
        #     print('\tsize:', f"{self.width}x{self.height}")

        if old:
            self.transparent = (0, 0, 0)
        else:
            self.transparent = [image_data.read_uint8() for _ in range(4)]

        if self.flags['LZX']:
            decompressed_size = image_data.read_uint32()
            image_data = reader.decompress_block(reader.size() - reader.tell(), decompressed_size)
        else:
            image_data = image_data.read_bytes()
        if self.graphic_mode == 2:
            point_class = index_point
            self.indexed = True
        elif self.graphic_mode == 3:
            point_class = index_point
            self.indexed = True
        elif self.graphic_mode == 4:  # 16 million colors
            point_class = point_instance
            self.indexed = False
        elif self.graphic_mode == 6:  # 32768 colors
            point_class = fifteen_point
            self.indexed = False
        elif self.graphic_mode == 7:  # 65536 colors
            point_class = sixteen_point
            self.indexed = False
        else:
            raise Exception('Unknown image type')

        data = image_data
        width, height = self.width, self.height
        if self.flags['RLE'] or self.flags['RLEW'] or self.flags['RLET']:
            image, bytes_read = read_rle(data, width, height, point_class)
            alpha_size = size - bytes_read
        else:
            image, image_size = read_rgb(data, width, height, point_class)
            alpha_size = size - image_size
        self.image = image

        if self.flags['Alpha']:
            pad = (alpha_size - width * height) / height
            self.alpha = read_alpha(data, width, height, size - alpha_size)

    def save(self):
        img = Image.frombytes('RGB', (self.width, self.height), bytes(self.image))
        if self.flags['Alpha']:
            alp = Image.frombytes("L", (self.width, self.height), bytes(self.alpha))
            img.putalpha(alp)
        ext = self.settings.get('IMAGEEXT')
        img.save(os.path.join(self.settings['dump_path'], "ImageBank", f'{self.handle}.{ext}'))
        del img
        if self.flags["Alpha"]:
            del alp
            del self.alpha
        del self.image


class ImageBank(DataLoader):
    @property
    def items(self):
        return self.images.values()

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.images = {}  # type: Dict[int,ImageItem]

    def read(self):
        reader = self.reader
        build = self.settings['build']
        print('Reading ImageBank.',end = ' ')
        number_of_items = reader.read_uint32()
        print('Total number of images:', number_of_items)
        print('Reading Images:')
        pbar = ProgressBar(max_progress= number_of_items)
        for i in range(number_of_items):
            image = ImageItem(self.reader)
            if self.settings.get('DUMPIMAGES',False) or self.settings.get('DUMPEVERYTHING',False):
                image.read()
            if build >= 284:
                image.handle -= 1
            if not self.settings.get('SAVERAM',True):
                self.images[image.handle] = image
            else:
                del image
            pbar.increment(1)
