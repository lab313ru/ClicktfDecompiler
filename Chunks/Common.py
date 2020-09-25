import byteflag
from CTF_ByteIO import ByteIO

from Loader import DataLoader

EXTENSION_BASE = 32


class Rectangle(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.left = None
        self.top = None
        self.right = None
        self.bottom = None

    def read(self):
        reader = self.reader
        self.left = reader.read_int32()
        self.top = reader.read_int32()
        self.right = reader.read_int32()
        self.bottom = reader.read_int32()

    def write(self, reader: ByteIO):
        reader.write_int32(self.left)
        reader.write_int32(self.top)
        reader.write_int32(self.right)
        reader.write_int32(self.bottom)


class Empty(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        if self.reader.read_bytes() != b'':
            raise Exception('expected empty chunk')

    @property
    def __dict__(self):
        return f'<Last chunk>'


class ObjectTypeMixin:
    def get_type(self):

        if self.object_type < EXTENSION_BASE:
            return self.object_type
        return EXTENSION_BASE

    def get_type_name(self):
        from Chunks.ObjectInfo import get_object_type
        return get_object_type(self.object_type)

    def has_object_info(self):
        return self.object_type >= 2

    def get_extension(self, extensionChunk):

        if self.get_type() != EXTENSION_BASE:
            raise Exception('type is not an extension')
        return extensionChunk.fromHandle(
            self.object_type - EXTENSION_BASE)


def get_name(object_type, num, systemDict, extensionDict):
    if object_type in systemDict and num in systemDict[object_type]:
        return systemDict[object_type][num]
    elif num in extensionDict:
        return extensionDict[num]


def is_qualifier(object_info):
    return byteflag.getFlag(object_info, 15)


def get_qualifier(object_info):
    return object_info & 0b11111111111


def get_type(self):
    if self.object_type < EXTENSION_BASE:
        return self.object_type
    return EXTENSION_BASE


class AceCommon(DataLoader):
    def get_objects(self, frameItems):
        return frameItems.fromHandle(self.object_info)

    def is_qualifier(self):
        return is_qualifier(self.object_info)

    def get_qualifier(self):
        return get_qualifier(self.object_info)

    def get_name(self):
        if self.name is None:
            self.name = get_name(self.object_type, self.num,
                                 self.systemDict, self.extensionDict)
        return self.name

    def get_type(self):
        return get_type(self)

    def get_type_name(self):
        from Chunks.ObjectInfo import get_object_type
        return get_object_type(self.object_type)

    def has_object_info(self):
        return self.object_type >= 2

    def get_extension(self, extensionChunk):
        if self.get_type() != EXTENSION_BASE:
            raise Exception('type is not an extension')
        return extensionChunk.fromHandle(
            self.object_type - EXTENSION_BASE)


class ObjectInfoMixin:
    def get_objects(self, frameItems):
        return frameItems.fromHandle(self.object_info)

    def is_qualifier(self):
        return is_qualifier(self.object_info)

    def get_qualifier(self):
        return get_qualifier(self.object_info)
