import byteflag
from CTF_ByteIO import ByteIO
from Chunks.Key import Key
from Loader import DataLoader

itemTypes = {
    'INSERT': 0,
    'CHANGE': 128,
    'APPEND': 256,
    'DELETE': 512,
    'REMOVE': 4096,
    'BYCOMMAND': 0,
    'BYPOSITION': 1024,
    'SEPARATOR': 2048,
    'ENABLED': 0,
    'GRAYED': 1,
    'DISABLED': 2,
    'UNCHECKED': 0,
    'CHECKED': 8,
    'USECHECKBITMAPS': 512,
    'STRING': 0,
    'BITMAP': 4,
    'OWNERDRAW': 256,
    'POPUP': 16,
    'MENUBARBREAK': 32,
    'MENUBREAK': 64,
    'UNHILITE': 0,
    'HILITE': 128,
    'SYSMENU': 8192,
    'HELP': 16384,
    'MOUSESELECT': -32768,
    'END': 128
}


class AppMenuItem(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.name = ''
        self.flags = 0
        self.id = 0
        self.mnemonic = ''

    def read(self):
        reader = self.reader
        self.flags = reader.read_int16()
        if not byteflag.getFlag(self.flags, 4):  # if bit 4 is not set, read id
            self.id = reader.read_int16()
        self.name = reader.read_wide_string()
        for index in range(len(self.name)):
            if self.name[index] == '&':
                self.mnemonic = self.name[index + 1].upper()
        self.name = self.name.replace('&', '')

    def print(self, indent=1):
        ind = '\t' * indent if indent else ''
        print(f'{ind}Name: {self.name}')
        print(f'{ind}Flags: {self.flags}')
        print(f'{ind}Id: {self.id}')
        print(f'{ind}Mnemonic: {self.mnemonic}')


class AppMenu(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.header_size = 0
        self.menu_offset = 0
        self.menu_size = 0
        self.accel_offset = 0
        self.accel_size = 0
        self.items = []
        self.accelId = []
        self.accelKey = []
        self.accelShift = []

    def read(self):
        reader = self.reader
        current_position = reader.tell()
        self.header_size = reader.read_uint32()
        self.menu_offset = reader.read_int32()
        self.menu_size = reader.read_int32()
        if self.menu_size == 0:
            return
        self.accel_offset = reader.read_int32()
        self.accel_size = reader.read_int32()
        reader.seek(current_position + self.menu_offset)
        reader.skip(4)
        self.load()
        reader.seek(current_position + self.accel_offset)
        for i in range(self.accel_size // 8):
            self.accelShift.append(Key(reader.read_int8()))
            reader.skip(1)
            self.accelKey.append(Key(reader.read_int16()))
            self.accelId.append(reader.read_int16())
            reader.skip(2)

    def load(self):
        reader = self.reader
        while True:
            new_item = AppMenuItem(reader)
            new_item.read()
            self.items.append(new_item)
            if byteflag.getFlag(new_item.flags, 4):  # if bit 4 is set
                self.load()  # load inner items?
            if byteflag.getFlag(new_item.flags, 7):
                break

    def print(self):
        print(f'Header size: {self.header_size}')
        print(f'Menu offset: {self.menu_offset}')
        print(f'Menu size: {self.menu_size}')
        print(f'Accel offset: {self.accel_offset}')
        print(f'Accel size: {self.accel_size}')
        print(f'AppMenuItem:')
        for item in self.items:
            item.print()
            print()
