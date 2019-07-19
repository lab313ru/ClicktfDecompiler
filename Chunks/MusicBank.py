import os.path

from CTF_ByteIO import ByteIO
from Loader import DataLoader
from bitdict import BitDict


class MusicFile(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.handle = None
        self.name = None
        self.checksum = None
        self.references = None
        self.flags = BitDict(
            'Wave',
            'MIDI',
            None, None,
            'LoadOnCall',
            'PlayFromDisk',
            'Loaded'
        )
        self.data = None
        self.ext = '.mp3'

    def read(self):
        reader = self.reader
        debug = self.settings.get('debug', False)
        compressed = not debug and self.settings.get('compressed', True)
        self.handle = reader.read_int32()
        if compressed:
            reader = reader.auto_decompress(True)
        self.checksum = reader.read_uint32()
        self.references = reader.read_uint32()
        size = reader.read_uint32()
        self.flags.setFlags(reader.read_uint32())
        reserved = reader.read_int32()
        name_length = reader.read_int32()
        self.name = reader.read_wide_string(name_length)
        self.data = reader.read_bytes(size - name_length)

        if self.flags['Wave']:
            self.ext = '.wav'
        elif self.flags['MIDI']:
            self.ext = '.midi'
        if self.settings.get('DUMPMUSIC', False) or self.settings.get('DUMPEVERYTHING', False):
            self.dump()

    def dump(self):
        if self.settings.get('VERBOSE',False):
            print(f'Saving "{self.name}{self.ext}"')

        with open(os.path.join(self.settings['dump_path'], 'MusicBank', f'{self.name}{self.ext}'), 'wb') as fp:
                fp.write(self.data)
        return self


class JavaMusic(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.handle = None
        self.data = None
        self.read()

    def read(self):
        reader = self.reader
        self.handle = reader.read_uint16()
        self.data = reader.read(reader.read_uint32())
        return self


class MusicBank(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []

    def read(self):
        reader = self.reader
        print('Reading MusicBank')
        java = self.settings.get('java', False)
        debug = self.settings.get('debug', False)

        if java:
            total_references = reader.read_int16()
            number_of_items = reader.read_int16()
            item_class = JavaMusic
        else:
            number_of_items = reader.read_uint32()
            item_class = MusicFile
        if self.settings.get('VERBOSE',False):
            print('Total music files:', number_of_items, 'music class:', item_class.__name__)
        for _ in range(number_of_items):
            item = item_class(reader).read()
            if not self.settings.get('SAVERAM', True):
                self.items.append(item)
            else:
                del item

    def fromHandle(self, handle):
        return [item for item in self.items if item.handle == handle][0]
