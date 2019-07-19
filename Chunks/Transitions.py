from CTF_ByteIO import ByteIO
from Loader import DataLoader
from bitdict import BitDict


class Transition(DataLoader):
    module = None
    name = None
    duration = None  # in ms
    flags = None
    color = None
    moduleFile = None
    parameterData = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.flags = BitDict('Color')

        currentPosition = self.reader.tell()
        self.module = self.reader.read(4)
        self.name = self.reader.read(4)
        self.duration = self.reader.read_int32()
        self.flags.setFlags(self.reader.read_uint32())
        self.color = [self.reader.read_uint8() for _ in range(4)]
        nameOffset = self.reader.read_int32()
        parameterOffset = self.reader.read_int32()
        parameterSize = self.reader.read_int32()
        self.reader.seek(currentPosition + nameOffset)
        self.moduleFile = self.reader.read_ascii_string()
        self.reader.seek(currentPosition + parameterOffset)
        self.parameterData = self.reader.read(parameterSize)

    def isStandard(self):
        return self.name == 'STDT'


class FadeIn(Transition):
    fadeIn = True


class FadeOut(Transition):
    fadeIn = False
