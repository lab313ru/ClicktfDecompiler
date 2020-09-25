from CTF_ByteIO import ByteIO
from Chunks.Common import AceCommon
from Loader import DataLoader

systemDict = {
    0: {  # operators
        0: 'End',
        2: 'Plus',
        4: 'Minus',
        6: 'Multiply',
        8: 'Divide',
        10: 'Modulus',
        12: 'Power',
        14: 'AND',
        16: 'OR',
        18: 'XOR'
    },
    2: {
        80: 'GetColorAt',
        81: 'GetXScale',
        82: 'GetYScale',
        83: 'GetAngle'
    },
    3: {
        80: 'CurrentParagraphIndex',
        81: 'CurrentText',
        82: 'GetParagraph',
        83: 'TextAsNumber',
        84: 'ParagraphCount'
    },
    7: {
        80: 'CounterValue',
        81: 'CounterMinimumValue',
        82: 'CounterMaximumValue',
        83: 'CounterColor1',
        84: 'CounterColor2'
    },
    8: {
        80: 'RTFXPOS',
        81: 'RTFYPOS',
        82: 'RTFSXPAGE',
        83: 'RTFSYPAGE',
        84: 'RTFZOOM',
        85: 'RTFWORDMOUSE',
        86: 'RTFWORDXY',
        87: 'RTFWORD',
        88: 'RTFXWORD',
        89: 'RTFYWORD',
        90: 'RTFSXWORD',
        91: 'RTFSYWORD',
        92: 'RTFLINEMOUSE',
        93: 'RTFLINEXY',
        94: 'RTFXLINE',
        95: 'RTFYLINE',
        96: 'RTFSXLINE',
        97: 'RTFSYLINE',
        98: 'RTFPARAMOUSE',
        99: 'RTFPARAXY',
        100: 'RTFXPARA',
        101: 'RTFYPARA',
        102: 'RTFSXPARA',
        103: 'RTFSYPARA',
        104: 'RTFXWORDTEXT',
        105: 'RTFYWORDTEXT',
        106: 'RTFXLINETEXT',
        107: 'RTFYLINETEXT',
        108: 'RTFXPARATEXT',
        109: 'RTFYPARATEXT',
        110: 'RTFMEMSIZE',
        111: 'RTFGETFOCUSWORD',
        112: 'RTFGETHYPERLINK'
    },
    9: {
        80: 'SubApplicationFrameNumber',
        81: 'SubApplicationGlobalValue',
        82: 'SubApplicationGlobalString'
    },
    -2: {
        0: 'GetMainVolume',
        1: 'GetSampleVolume',
        2: 'GetChannelVolume',
        3: 'GetMainPan',
        4: 'GetSamplePan',
        5: 'GetChannelPan',
        6: 'GetSamplePosition',
        7: 'GetChannelPosition',
        8: 'GetSampleDuration',
        9: 'GetChannelDuration',
        10: 'GetSampleFrequency',
        11: 'GetChannelFrequency'
    },
    -7: {
        0: 'PlayerScore',
        1: 'PlayerLives',
        2: 'PlayerInputDevice',
        3: 'PlayerKeyName',
        4: 'PlayerName'
    },
    -6: {
        0: 'XMouse',
        1: 'YMouse',
        2: 'MouseWheelValue'
    },
    -5: {
        0: 'TotalObjectCount'
    },
    -4: {
        0: 'TimerValue',
        1: 'TimerHundreds',
        2: 'TimerSeconds',
        3: 'TimerHours',
        4: 'TimerMinutes',
        5: 'TimerEventIndex'
    },
    -3: {
        0: 'CurrentFrameOld',
        1: 'PlayerCount',
        2: 'XLeftFrame',
        3: 'XRightFrame',
        4: 'YTopFrame',
        5: 'YBottomFrame',
        6: 'FrameWidth',
        7: 'FrameHeight',
        8: 'CurrentFrame',
        9: 'GetCollisionMask',
        10: 'FrameRate',
        11: 'GetVirtualWidth',
        12: 'GetVirtualHeight',
        13: 'FrameBackgroundColor',
        14: 'DisplayMode',
        15: 'PixelShaderVersion',
        16: 'FrameAlphaCoefficient',
        17: 'FrameRGBCoefficient',
        18: 'FrameEffectParameter'
    },
    -1: {
        0: 'Long',
        1: 'Random',
        2: 'GlobalValueExpression',
        3: 'String',
        4: 'ToString',
        5: 'ToNumber',
        6: 'ApplicationDrive',
        7: 'ApplicationDirectory',
        8: 'ApplicationPath',
        9: 'ApplicationFilename',
        10: 'Sin',
        11: 'Cos',
        12: 'Tan',
        13: 'SquareRoot',
        14: 'Log',
        15: 'Ln',
        16: 'Hex',
        17: 'Bin',
        18: 'Exp',
        19: 'LeftString',
        20: 'RightString',
        21: 'MidString',
        22: 'StringLength',
        23: 'Double',
        24: 'GlobalValue',
        28: 'ToInt',
        29: 'Abs',
        30: 'Ceil',
        31: 'Floor',
        32: 'Acos',
        33: 'Asin',
        34: 'Atan',
        35: 'Not',
        36: 'DroppedFileCount',
        37: 'DroppedFilename',
        38: 'GetCommandLine',
        39: 'GetCommandItem',
        40: 'Min',
        41: 'Max',
        42: 'GetRGB',
        43: 'GetRed',
        44: 'GetGreen',
        45: 'GetBlue',
        46: 'LoopIndex',
        47: 'NewLine',
        48: 'Round',
        49: 'GlobalStringExpression',
        50: 'GlobalString',
        51: 'LowerString',
        52: 'UpperString',
        53: 'Find',
        54: 'ReverseFind',
        55: 'GetClipboard',
        56: 'TemporaryPath',
        57: 'TemporaryBinaryFilePath',
        58: 'FloatToString',
        59: 'Atan2',
        60: 'Zero',
        61: 'Empty',
        62: 'DistanceBetween',
        63: 'AngleBetween',
        64: 'ClampValue',
        65: 'RandomRange',
        -1: 'Parenthesis',
        -3: 'Virgule',
        -2: 'EndParenthesis'
    }
}

extensionDict = {
    1: 'YPosition',
    2: 'AnimationFrame',
    3: 'Speed',
    4: 'GetAcceleration',
    5: 'GetDeceleration',
    6: 'GetDirection',
    7: 'ObjectLeft',
    8: 'ObjectRight',
    9: 'ObjectTop',
    10: 'ObjectBottom',
    11: 'XPosition',
    12: 'FixedValue',
    13: 'GetFlag',
    14: 'AnimationNumber',
    15: 'ObjectCount',
    16: 'AlterableValue',
    17: 'SemiTransparency',
    18: 'MovementNumber',
    19: 'AlterableString',
    20: 'FontName',
    21: 'FontSize',
    22: 'FontColor',
    23: 'ObjectLayer',
    24: 'GetGravity',
    25: 'ActionX',
    26: 'ActionY',
    27: 'AlphaCoefficient',  # HWA
    28: 'RGBCoefficient',  # HWA
    29: 'EffectParameter',  # HWA
    30: 'AlterableValueIndex',
    31: 'AlterableStringIndex',
    32: 'ObjectDistanceBetween',
    33: 'ObjectAngleBetween',
    34: 'ObjectLoopIndex',
    35: 'RigidbodyFriction',
    36: 'RigidbodyRestitution',
    37: 'RigidbodyDensity',
    38: 'RigidbodyVelocity',
    39: 'RigidbodyAngle',
    40: 'GetWidth',
    41: 'GetHeight'
}


class String(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = 0

    def read(self):
        reader = self.reader
        self.value = reader.read_ascii_string()

    def write(self, reader: ByteIO):
        reader.write_ascii_string(self.value)


class Long(String):

    def read(self):
        reader = self.reader
        self.value = reader.read_int32()

    def write(self, reader: ByteIO):
        reader.write_int32(self.value)


class Double(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = 0
        self.floatValue = 0

    def read(self):
        reader = self.reader
        self.value = reader.read_double()
        self.floatValue = reader.read_float()

    def write(self, reader: ByteIO):
        reader.write_double(self.value)
        reader.write_float(self.floatValue)


class GlobalCommon(String):

    def read(self):
        reader = self.reader
        # Oi et OIlist qui servent a rien
        # I does not translate. Sorry. Failure. :(
        reader.skip(4)
        self.value = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_bytes('\x00' * 4)
        reader.write_int16(self.value)


class GlobalString(GlobalCommon):
    pass


class GlobalValue(GlobalCommon):
    pass


class ExtensionCommon(String):

    def read(self):
        reader = self.reader
        self.value = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_int16(self.value)


class ExtensionString(ExtensionCommon):
    pass


class ExtensionValue(ExtensionCommon):
    pass


system_loaders = {
    -1: {
        0: Long,
        3: String,
        23: Double,
        24: GlobalValue,
        50: GlobalString
    }
}

extensionLoaders = {
    16: ExtensionValue,
    19: ExtensionString
}


class Expression(AceCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.systemDict = systemDict
        self.extensionDict = extensionDict
        self.object_info = 0
        self.num = 0
        self.object_type = 0
        self.object_info_list = []
        self.loader = None

    def read(self):
        reader = self.reader
        current_position = reader.tell()
        self.object_type = reader.read_int16()
        self.num = reader.read_int16()
        if self.object_type == 0 and self.num == 0:
            return
        size = reader.read_uint16()
        if self.object_type in system_loaders and self.num in system_loaders[self.object_type]:
            self.loader = self.new(
                system_loaders[self.object_type][self.num], reader)
        elif self.object_type >= 2 or self.object_type == -7:
            self.object_info = reader.read_uint16()
            self.object_info_list = reader.read_int16()
            if self.num in extensionLoaders:
                self.loader = self.new(extensionLoaders[self.num], reader)
        reader.seek(current_position + size)

    def write(self, reader: ByteIO):
        reader.write_int16(self.object_type)
        reader.write_int16(self.num)
        if self.object_type == 0 and self.num == 0:
            return
        dataReader = ByteIO(mode='wb')
        if self.object_type in system_loaders and self.num in system_loaders[self.object_type]:
            self.loader.write(dataReader)
        elif self.object_type >= 2 or self.object_type == -7:
            dataReader.write_uint16(self.object_info)
            dataReader.write_int16(self.object_info_list)
            if self.num in extensionLoaders:
                self.loader.write(dataReader)
        reader.write_uint16(len(dataReader) + 6)
        reader.write_bytes(dataReader.read_bytes())

    def get_extension_num(self):
        return self.num - 80
