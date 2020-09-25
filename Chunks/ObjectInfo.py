from Chunks.Objects import *
from Chunks.StringChunks import StringChunk
from Loader import DataLoader
from bitdict import BitDict

EXTENSION_BASE = 32

objectTypes = {
    -7: 'Player',
    -6: 'Keyboard',
    -5: 'Create',
    -4: 'Timer',
    -3: 'Game',
    -2: 'Speaker',
    -1: 'System',
    0: 'QuickBackdrop',
    1: 'Backdrop',
    2: 'Active',
    3: 'Text',
    4: 'Question',
    5: 'Score',
    6: 'Lives',
    7: 'Counter',
    8: 'RTF',
    9: 'SubApplication'
}

NONE_EFFECT = 0
SEMITRANSPARENT_EFFECT = 1
INVERTED_EFFECT = 2
XOR_EFFECT = 3
AND_EFFECT = 4
OR_EFFECT = 5
REPLACE_TRANSPARENT_EFFECT = 6
DWROP_EFFECT = 7
ANDNOT_EFFECT = 8
ADD_EFFECT = 9
MONOCHROME_EFFECT = 10
SUBTRACT_EFFECT = 11
NO_REPLACE_EFFECT = 12
SHADER_EFFECT = 13

HWA_EFFECT = 0x1000  # BOP_RGBAFILTER

INK_EFFECTS = {
    NONE_EFFECT: 'None',
    SEMITRANSPARENT_EFFECT: 'Semitransparent',
    INVERTED_EFFECT: 'Inverted',
    XOR_EFFECT: 'XOR',
    AND_EFFECT: 'AND',
    OR_EFFECT: 'OR',
    ADD_EFFECT: 'Add',
    MONOCHROME_EFFECT: 'Monochrome',
    SUBTRACT_EFFECT: 'Subtract',
    SHADER_EFFECT: 'Shader',
    HWA_EFFECT: 'HWA'
}

OBJECT_FLAGS = BitDict(
    'LoadOnCall',
    'Discardable',
    'Global',
    'Reserved_1'
)
(PLAYER, KEYBOARD, CREATE, TIMER, GAME, SPEAKER,
 SYSTEM, QUICKBACKDROP, BACKDROP, ACTIVE, TEXT,
 QUESTION, SCORE, LIVES, COUNTER, RTF, SUBAPPLICATION) = range(-7, 10)


def get_object_type(id):
    if id < EXTENSION_BASE:
        return objectTypes[id]
    else:
        return 'Extension'


class ObjectName(StringChunk):
    pass


class ObjectEffects(DataLoader):
    items = None

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.id = 0
        self.items = []

    def read(self):
        self.id = self.reader.read_int32()
        self.items = [self.reader.read_bytes(4)
                      for _ in range(self.reader.read_int32())]


class ObjectProperties(DataLoader, ObjectTypeMixin):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.loader = None
        self.objectType = None
        self.isCommon = None
        self._loadReader = None

    def read(self, objectType=0):
        self.objectType = objectType
        reader = self.reader
        reader.seek(0)

        self.isCommon = False
        if objectType == QUICKBACKDROP:
            self.loader = QuickBackdrop(self.reader)
        elif objectType == BACKDROP:
            self.loader = Backdrop(self.reader)
        else:
            self.isCommon = True
            self.loader = ObjectCommon(self.reader, parent=self)


class ObjectHeader(DataLoader, ObjectTypeMixin):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.handle = 0
        self.objectType = 0
        self.flags = OBJECT_FLAGS.copy()
        # self.flags = bitdict.BitDict().setFlags(self.reader.read_uint16())
        self.inkEffect = 0
        self.inkEffectParameter = 0

    def read(self):
        self.handle = self.reader.read_int16()
        self.objectType = self.reader.read_int16()
        self.flags.setFlags(self.reader.read_uint16())
        # self.flags = bitdict.BitDict().setFlags(self.reader.read_uint16())
        reserved = self.reader.read_int16()  # no longer used
        self.inkEffect = self.reader.read_uint32()
        self.inkEffectParameter = self.reader.read_uint32()


class ObjectInfo(DataLoader, ObjectTypeMixin):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.chunks = []
        self.properties = 0
        self.name = ''
        self.handle = 0
        self.objectType = 0
        self.flags = 0
        self.transparent = 0
        self.antialias = 0
        self.inkEffect = 0
        self.inkEffectValue = 0
        self.shaderId = 0
        self.items = 0

    def read(self):
        from ChunkList import ChunkList
        reader = self.reader
        infoChunks = ChunkList(self.reader)
        infoChunks.verbose = False
        infoChunks.read()
        self.properties = None
        for chunk in infoChunks.chunks:
            loader = chunk.loader
            klass = loader.__class__
            if klass is ObjectName:
                self.name = loader.value
            elif klass is ObjectHeader:
                self.handle = loader.handle
                self.objectType = loader.objectType
                self.flags = loader.flags
                inkEffect = loader.inkEffect
                self.transparent = byteflag.getFlag(inkEffect, 28)
                self.antialias = byteflag.getFlag(inkEffect, 29)
                self.inkEffect = inkEffect & 0xFFFF
                self.inkEffectValue = loader.inkEffectParameter
            elif klass is ObjectProperties:
                properties = loader
            elif klass is ObjectEffects:
                self.shaderId = loader.id
                self.items = loader.items

        if self.properties:
            self.properties.read(self.objectType)

        for chunk in infoChunks.chunks:
            try:
                os.makedirs(os.path.join(self.settings['dump_path'], 'CHUNKS', 'OBJECTINFO', self.name), exist_ok=True)
                with open(os.path.join(self.settings['dump_path'], 'CHUNKS', 'OBJECTINFO', self.name,
                                       f'{chunk.name}.chunk'), 'wb') as fp:
                    a = chunk.raw_data
                    fp.write(a)
            except:
                pass
