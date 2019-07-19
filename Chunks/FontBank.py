from CTF_ByteIO import ByteIO
from Loader import DataLoader


class LogFont(DataLoader):

    def __init__(self, reader: ByteIO, old=False):
        self.old = old
        self.reader = reader
        self.height = None
        self.width = None
        self.escapement = None
        self.orientation = None
        self.weight = None
        self.italic = None
        self.underline = None
        self.strikeOut = None
        self.charSet = None
        self.outPrecision = None
        self.clipPrecision = None
        self.quality = None
        self.pitchAndFamily = None
        self.faceName = None

    def read(self):
        reader = self.reader
        if self.settings.get('old', False) or self.old:
            read_method = reader.read_int16
        else:
            read_method = reader.read_int32
        self.height = read_method()
        self.width = read_method()
        self.escapement = read_method()
        self.orientation = read_method()
        self.weight = read_method()
        self.italic = reader.read_int8()
        self.underline = reader.read_int8()
        self.strikeOut = reader.read_int8()
        self.charSet = reader.read_int8()
        self.outPrecision = reader.read_int8()
        self.clipPrecision = reader.read_int8()
        self.quality = reader.read_int8()
        self.pitchAndFamily = reader.read_int8()
        self.faceName = reader.read_ascii_string(32)


class FontItem(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.handle = 0
        self.checksum = 0
        self.references = 0
        self.size = 0
        self.value = None

    def read(self):
        reader = self.reader
        java = self.settings.get('java', False)
        debug = self.settings.get('debug', False)
        compressed = not debug and self.settings.get('compressed', True)

        self.handle =100 
		#reader.read_uint32()

        if not java and compressed:
            new_reader = reader.auto_decompress(True)
        else:
            new_reader = reader
        currentPosition = new_reader.tell()
        self.checksum = new_reader.read_int32()
        self.references = new_reader.read_int32()
        size = new_reader.read_int32()
        self.value = self.new(LogFont, new_reader)


class FontBank(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []
        self.offsets = []

    def read(self):
        reader = self.reader
        debug = self.settings.get('debug', False)
        old = self.settings.get('old', False)

        item_count = 100 
		#reader.read_int32()

        if old:
            raise NotImplementedError('Old fonts are not supported')
        else:
            klass = FontItem

        #offset = 0
        #if self.settings['build'] >= 284 and not debug:
        offset = -1

        self.items = []
        for _ in range(item_count):
            item = self.new(klass, reader)
            item.handle += offset
            self.items.append(item)

    def fromHandle(self, handle):
        item, = [item for item in self.items if item.handle == handle]
        return item
