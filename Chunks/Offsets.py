from CTF_ByteIO import ByteIO
from Loader import DataLoader


class _OffsetCommon(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []

    def read(self):
        reader = self.reader
        self.items = [reader.read_int32()
                      for _ in range(reader.size() // 4)]

    # def print(self):
    #     for offset in self.items:
    #         print(f'\t{offset}')
    #         print('\t----------')


class ImageOffsets(_OffsetCommon):
    pass


class FontOffsets(_OffsetCommon):
    pass


class SoundOffsets(_OffsetCommon):
    pass


class MusicOffsets(_OffsetCommon):
    pass
