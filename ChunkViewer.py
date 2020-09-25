import binascii
import traceback
from pprint import pformat

from CTF_ByteIO import ByteIO

split = lambda A, n=3: [A[i:i + n] for i in range(0, len(A), n)]


class ChunkViewer:
    shell_globals = {}
    shell_locals = {}

    @classmethod
    def get_locals(cls):
        return cls.shell_locals

    @classmethod
    def update_locals(cls, shell_locals):
        cls.shell_locals.update(shell_locals)

    @classmethod
    def get_globals(cls):
        return cls.shell_globals

    @classmethod
    def update_globals(cls, shell_globals):
        cls.shell_globals.update(shell_globals)

    def __init__(self, raw_chunk_data: bytes, chunk):
        self.data = raw_chunk_data
        self.chunk = chunk

    def print_help(self):
        print('=====HELP=====')
        print('\t help or -h to display help')
        print('\t quit or -q or exit to exit ChunkViewer')
        print('\t raw or praw to print HEX representation of chunk')
        print('\t pchunk or chunk to print chunk loader data')
        print('\t shell or py to run python console')

    def print_chunk(self):
        print('=====CHUNK LOADER DATA=====')
        if hasattr(self.chunk, 'print'):
            getattr(self.chunk, 'print')()
        else:
            for name, value in self.chunk.__dict__.items():
                print(f'{name} : {pformat(value, indent=2, compact=True)}')

    def parse_command(self, raw_command, aliases):
        for allias in aliases:
            if allias == raw_command:
                return True
        return False

    def print_raw(self):
        block_size = 32
        for block in split(self.data, block_size):
            char_acc = ''
            for b in block:
                if b < 32:
                    char_acc += ' '
                    continue
                try:
                    char_acc += chr(b)
                except:
                    char_acc += ' '

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

    def run_shell(self):
        print('Local variables:')
        print('\t data - raw chunk data')
        print('\t chunk - chunk loader object')
        print('\t reader - ByteIO reader object with raw data')
        print('Local functions')
        print('\t raw() - prints HEX representation of chunk')
        print('\t pchunk() - print chunk loader data')

        while True:
            try:
                locals_ = self.get_locals()
                globals_ = self.get_globals()
                locals_['data'] = self.data
                locals_['reader'] = ByteIO(byte_object=self.data)
                locals_['chunk'] = self.chunk
                locals_['raw'] = self.print_raw
                locals_['pchunk'] = self.print_chunk
                code = input('>>')
                if code == 'exit':
                    print('Exiting shell')
                    return
                compiled_code = compile(code, "iPy", 'single')
                exec(compiled_code, globals_, locals_)
                self.update_locals(locals_)
                self.update_globals(globals_)
            except KeyboardInterrupt:
                print('Keyboard Interruption, exiting shell')
                return
            except Exception as ex:
                traceback.print_exc()

    def start(self):
        while True:
            self.print_help()
            command = input('>>')
            if self.parse_command(command, ['help', '-h']):
                self.print_help()

            elif self.parse_command(command, ['exit', '-q', 'quit']):
                break

            elif self.parse_command(command, ['pchunk', '-pcnk', 'chunk', '-p']):
                self.print_chunk()

            elif self.parse_command(command, ['praw', 'raw', '-r']):
                self.print_raw()

            elif self.parse_command(command, ['shell', 'py']):
                self.run_shell()

            else:
                print('Unrecognized command!')


if __name__ == '__main__':
    pass
