from pprint import pformat
from typing import List

from CTF_ByteIO import ByteIO
from Loader import DataLoader
from bitdict import BitDict

graphicModes = {
    4: '16 million colors',
    7: '65536 colors',
    6: '32768 colors',
    3: '256 colors'
}
controlTypes = [
    'Joystick 1',
    'Joystick 2',
    'Joystick 3',
    'Joystick 4',
    'Keyboard'
]

HEADER_FLAGS = BitDict(
    'BorderMax',
    'NoHeading',
    'Panic',
    'SpeedIndependent',
    'Stretch',
    'MusicOn',  # obsolete?
    'SoundOn',  # obsolete?
    'MenuHidden',
    'MenuBar',
    'Maximize',  # maximized at bootup?
    'MultiSamples',
    'FullscreenAtStart',
    'FullscreenSwitch',
    'Protected',  # wonder...
    'Copyright',
    'OneFile'  # ?
)

HEADER_NEW_FLAGS = BitDict(
    'SamplesOverFrames',
    'RelocFiles',
    'RunFrame',
    'SamplesWhenNotFocused',
    'NoMinimizeBox',
    'NoMaximizeBox',
    'NoThickFrame',
    'DoNotCenterFrame',
    'ScreensaverAutostop',
    'DisableClose',
    'HiddenAtStart',
    'XPVisualThemes',
    'VSync',
    'RunWhenMinimized',
    'MDI',
    'RunWhileResizing',
)

HEADER_OTHER_FLAGS = BitDict(
    'DebuggerShortcuts',
    'DirectX',
    'VRAM',
    'Obsolete',
    'AutoImageFilter',
    'AutoSoundFilter',
    'AllInOne',  # no idea
    'ShowDebugger',
    'Reserved1',
    'Reserved2'
)


class Keys(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.up = None
        self.down = None
        self.left = None
        self.right = None
        self.button1 = None
        self.button2 = None
        self.button3 = None
        self.button4 = None

    def read(self):
        self.up = self.reader.read_int16()
        self.down = self.reader.read_int16()
        self.left = self.reader.read_int16()
        self.right = self.reader.read_int16()
        self.button1 = self.reader.read_int16()
        self.button2 = self.reader.read_int16()
        self.button3 = self.reader.read_int16()
        self.button4 = self.reader.read_int16()

    def print(self, indent=3):
        ind = '\t' * indent if indent else ''
        print(f'{ind}Keys:')
        print(f'{ind}\tUp:{self.up}')
        print(f'{ind}\tDown:{self.down}')
        print(f'{ind}\tLeft:{self.left}')
        print(f'{ind}\tRight:{self.right}')
        print(f'{ind}\tButton1:{self.button1}')
        print(f'{ind}\tButton2:{self.button2}')
        print(f'{ind}\tButton3:{self.button3}')
        print(f'{ind}\tButton4:{self.button4}')

    def __repr__(self):
        locald = {a: b for a, b in self.__dict__.items() if a != 'data'}
        return pformat(locald)


class PlayerControl(DataLoader):

    def __init__(self, reader):
        self.reader = reader
        self.controlType = 0
        self.keys = Keys(self.reader)
    def read(self):
        self.controlType = self.reader.read_int16()
        self.keys.read()

    def print(self, indent=2):
        ind = '\t' * indent if indent else ''
        print(f'{ind}PlayerControl:')
        ind = '\t' * (indent+1) if indent+1 else ''
        print(f'{ind}Control type: {self.controlType}')
        self.keys.print(indent+2)

    def __repr__(self):
        locald = {a: b for a, b in self.__dict__.items() if a != 'data'}
        return pformat(locald)


class Controls(DataLoader):
    def __init__(self, reader):
        self.reader = reader
        self.items = []  # type: List[PlayerControl]

    def read(self):
        self.items = [PlayerControl(self.reader) for _ in range(4)]
        for control in self.items:
            control.read()

    def print(self, indent=1):
        ind = '\t' * indent if indent else ''
        print(f'{ind}Controls:')
        for control in self.items:
            control.print(indent+1)

    def __repr__(self):
        locald = {a: b for a, b in self.__dict__.items() if a != 'data'}
        return pformat(locald)


class AppHeader(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.flags = HEADER_FLAGS.copy()
        self.new_flags = HEADER_NEW_FLAGS.copy()
        self.other_flags = HEADER_OTHER_FLAGS.copy()
        self.borderColor = None
        self.numberOfFrames = None
        self.frameRate = None
        self.windowsMenuIndex = None  # Index of Window menu for MDI applications

        self.graphics_mode = None

        self.windowWidth = None
        self.windowHeight = None
        self.initialScore = None
        self.initialLives = None
        self.controls = Controls(reader)
        self.checksum = None

    def read(self):
        reader = self.reader

        size = reader.read_int32()
        self.flags.setFlags(reader.read_int16())
        self.new_flags.setFlags(reader.read_int16())
        self.graphics_mode = reader.read_int16()
        self.other_flags.setFlags(reader.read_int16())
        self.windowWidth = reader.read_int16()
        self.windowHeight = reader.read_int16()
        self.initialScore = reader.read_uint32() ^ 0xffffffff
        self.initialLives = reader.read_uint32() ^ 0xffffffff
        self.controls.read()
        self.borderColor = reader.read_bytes(4)
        self.numberOfFrames = reader.read_int32()
        self.frameRate = reader.read_int32()
        self.windowsMenuIndex = reader.read_uint8()
        if not self.flags['OneFile']:
            # we're debugging, let new chunks know
            self.update_settings(debug=True)
            self.settings['debug'] = True

    def print(self):
        print(f'Flags: {self.flags}')
        print(f'Flags2: {self.new_flags}')
        print(f'Graphics mode: {self.graphics_mode}')
        print(f'Flags3: {self.other_flags}')
        print(f'Window width: {self.windowWidth}')
        print(f'Window height: {self.windowHeight}')
        print(f'Initial score: {self.initialScore}')
        print(f'Initial lives: {self.initialLives}')
        print(f'Controls:')
        self.controls.print()
        print(f'Border color: {"".join([hex(a)[2:] for a in self.borderColor])}')
        print(f'Frame count: {self.numberOfFrames}')
        print(f'FPS: {self.frameRate}')
        print(f'Windows menu index: {self.windowsMenuIndex}')


class ExtendedHeader(DataLoader):

    def __init__(self, reader):
        self.reader = reader
        self.flags = BitDict(
            'KeepScreenRatio',
            'FrameTransition',  # (HWA only) frame has a transition
            'ResampleStretch',  # (HWA only) resample while resizing
            'GlobalRefresh'  # (Mobile) force global refresh
        )
        self.buildType = None
        self.buildFlags = None
        self.screenRatioTolerance = None
        self.screenAngle = None

    def read(self):
        self.flags.setFlags(self.reader.read_int32())
        self.buildType = self.reader.read_uint32()
        self.buildFlags = self.reader.read_uint32()
        self.screenRatioTolerance = self.reader.read_int16()
        self.screenAngle = self.reader.read_int16()
        self.reader.read_int32()
        if self.buildType >= 0x10000000:
            self.update_settings(compat=True)

    def print(self):
        print(f'Flag: {self.flags}')
        print(f'Build type: {self.buildType}')
        print(f'Build flags: {self.buildFlags}')
        print(f'Screen ratio tolerance: {self.screenRatioTolerance}')
        print(f'Screen Angle: {self.screenAngle}')
