import os

from PIL import Image

import byteflag
from CTF_ByteIO import ByteIO
from Loader import DataLoader


class BinaryItem(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.name = None
        self.data = None

    def read(self):
        reader = self.reader
        self.name = reader.read_wide_string(reader.read_uint16())
        self.data = reader.read_bytes(reader.read_uint16())


class BinaryFiles(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []

    def read(self):
        reader = self.reader
        count = reader.read_uint32()
        if self.settings.get('VERBOSE', False):
            print(f'Found {count} BinaryFiles!')
        self.items = [BinaryItem(reader)
                      for _ in range(count)]


class AppIcon(DataLoader):
    width = 16
    height = 16

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.points = None
        self.alpha = []

    def read(self):
        print('Dumping app icon')
        reader = self.reader
        reader.read_bytes(reader.read_int32() - 4)
        color_indexes = []
        for _ in range(16 * 16):
            b = self.reader.read_uint8()
            g = self.reader.read_uint8()
            r = self.reader.read_uint8()
            self.reader.read_int8()
            color_indexes.append((r, g, b))
        self.points = []
        for y in range(16):
            x_list = []
            for x in range(16):
                x_list.extend(color_indexes[self.reader.read_uint8()])
            self.points = x_list + self.points
        for _ in range(16 * 16 // 8):
            new_alphas = byteflag.getFlags(self.reader.read_uint8(), *range(8))
            for item in reversed(new_alphas):
                if item:
                    # is transparent
                    self.alpha.append(0)
                else:
                    # is opaque
                    self.alpha.append(255)
        if self.settings.get('DUMPICON',False) or self.settings.get('DUMPEVERYTHING',False):
            self.dump()

    def dump(self):
        path = os.path.join(self.settings.get('dump_path'), 'icon.png')
        alpha = Image.frombytes('L', (self.width, self.height), bytes(self.alpha))
        img = Image.frombytes('RGB', (self.width, self.height), bytes(self.points))
        img.convert('RGBA')
        img.putalpha(alpha)
        img.save(path)
