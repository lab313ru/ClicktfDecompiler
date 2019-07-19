import os
import sys

from CTFGameData import GameData
from CTFPackData import PackData
from CTF_ByteIO import ByteIO
from CTF_Constants import *
from Loader import DataLoader
from Bytereader import ByteReader
from Pame2mfa import translate
from Exe import ExecutableData
from Mfa import MFA


class CTFExecutale(DataLoader):

    def __init__(self, game_file: str):
        self.game_file: str = game_file
        self.update_settings(GAME=os.path.basename(game_file)[:-4])
        self.reader = reader = ByteIO(path=game_file, copy_data_from_handle=False)
        if reader.read_ascii_string(2) != 'MZ':
            raise Exception('Invalid executable signature')
        self.pack_data = None
        self.game_data = GameData(self.reader)
        

    def parse_exe(self):
        reader = self.reader
        reader.seek(60)
        hdr_offset = reader.read_uint16()
        reader.seek(hdr_offset)
        if reader.read_bytes(4) != b'PE\x00\x00':
            raise Exception('Invalid PE executable signature')
        reader.skip(2)
        num_of_sections = reader.read_uint16()
        reader.skip(16)
        optional_header = 28 + 68
        data_dir = 16 * 8
        reader.skip(optional_header + data_dir)
        possition = 0
        for i in range(num_of_sections):
            entry = reader.tell()
            section_name = reader.read_ascii_string()
            if section_name == '.extra':
                reader.seek(entry + 20)
                possition = reader.read_uint32()  # pointerToRawData
                break
            elif i >= num_of_sections - 1:
                reader.seek(entry + 16)
                size = reader.read_uint32()
                address = reader.read_uint32()
                possition = address + size
                break
            reader.seek(entry + 40)
        reader.seek(possition)
        first_short = reader.peek_int16()
        pame_magic = reader.peek_fourcc()
        pack_magic = bytes(reader.peek_fmt('8B'))

        if first_short == 8748:
            self.update_settings(old=True)
        elif pack_magic == PACK_HEADER:
            print('Found PackData header!\nReading PackData header.')
            self.pack_data = PackData(self.reader)
            self.pack_data.read()
            if self.settings.get('DUMPPACK', False) or self.settings.get('DUMPEVERYTHING', False):
                print('Dumping packed files!')
                for f in self.pack_data.items:
                    f.dump()
        elif pame_magic == GAME_HEADER:
            self.update_settings(old=True)
        else:
            raise Exception('Failed to found any known headers')

        if self.settings.get('VERBOSE', False):
            print('Reading GameData')
        self.game_data.read()

        return self
        self.dumpmfa()
    def prepare_folders(self):
        cur_path = self.settings.get('PATH', os.path.abspath("."))
        game = self.settings.get('GAME', 'game')
        dump_path = os.path.join(cur_path, 'DUMP', game)
        os.makedirs(dump_path, exist_ok=True)
        self.update_settings(dump_path=dump_path)
        input = "F:\Games\sl\SisterLocation.exe"
        os.makedirs(os.path.join(dump_path, "LOG"), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "CHUNKS"), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "CHUNKS",'OBJECTINFO'), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "CHUNKS",'FRAMES'), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "ImageBank"), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "SoundBank"), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "MusicBank"), exist_ok=True)
        os.makedirs(os.path.join(dump_path, "extensions"), exist_ok=True)
        self.dumpmfa()
        
		
		
    def dumpmfa(self):
        fp = ByteReader(open("F:\Games\sl\SisterLocation.exe", 'rb'))	
        #if input.endswith('.ccn'):
        newGame = GameData(fp)
        #else:
            #newExe = ExecutableData(fp, loadImages=True)

        newMfa = translate(newGame, print_func = "F:\Games\sl\SisterLocation.exe")
        out_path = os.path.join("F:\Games\sl\out.mfa")
        newMfa.write(ByteReader(open(out_path, 'wb')))

       #newMfa = MFA(ByteReader(open(out_path, 'rb')))
        print ('Finished!')

		


if __name__ == '__main__':
    a = CTFExecutale(sys.argv[1] if len(
        sys.argv) > 1 else r"F:\Games\sl\SisterLocation.exe")
        # sys.argv) > 1 else r"E:\SteamLibrary\steamapps\common\Ultimate Custom Night\Ultimate Custom Night.exe")
    a.update_settings(VERBOSE=True)
    a.update_settings(DUMPICON=True)
    a.update_settings(DUMPCHUNKS=True)
    a.update_settings(DUMPEVERYTHING=False)
    # a.update_settings(DUMPIMAGES=True)
    a.update_settings(IMAGEEXT='png')
    # a.update_settings(DUMPMUSIC=True)
    # a.update_settings(DUMPSOUNDS=True)
    a.update_settings(PRINTCHUNKS=True)
    a.update_settings(SAVERAM=True)
    a.update_settings(INTERACTIVECHUNKS=True)
    a.prepare_folders()
    a.parse_exe()
    print(a.settings)
