from CTF_ByteIO import ByteIO
from Loader import DataLoader


class StringChunk(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = ''

    def print(self):
        print(self.__class__.__name__, 'contains string', f'"{self.value}"')

    def read(self):
        reader = self.reader
        self.value = reader.read_wide_string()
        # if self.settings.get('VERBOSE',False):
        #     print(self.__class__.__name__,'contains string',f'"{self.value}"')


class AppName(StringChunk):
    pass


class AppAuthor(StringChunk):
    pass


class ExtPath(StringChunk):
    pass


class EditorFilename(StringChunk):
    pass


class TargetFilename(StringChunk):
    pass


class AppDoc(StringChunk):
    pass


class AboutText(StringChunk):
    pass


class Copyright(StringChunk):
    pass


class DemoFilePath(StringChunk):
    pass
