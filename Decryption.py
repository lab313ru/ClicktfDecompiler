import binascii
import platform
import sys
from ctypes import *

from CTF_ByteIO import ByteIO
from Loader import DataLoader

split = lambda A, n=3: [A[i:i + n] for i in range(0, len(A), n)]

is_win64 = platform.architecture(executable=sys.executable, bits='', linkage='')[0] == "64bit"
if __name__ == '__main__':
    _lak_lib = r"E:\PYTHON_STUFF\CTF_ReaderV2\DecryptLib\build\Release\x64\Decrypter-x64.dll"
else:
    _lak_lib = "Decrypter-x64.dll" if is_win64 else "Decrypter-x86.dll"
LAKDLL = windll.LoadLibrary(_lak_lib)


class Decrypter(DataLoader):
    _get_key = LAKDLL.make_key
    _get_key.argtypes = [c_char_p, c_char_p, c_char_p, c_bool]
    _get_key.restype = POINTER(c_ubyte * 256)
    _decode_chunk = LAKDLL.decode_chunk
    _decode_chunk.argtypes = [c_char_p, c_int32, c_char]
    _decode_chunk.restype = POINTER(c_ubyte)

    def __init__(self):
        self.key = bytes(256)

    def generate_key(self, title, copyright, project, unicode):
        title = create_string_buffer(title.encode('ascii'))
        copyright = create_string_buffer(copyright.encode('ascii'))
        project = create_string_buffer(project.encode('ascii'))
        a = self._get_key(title, copyright, project, unicode)
        self.key = bytes(list(a.contents))

    def decode(self, chunk_data, chunk_size, magic_key=54, as_reader=False):
        decoded_chunk_pointer = self._decode_chunk(chunk_data, chunk_size, magic_key)

        decoded_chunk_pointer = cast(decoded_chunk_pointer, POINTER(c_ubyte * chunk_size))
        if as_reader:
            return ByteIO(byte_object=bytes(list(decoded_chunk_pointer.contents)))
        else:
            return bytes(list(decoded_chunk_pointer.contents))

    def print_hex(self, data):
        block_size = 16
        for block in split(data, block_size):
            char_acc = ''
            for b in block:
                if 32 < b < 128:
                    char_acc += chr(b)
                else:
                    char_acc += '.'

            b_len = len(block)
            acc_len = b_len * 2 + block_size - 1
            acc = binascii.hexlify(block)
            acc = acc.upper().decode('ascii')
            acc = ' '.join(split(acc, 2))
            if b_len == block_size:
                acc_len = len(acc)
            if b_len < block_size:
                acc += ' ' * ((acc_len - len(acc)) * 3)
            acc += '\t|\t' + char_acc
            print(acc)

    def decode_mode3(self, chunk_data, chunk_size, chunk_id, magic_key=54, as_reader=False):
        reader = ByteIO(byte_object=chunk_data)
        decompressed_size = reader.read_uint32()
        chunk_data = bytearray(reader.read_bytes())
        if chunk_id & 0x1:
            chunk_data[0] ^= (chunk_id & 0xFF) ^ (chunk_id >> 0x8)
        chunk_data = bytes(chunk_data)
        data = self.decode(chunk_data, chunk_size, magic_key, True)
        compressed_size = data.read_uint32()
        if as_reader:
            return data.decompress_block(compressed_size, decompressed_size, True)
        else:
            return data.decompress_block(compressed_size, decompressed_size, False)


if __name__ == '__main__':
    keygen = Decrypter()
    keygen.generate_key(r'Ultimate Custom Night', 'Scott Cawthon', r'C:\Users\Scott\Desktop\FNAF 6\CustomNight-151.mfa',
                        False)
    keygen.print_hex(keygen.key)
    keygen.print_hex(keygen.decode(b'\xE5\xC0\x66\x76', 4, 54))
