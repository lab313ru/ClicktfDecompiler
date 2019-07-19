import os
from typing import List

from CTF_ByteIO import ByteIO
from CTF_Constants import *
from Loader import DataLoader


class PackFile(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.filename = 'ERROR'
        self.bingo = 0
        self.data = None

    def read(self):
        reader = self.reader
        self.filename = reader.read_wide_string(reader.read_uint16())
        if self.settings.get('bingo', False):
            self.bingo = reader.read_int32()
        self.data = reader.read_bytes(self.reader.read_uint32())
        if self.settings.get('VERBOSE'):
            print(f'\tFile "{self.filename}" size:{len(self.data)}')
        return self

    def dump(self):
        path = self.settings.get('PATH', '.')
        game = self.settings.get('GAME', 'GAME')
        print(f'\tWriting packed file: "{self.filename}"')
        with open(os.path.join(path, 'dump', game, "extensions", self.filename), 'wb') as pack:
            pack.write(self.data)
        return self


class PackData(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.format_version = None
        self.items = []  # type: List[PackFile]

    def read(self):
        reader = self.reader

        start = self.reader.tell()
        header = bytes(reader.read_fmt('8B'))
        if header != PACK_HEADER:
            raise NotImplementedError('CRITICAL ERROR, invalid pack header')
        header_size = reader.read_uint32()
        data_size = reader.read_uint32()

        reader.seek(start + data_size - 32)
        if reader.read_fourcc() == UNICODE_GAME_HEADER:
            self.update_settings(unicode=True)
        reader.seek(start + 16)
        self.format_version = reader.read_uint32()

        reader.skip(8)
        count = reader.read_uint32()
        if self.settings.get('VERBOSE'):
            print('Found', count, 'packed files:')
        offset = reader.tell()
        for _ in range(count):
            if not reader.check(2):
                break
            value = reader.read_uint16()
            if not reader.check(value):
                break
            reader.read_bytes(value)
            if not reader.check(4):
                break
            value = reader.read_uint32()
            if not reader.check(value):
                break
            reader.read_bytes(value)
        header = reader.read_fourcc()
        has_bingo = header not in (GAME_HEADER, UNICODE_GAME_HEADER)
        self.update_settings(bingo=has_bingo)
        reader.seek(offset)

        self.items = [PackFile(self.reader).read()
                      for _ in range(count)]

        return self
