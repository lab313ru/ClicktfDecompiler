import os
from typing import List

from CTF_ByteIO import ByteIO
from Loader import DataLoader
from Utils import prettier_size
from bitdict import BitDict


class BaseSound(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.handle = 0
        self.name = ''
        self.data = bytes()

    def get_type(self):
        reader = ByteIO(byte_object=self.data)
        header = reader.read_fourcc()
        header2 = reader.read_fourcc()
        if header == 'RIFF':
            return 'WAV'
        elif header2 == 'AIFF':
            return 'AIFF'
        elif header == 'OggS':
            return 'OGG'
        else:
            # assume MOD
            return 'MOD'


SOUND_FLAGS = BitDict(
    'Wave',
    'MIDI',
    None, None,
    'LoadOnCall',
    'PlayFromDisk',
    'Loaded'
)


class SoundItem(BaseSound):

    def __init__(self, reader):
        super().__init__(reader)
        self.compressed = not self.settings.get('debug',False)
        self.checksum = None
        self.references = None
        self.flags = SOUND_FLAGS.copy()


    def read(self):
        reader = self.reader
        start = reader.tell()
        self.handle = reader.read_uint32()
        self.checksum = reader.read_int32()
        self.references = reader.read_int32()
        decompressed_size = reader.read_int32()
        self.flags.setFlags(reader.read_uint32())
        reserved = reader.read_int32()
        name_lenght = reader.read_int32()

        if self.compressed and not self.flags['PlayFromDisk']:
            size = reader.read_int32()
            data = reader.decompress_block(size, decompressed_size, True)
        else:
            data = ByteIO(byte_object=reader.read_bytes(decompressed_size))
        self.name = str(data.read_wide_string(name_lenght))
        self.data = data.read_bytes()
        # if self.settings.get('VERBOSE', False):
        #     print(f'Found sound file "{self.name}" size:{len(self.data)}')
        if self.settings.get('DUMPSOUNDS', False) or self.settings.get('DUMPEVERYTHING', False):
            self.dump()
        return self

    def dump(self):
        # if self.settings.get('VERBOSE'):
        #     print(f'Saving { self.name}.{self.get_type()}')
        with open(os.path.join(self.settings['dump_path'], 'SoundBank', f'{self.name}.{self.get_type()}'), 'wb') as fp:
            fp.write(self.data)


class JavaSound(BaseSound):

    def __init__(self, reader):
        super().__init__(reader)

        self.data = None

    def read(self):
        reader = self.reader
        self.handle = reader.read_int16()
        size = reader.read_int32()
        self.data = reader.read_bytes(size)
        with open(os.path.join('.', 'dump', 'SoundBank', f'{self.handle}-java.mp3'), 'wb') as fp:
            fp.write(self.data)
        return self


class FlashSound(BaseSound):
    def __init__(self, reader):
        super().__init__(reader)
        self.handle = None
        self.name = None
        self.data = None

    def read(self):
        reader = self.reader
        self.handle = reader.read_int16()
        self.name = reader.read_ascii_string(reader.read_int16())
        # with open(os.path.join('.','out',f'{self.name}.mp3'),'wb') as fp:
        #     fp.write(self.data)
        return self


#

class SoundBank(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.reference_count = 0
        self.number_of_items = 0
        self.items = [] #type: List[BaseSound]

    def print(self):
        print(f'\tSound count:{self.number_of_items}')
        for item in self.items:
            print(f'\t\tSound file "{item.name}" size:{prettier_size(item)}')


    def read(self):

        reader = self.reader

        java = self.settings.get('java', False)
        flash = self.settings.get('flash', False)
        old = self.settings.get('old', False)

        if java:
            self.reference_count = reader.read_int16()
            self.number_of_items = reader.read_int16()
            if flash:
                item_class = FlashSound
            elif old:
                item_class = None
            else:
                item_class = JavaSound
        else:
            self.number_of_items = reader.read_int32()
            if old:
                item_class = None
            else:
                item_class = SoundItem

        if not old:
            for _ in range(self.number_of_items):
                item = item_class(reader).read()
                if not self.settings.get('SAVERAM', True):
                    self.items.append(item)
                else:
                    del item

