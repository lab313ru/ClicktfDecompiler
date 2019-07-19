import os

from CTF_ByteIO import ByteIO
from Loader import DataLoader


class ExtData(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.name = None
        self.data = None

    def read(self):
        if self.settings.get('old', False):
            self.name = self.reader.read_ascii_string()
            self.data = self.reader.read_bytes()
        else:
            self.data = self.reader.read_int32()
            self.reader.read_bytes()


class OtherExtensions(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.item_count = 0
        self.items = []
        self.read()

    def print(self):
        print(f'count: {self.item_count}')
        for item in self.items:
            print(f'\t{item}')
    def read(self):
        reader = self.reader
        self.item_count = reader.read_uint16()
        for _ in range(self.item_count):
            item = reader.read_wide_string()
            self.items.append(item)



class Extension(DataLoader):


    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.name = None
        self.extension = None
        self.handle = None
        self.subType = None
        self.magicNumber = None
        self.versionLS = None
        self.versionMS = None
        self.loaded = None
        
    def read(self):
        reader = self.reader
        size = self.reader.read_int16()
        if size < 0:
            size = -size
        self.handle = self.reader.read_int16()
        self.magicNumber = self.reader.read_uint32()
        self.versionLS = self.reader.read_uint32()
        self.versionMS = self.reader.read_uint32()
        self.name, self.extension = self.reader.read_wide_string().split('.')
        self.subType = self.reader.read_wide_string()




    def __repr__(self):
        return str(self.__dict__)


class ExtensionList(DataLoader):
    

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []
        self.preload_extensions = None
        
    def read(self):
        number_of_extensions = self.reader.read_int16()
        self.preload_extensions = self.reader.read_int16()
        if self.settings.get('VERBOSE',False):
            print(f'Found ExtensionList with {number_of_extensions} extensions, preload:{self.preload_extensions}')
        self.items = [Extension(self.reader)
                      for _ in range(number_of_extensions)]
        [i.read() for i in self.items]



