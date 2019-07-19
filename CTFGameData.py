from CTF_ByteIO import ByteIO
from CTF_Constants import *
from ChunkList import ChunkList
from Loader import DataLoader


class GameData(DataLoader):
    runtimeVersion = None
    runtimeSubversion = None
    productVersion = None
    productBuild = None
    chunks = None

    name = None
    author = None
    copyright = None
    aboutText = None
    doc = None

    editorFilename = None
    targetFilename = None

    exeOnly = None

    menu = None
    icon = None

    header = None
    extendedHeader = None

    fonts = None
    sounds = None
    music = None
    images = None

    globalValues = None
    globalStrings = None

    extensions = None

    frameItems = None

    frames = None
    frameHandles = None

    serial = None

    shaders = None
	
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.runtime_version = None
        self.runtime_subversion = None
        self.product_version = None
        self.product_build = None
        self.build = None
        self.chunk_list = ChunkList(self.reader)


    def read(self):
        reader = self.reader

        magic = reader.read_fourcc()
        if magic == UNICODE_GAME_HEADER:
            self.update_settings(unicode=True)
        elif magic != GAME_HEADER:
            raise Exception('Invalid GamePack header')

        self.runtime_version = reader.read_uint16()
        if self.runtime_version == CNCV1_VERSION:
            self.update_settings(cnc=True)
        self.runtime_subversion = reader.read_uint16()
        self.product_version = reader.read_int32()
        self.product_build = reader.read_int32()
        self.build = products.get(self.runtime_version, 'UNK')
        self.update_settings(build=self.product_build)
        if self.settings.get('VERBOSE', False):
            print(self)
        self.chunk_list.read()
        self.files = None
        self.chunks = chunks


    def __repr__(self):
        return f'<GameData {self.build} runtime version:{self.runtime_version}:{self.runtime_subversion} '\
               f'build:{self.product_build} version:{self.product_version}>'
