from CTF_ByteIO import ByteIO
from Loader import DataLoader


class SecNum(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.tick_count = 0
        self.serial_slice = 0

    def read(self):
        eax = self.reader.read_int32()
        ecx = self.reader.read_int32()

        tick_count = eax ^ 0xBD75329

        serial_slice = ecx + eax
        serial_slice ^= 0xF75A3F
        serial_slice ^= eax
        serial_slice -= 10

        self.tick_count = tick_count
        self.serial_slice = serial_slice
