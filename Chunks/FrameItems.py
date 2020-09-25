from CTF_ByteIO import ByteIO
from Chunks.ObjectInfo import ObjectInfo

from Loader import DataLoader


class FrameItems(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.itemDict = {}
        self.names = []

    def read(self, ):
        reader = self.reader
        itemDict = self.itemDict
        for _ in range(reader.read_int32()):
            item = ObjectInfo(reader)
            item.read()
            itemDict[item.handle] = item
            self.names.append(item.name)

    def fromHandle(self, handle):
        return self.itemDict[handle]
