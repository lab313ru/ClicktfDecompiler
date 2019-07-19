import struct

from CTF_ByteIO import ByteIO
from Loader import DataLoader


def wrap(value):
    return value & 0xFFFFFFFF


def wrap_signed_char(value):
    value = value & 0xFF
    if value > 127:
        value -= 256
    return value


def make_checksum(data):
    result = 0
    bufferOffset = 0
    numberOfBytes = len(data)
    numberOfReads = numberOfBytes >> 2
    for _ in range(numberOfReads):
        newInt, = struct.unpack_from('<I', data, bufferOffset)
        result = newInt + (wrap(result) >> 31) + 2 * result
        result = wrap(result)
        bufferOffset += 4
    for _ in range(numberOfBytes & 3):
        v7 = (wrap(result) >> 31) + struct.unpack_from('<B', data, bufferOffset)[0]
        bufferOffset += 1
        result = wrap(v7 + 2 * result)
    return wrap(result)


GROUP_WORDS = list('mqojhm:qskjhdsmkjsmkdjhq\x63clkcdhdlkjhd')


def make_group_checksum(password, group_name):
    v4 = 57
    for c in group_name:
        v4 += ord(c) ^ 0x7F
    v5 = 0
    for c in password:
        v4 += wrap_signed_char(ord(GROUP_WORDS[v5]) + (ord(c) ^ 0xC3)) ^ 0xF3
        v5 += 1
        if v5 > len(GROUP_WORDS):
            v5 = 0
    return v4


def make_pame_checksum(data):
    checksum = make_checksum(data)
    lastByte = checksum & 0x000000FF  # get last byte
    xorByte = lastByte ^ 13
    checksum = checksum & 0xFFFFFF00 | xorByte
    return int(checksum)


class Checksum(object):
    data = None

    def __init__(self, data=None):
        if data:
            self.data = data

    def get_checksum(self):
        return make_pame_checksum(self.data)


class Protection(DataLoader):
    def __init__(self,reader:ByteIO):
        self.reader = reader
        self.checksum = None
        # self.read(self.reader)
    def read(self):
        reader = self.reader
        self.checksum = reader.read_uint32()

    def compare_data(self, data):
        real_checksum = Checksum(data).get_checksum()
        return real_checksum == self.checksum


    def set_data(self, data):
        self.checksum = Checksum(data).get_checksum()