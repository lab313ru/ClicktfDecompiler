import os
import traceback
from enum import IntEnum
from typing import List

import Decryption
from CTF_Constants import *
from ChunkViewer import ChunkViewer
from Chunks.AppHeader import AppHeader, ExtendedHeader
from Chunks.AppMenu import AppMenu
from Chunks.ExternalData import ExtData, OtherExtensions, ExtensionList
from Chunks.Frame import Frame, FrameName, FrameHandles, FrameHeader, VirtualSize, Layers
from Chunks.FrameItems import FrameItems
from Chunks.ImageBank import ImageBank
from Chunks.MusicBank import MusicBank
from Chunks.ObjectInfo import ObjectName, ObjectHeader, ObjectProperties
from Chunks.Offsets import *
from Chunks.Protection import Protection
from Chunks.SecNum import SecNum
from Chunks.SoundBank import SoundBank
from Chunks.StringChunks import *
from Chunks.Transitions import FadeIn, FadeOut
from Chunks.yves import BinaryFiles, AppIcon
from Loader import DataLoader
from Utils import prettier_size


class Plug:

    def __init__(self, reader: ByteIO):
        pass

    def read(self):
        pass


class ChunkFlags(IntEnum):
    NOT_COMPRESSED = 0
    COMPRESSED = 1
    ENCRYPTED = 2
    COMPRESSED_AND_ENCRYPTED = 3


class Chunk(DataLoader):
    def __init__(self, reader: ByteIO, uid, chunk_list: 'ChunkList'):
        self.chunk_list = chunk_list
        self.verbose = True
        self.reader = reader
        self.uid = uid
        self.id = 0
        self.name = 'UNKNOWN'
        self.loader = None
        self.raw_data = bytes()
        self.flag = ChunkFlags(0)
        self.raw_flag = 0
        self.size = 0
        self.decompressed_size = 0
        self.entry = 0

    def build_key(self):
        if not self.settings.get('DECYPTER', False):
            decrypter = Decryption.Decrypter()
            title = ''
            copyright = ''
            project = ''
            if self.chunk_list.get_chunk(AppName):
                title = self.chunk_list.get_chunk(AppName).value
            if self.chunk_list.get_chunk(Copyright):
                copyright = self.chunk_list.get_chunk(Copyright).value
            if self.chunk_list.get_chunk(EditorFilename):
                project = self.chunk_list.get_chunk(EditorFilename).value
            unicode = self.settings.get('UNICODE', False)
            decrypter.generate_key(title, copyright, project, unicode)
            self.update_settings(DECYPTER=decrypter)
            print('New key!')
            decrypter.print_hex(decrypter.key)
            if self.verbose:
                print('Warning! This chunk is encrypted and cannot be extracted!')

    def read(self):
        reader = self.reader

        self.id = reader.read_int16()
        self.name = chunk_names.get(self.id, f'UNKNOWN-{self.id}')
        self.loader = chunk_loaders.get(self.id, Plug)
        self.raw_flag = reader.read_int16()
        self.flag = ChunkFlags(self.raw_flag)
        self.size = reader.read_int32()

        if self.raw_flag == ChunkFlags.ENCRYPTED:

            decrypter = self.settings.get('DECYPTER', False)
            if not decrypter:
                print('NO DECRYPTOR DEFINED ERROR')
                raise Exception('NO DECRYPTOR DEFINED')
            chunk_data = decrypter.decode(reader.read_bytes(self.size), self.size, as_reader=True)
            self.decompressed_size = len(chunk_data)

        elif self.raw_flag == ChunkFlags.COMPRESSED_AND_ENCRYPTED:
            decrypter = self.settings.get('DECYPTER', False)
            if not decrypter:
                print('NO DECRYPTOR DEFINED ERROR')
                raise Exception('NO DECRYPTOR DEFINED')
            chunk_data = decrypter.decode_mode3(reader.read_bytes(self.size), self.size, self.id, as_reader=True)
            self.decompressed_size = len(chunk_data)

        elif self.raw_flag == ChunkFlags.COMPRESSED:
            chunk_data = reader.auto_decompress(True)

        else:
            chunk_data = ByteIO(byte_object=reader.read_bytes(self.size))
            self.decompressed_size = chunk_data.size()
        if self.settings.get('INTERACTIVECHUNKS', False):
            with chunk_data.save_current_pos():
                if self.size > 20000000:
                    if self.verbose:
                        print('Chunk is too big for live preview')
                    self.raw_data = bytes()
                else:
                    self.raw_data = chunk_data.read_bytes()
        if self.settings.get('DUMPEVERYTHING', False) or self.settings.get('DUMPCHUNKS', False):
            with open(os.path.join(self.settings['dump_path'], 'CHUNKS', f'{self.name}.chunk'), 'wb') as fp:
                with chunk_data.save_current_pos():
                    fp.write(chunk_data.read_bytes())
        # print(self.loader)
        self.decompressed_size = len(chunk_data)
        self.loader = self.loader(chunk_data)

        self.entry = reader.tell()
        if self.chunk_list.get_chunk(EditorFilename):
            self.build_key()

    def load(self):
        try:
            self.loader.read()
        except Exception as Ex:
            print(f'Failed to load chunk {self.name} {self.id}')
            print(traceback.print_exc())
            input('Press enter to continue...')

    def __repr__(self):
        return f'<Chunk {self.name} size:{self.size} flag:{self.flag.name}>'

    def print(self):
        print(f'Chunk {self.name}:')
        print(f'    ID: {self.id} ({hex(self.id)})')
        print(f'    FLAGS: {self.raw_flag} {self.flag.name}')
        print(f'    LOADER: {self.loader.__class__.__name__}')
        print(f'    SIZE: {self.size}')
        print(f'    DECOMPRESSED SIZE: {self.decompressed_size}')
        print(f'    Pretty SIZE: {prettier_size(self.size)}')
        print(f'    Pretty DECOMPRESSED SIZE: {prettier_size(self.decompressed_size)}')

    def print_chunk_data(self):
        if self.settings.get('PRINTCHUNKS', False) and hasattr(self.loader, 'print'):
            print('======CHUNK DATA=======')
            getattr(self.loader, 'print')()
        print()


class ChunkList(DataLoader):
    chunks_to_watch = []

    @classmethod
    def get_chunks_to_watch(cls):
        return cls.chunks_to_watch

    @classmethod
    def set_chunks_to_watch(cls, chunks):
        cls.chunks_to_watch = chunks

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.verbose = True
        self.chunks = []  # type: List[Chunk]
        self.read_later = []  # type: List[Chunk]

    def interactive_mode(self):
        if self.settings.get('INTERACTIVECHUNKS', False) and self.get_chunks_to_watch() == []:
            print('Interactive chunks are enabled!\nPlease input chunks that you want to examine!')
            raw_inp = input('Chunk IDs to monitor >>').upper()
            if raw_inp:

                if raw_inp == 'ALL':
                    chunks = [-1]
                else:
                    if '0X' in raw_inp:
                        chunks = []
                        for chunk in raw_inp.split(' '):
                            chunk = eval(chunk)
                            chunks.append(chunk)
                    else:
                        chunks = list(map(int, raw_inp.split(' ')))
            else:
                chunks = [0]
            self.set_chunks_to_watch(chunks)

    def read(self):
        if self.settings.get('INTERACTIVECHUNKS', False):
            self.interactive_mode()
        chunks = self.get_chunks_to_watch()
        reader = self.reader
        while reader:
            chunk = Chunk(reader, len(self.chunks), self)
            chunk.verbose = self.verbose
            chunk.read()
            if self.verbose:
                chunk.print()
            # if chunk.id != 13117:
            chunk.load()
            if self.verbose:
                chunk.print_chunk_data()
            if self.settings.get('INTERACTIVECHUNKS', False):
                if chunk.id in chunks or chunks[0] == -1:
                    viewer = ChunkViewer(chunk.raw_data, chunk.loader)
                    viewer.start()
            if self.verbose:
                print('-' * 20)
                print()
            self.chunks.append(chunk)
            if chunk.id == 32639:
                break

    def get_chunk(self, chunk_type):
        for chunk in self.chunks:
            if type(chunk.loader) == chunk_type:
                return chunk.loader
        return None


chunk_loaders = {
    # 4386: 'all.VitalizePreview',  # Preview 0x1122
    8739: AppHeader,  #
    8740: AppName,  #
    8741: AppAuthor,
    8742: AppMenu,
    8743: ExtPath,
    # 8745: FrameItems,  # FrameItems
    8747: FrameHandles,  # FrameHandles
    8748: ExtData,  # ExtData
    8750: EditorFilename,  # AppEditorFilename
    8751: TargetFilename,  # AppTargetFilename
    8752: AppDoc,  # AppDoc
    8753: OtherExtensions,  # OtherExts
    # 8754: 'all.GlobalValues',
    # 8755: "global_data.GlobalStrings",  # GlobalStrings
    8756: ExtensionList,  # Extensions2
    8757: AppIcon,  # AppIcon_16x16x8
    # 8758: 'createPreservingLoader()',  # DemoVersion
    8759: SecNum,  # serial number
    8760: BinaryFiles,  # BinaryFiles
    # 8761: 'createPreservingLoader()',  # AppMenuImages
    8762: AboutText,  # AboutText
    8763: Copyright,  # Copyright
    # 8764: 'createPreservingLoader()',  # GlobalValueNames
    # 8765: 'GlobalStringNames',  # GlobalStringNames
    # 8766: 'all.MovementExtensions',  # MvtExts
    8767: FrameItems,  # FrameItems_2
    # 8768: application.ExeOnly,  # EXEOnly
    8770: Protection,
    # 8771: 'all.Shaders',  # Shaders
    8773: ExtendedHeader,  # ExtendedHeader aka APPHEADER2
    13107: Frame,  # Frame
    13108: FrameHeader,  # FrameHeader
    13109: FrameName,  # FrameName
    # 13110: FramePassword,  # FramePassword
    # 13111: FramePalette,  # FramePalette
    # 13112: ObjectInstances,  # FrameItemInstances
    # 13113: 'createPreservingLoader()',  # FrameFadeInFrame
    # 13114: 'createPreservingLoader()',  # FrameFadeOutFrame
    13115: FadeIn,  # FrameFadeIn
    13116: FadeOut,  # FrameFadeOut
    # 13117: Events,  # FrameEvents
    # 13118: 'createPreservingLoader()',  # FramePlayHeader
    # 13119: 'createPreservingLoader()',  # Additional_FrameItem
    # 13120: 'createPreservingLoader()',  # Additional_FrameItemInstance
    13121: Layers,  # FrameLayers
    13122: VirtualSize,  # FrameVirtualRect
    # 13123: 'all.DemoFilePath',  # DemoFilePath
    # 13124: PreservingLoader(),  # RandomSeed
    # 13125: 'all.LayerEffects',  # FrameLayerEffects
    # 13126: PreservingLoader(),  # BluRayFrameOptions
    # 13127: 'all.MovementTimerBase',  # MvtTimerBase
    # 13128: 'createPreservingLoader()',  # MosaicImageTable
    # 13129: 'all.FrameEffects',  # FrameEffects
    # 13130: PreservingLoader(),  # FrameIphoneOptions
    17476: ObjectHeader,  # ObjInfoHeader
    17477: ObjectName,
    17478: ObjectProperties,  # ObjectsCommon
    # 17479: 'createPreservingLoader()',  # ObjectUnknown
    # 17480: 'all.ObjectEffects',  # ObjectUnknown2
    21845: ImageOffsets,  # ImagesOffsets
    21846: FontOffsets,  # FontsOffsets
    21847: SoundOffsets,  # SoundsOffsets
    21848: MusicOffsets,  # MusicsOffsets
    26214: ImageBank,  # Images
    # 26215: FontBank,
    26216: SoundBank,
    26217: MusicBank,  # Musics
    # 32639: last.Last,  # Last
}
