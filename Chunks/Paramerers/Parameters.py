from typing import List

from CTF_ByteIO import ByteIO
from Chunks.Common import ObjectInfoMixin, ObjectTypeMixin
from Chunks.Expressions.Expression import Expression
from Chunks.FontBank import LogFont
from Chunks.Key import Key
from Loader import DataLoader
from bitdict import BitDict

EQUAL = 0
DIFFERENT = 1
LOWER_OR_EQUAL = 2
LOWER = 3
GREATER_OR_EQUAL = 4
GREATER = 5

OPERATOR_LIST = [
    '=',
    '<>',
    '<=',
    '<',
    '>=',
    '>'
]
SAMPLE_FLAGS = BitDict(
    'Uninterruptible',
    'Bad',
    'IPhoneAudioPlayer',
    'IPhoneOpenAL'
)

POSITION_FLAGS = BitDict(
    # Located flag
    # True: transform position according to the direction of parent
    # False: use position without transformation
    'Direction',
    # Origin flag
    'Action',
    # 2 orientation flags (both are set appropriately)
    # True: use direction of parent
    'InitialDirection',
    # True: use default movement direction
    'DefaultDirection'
)

PROGRAM_FLAGS = BitDict(
    'Wait',
    'Hide'
)

GROUP_FLAGS = BitDict(
    'Inactive',
    'Closed',
    'ParentInactive',
    'GroupInactive',
    'Global'  # unicode?
)

LEFT_CLICK = 0
MIDDLE_CLICK = 1
RIGHT_CLICK = 2

CLICK_NAMES = [
    'Left',
    'Middle',
    'Right'
]


def get_attributes(loader):
    attributes = {}
    for k in dir(loader):
        if k.startswith('__') or k in dir(DataLoader):
            continue
        v = getattr(loader, k)
        if hasattr(v, '__call__'):
            continue
        if isinstance(v, DataLoader):
            v = get_attributes(v)
        attributes[k] = v
    return attributes


class ParameterCommon(DataLoader):
    isExpression = False


class Object(ParameterCommon, ObjectInfoMixin, ObjectTypeMixin):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.objectInfoList = None
        self.objectInfo = None
        self.objectType = None

    def read(self):
        reader = self.reader
        self.objectInfoList = reader.read_int16()
        self.objectInfo = reader.read_uint16()
        self.objectType = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_int16(self.objectInfoList)
        reader.write_uint16(self.objectInfo)
        reader.write_int16(self.objectType)


class Time(ParameterCommon):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.timer = None
        self.loops = None

    def read(self):
        reader = self.reader
        self.timer = reader.read_int32()
        self.loops = reader.read_int32()

    def write(self, reader: ByteIO):
        reader.write_int32(self.timer)
        reader.write_int32(self.loops)


class Short(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = None

    def read(self):
        reader = self.reader
        self.value = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_int16(self.value)


class Int(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = None

    def read(self):
        reader = self.reader
        self.value = reader.read_int32()

    def write(self, reader: ByteIO):
        reader.write_int32(self.value)


class Remark(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.font = LogFont(reader, True)
        self.fontColor = None
        self.backColor = None
        self.id = None

    def read(self):
        reader = self.reader
        self.font.read()
        self.fontColor = reader.read_fmt('BBBB')
        self.backColor = reader.read_fmt('BBBB')
        if reader.read_int16() != 0:
            print('remark NOOO')
        self.id = reader.read_uint32()

    def write(self, reader: ByteIO):
        # self.font.write(reader) #TODO
        reader.write_fmt('BBBB', self.fontColor)
        reader.write_fmt('BBBB', self.backColor)
        reader.write_int16(0)
        reader.write_int32(self.id)


class Sample(ParameterCommon):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = SAMPLE_FLAGS.copy()
        self.handle = None
        self.flags = None
        self.name = None

    def read(self):
        reader = self.reader
        self.handle = reader.read_int16()
        self.flags.setFlags(reader.read_uint16())
        self.name = reader.read_ascii_string()

    def write(self, reader: ByteIO):
        reader.write_int16(self.handle)
        reader.write_int16(self.flags.getFlags())
        reader.write_ascii_string(self.name, zero_terminated=True)


class Position(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.objectInfoParent = None
        self.flags = POSITION_FLAGS.copy()
        self.x = None
        self.y = None
        self.slope = None
        self.angle = None
        self.direction = None
        self.typeParent = None
        self.objectInfoList = None
        self.layer = None

    def read(self):
        reader = self.reader
        self.objectInfoParent = reader.read_uint16()
        self.flags.setFlags(reader.read_uint16())
        self.x = reader.read_int16()
        self.y = reader.read_int16()
        self.slope = reader.read_int16()
        self.angle = reader.read_int16()
        self.direction = reader.read_int32()
        self.typeParent = reader.read_int16()
        self.objectInfoList = reader.read_int16()
        self.layer = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_uint16(self.objectInfoParent)
        reader.write_uint16(self.flags.getFlags())
        reader.write_int16(self.x)
        reader.write_int16(self.y)
        reader.write_int16(self.slope)
        reader.write_int16(self.angle)
        reader.write_int32(self.direction)
        reader.write_int16(self.typeParent)
        reader.write_int16(self.objectInfoList)
        reader.write_int16(self.layer)


class Create(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.objectInstance = None
        self.objectInfo = None
        self.position = Position(reader)

    def read(self, reader):
        self.position.read()
        self.objectInstance = reader.read_uint16()
        self.objectInfo = reader.read_uint16()
        reader.skipBytes(4)  # free

    def write(self, reader):
        self.position.write(reader)
        reader.write_int16(self.objectInstance, True)
        reader.write_int16(self.objectInfo, True)
        reader.write_bytes('\x00' * 4)


class Every(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.delay = None
        self.compteur = None

    def read(self):
        reader = self.reader
        self.delay = reader.read_int32()  # in ms
        self.compteur = reader.read_int32()

    def write(self, reader: ByteIO):
        reader.write_int32(self.delay)
        reader.write_int32(self.compteur)


class KeyParameter(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.key = None

    def read(self):
        reader = self.reader
        self.key = Key(reader.read_int16())

    def write(self, reader: ByteIO):
        reader.write_int16(self.key.getValue())


class ExpressionParameter(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.isExpression = True
        self.comparison = 0
        self.items = []  # type: List[Expression]

    def read(self):
        reader = self.reader
        self.comparison = reader.read_int16()
        items = self.items
        while 1:
            expression = Expression(reader)
            expression.read()
            items.append(expression)
            if expression.object_type == 0 and expression.num == 0:
                break

    def write(self, reader):
        reader.write_int16(self.comparison)
        for item in self.items:
            item.write(reader)

    def get_operator(self):
        return OPERATOR_LIST[self.comparison]


class Shoot(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.position = Position(reader)
        self.objectInstance = 0
        self.objectInfo = 0
        self.shootSpeed = 0

    def read(self):
        reader = self.reader
        self.position.read()
        self.objectInstance = reader.read_uint16()
        self.objectInfo = reader.read_uint16()
        reader.skip(4)  # free
        self.shootSpeed = reader.read_int16()

    def write(self, reader):
        self.position.write(reader)
        reader.write_uint16(self.objectInstance)
        reader.write_uint16(self.objectInfo)
        reader.write_bytes('\x00' * 4)
        reader.write_int16(self.shootSpeed)


class Zone(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0

    def read(self):
        reader = self.reader
        self.x1 = reader.read_int16()
        self.y1 = reader.read_int16()
        self.x2 = reader.read_int16()
        self.y2 = reader.read_int16()

    def write(self, reader):
        reader.write_int16(self.x1)
        reader.write_int16(self.y1)
        reader.write_int16(self.x2)
        reader.write_int16(self.y2)


class Colour(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = ()

    def read(self):
        reader = self.reader
        self.value = reader.read_fmt('BBBB')

    def write(self, reader: ByteIO):
        reader.write_fmt('BBBB', self.value)


class Program(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = PROGRAM_FLAGS.copy()
        self.filename = ''
        self.command = ''

    def read(self):
        reader = self.reader
        self.flags.setFlags(reader.read_uint16())
        self.filename = reader.read_ascii_string(260)
        self.command = reader.read_ascii_string()

    def write(self, reader: ByteIO):
        reader.write_uint16(self.flags.getFlags())
        filename = self.filename[:259]
        reader.write_ascii_string(filename, 260)
        reader.write_bytes(self.command.encode('ascii'))


class Group(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = GROUP_FLAGS.copy()
        self.id = 0
        self.name = ''
        self.offset = 0
        self.password = 0

    def read(self):
        reader = self.reader
        self.offset = reader.tell() - 24
        self.flags.setFlags(reader.read_uint16())
        self.id = reader.read_uint16()
        self.name = reader.read_ascii_string(96)
        self.password = reader.read_int32()

    def write(self, reader: ByteIO):
        reader.write_uint16(self.flags.getFlags())
        reader.write_uint16(self.id)
        reader.write_ascii_string(self.name, 96)
        reader.write_int32(self.password)


class GroupPointer(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.savedPointer = 0
        self.pointer = 0
        self.id = 0

    def read(self):
        reader = self.reader
        self.pointer = self.savedPointer = reader.read_int32()
        self.id = reader.read_int16()
        if self.pointer != 0:
            self.pointer += reader.tell()

    def write(self, reader: ByteIO):
        reader.write_int32(self.savedPointer)
        reader.write_int16(self.id)


class String(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value = None

    def read(self):
        self.value = self.reader.read_ascii_string()

    def write(self, reader: ByteIO):
        reader.write_ascii_string(self.value, 260)


class Filename(String):

    def write(self, reader: ByteIO):
        value = self.value[:259]
        reader.write_ascii_string(value, 260)


class CompareTime(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.timer = None
        self.loops = None
        self.comparison = None

    def read(self):
        reader = self.reader
        self.timer = reader.read_int32()
        self.loops = reader.read_int32()
        self.comparison = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_int32(self.timer)
        reader.write_int32(self.loops)
        reader.write_int16(self.comparison)


class TwoShorts(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.value1 = 0
        self.value2 = 0

    def read(self, ):
        reader = self.reader
        self.value1 = reader.read_int16()
        self.value2 = reader.read_int16()

    def write(self, reader: ByteIO):
        reader.write_int16(self.value1)
        reader.write_int16(self.value2)


class Extension(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.data = ByteIO()
        self.size = 0
        self.type = 0
        self.code = 0

    def read(self):
        reader = self.reader
        self.size = reader.read_int16()
        self.type = reader.read_int16()
        self.code = reader.read_int16()
        self.data = ByteIO(byte_object=reader.read_bytes(self.size - 6))

    def get_reader(self):
        self.data.seek(0)
        return self.data

    def write(self, reader: ByteIO):
        reader.write_int16(len(self.data) + 6)
        reader.write_int16(self.type)
        reader.write_int16(self.code)
        reader.write_bytes(self.data.read_bytes())


class Click(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.double = 0
        self.click = 0

    def read(self):
        reader = self.reader
        self.click = reader.read_int8()
        self.double = bool(reader.read_int8())

    def write(self, reader: ByteIO):
        reader.write_int8(self.click)
        reader.write_int8(int(self.double))

    def get_button(self):
        return CLICK_NAMES[self.click]


class CharacterEncoding(ParameterCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader

    def read(self):
        pass
        # raise NotImplementedError()
        # typedef struct {
        #     WORD    wCharEncoding;
        #     DWORD   dwUnusedParam;
        # } charEncodingParam;

    def write(self, reader):
        pass
        # raise NotImplementedError()


class Bug(ParameterCommon):
    def read(self, reader):
        pass

    def write(self, reader):
        pass


parameter_loaders = [
    None,
    Object,
    Time,
    Short,
    Short,
    Int,
    Sample,
    Sample,
    None,
    Create,
    Short,
    Short,
    Short,
    Every,
    KeyParameter,
    ExpressionParameter,
    Position,
    Short,
    Shoot,
    Zone,
    None,
    Create,
    ExpressionParameter,
    ExpressionParameter,
    Colour,
    Int,
    Short,
    ExpressionParameter,
    ExpressionParameter,
    Int,
    None,
    Short,
    Click,
    Program,
    Int,
    Sample,
    Sample,
    Remark,
    Group,
    GroupPointer,
    Filename,
    String,
    CompareTime,
    Short,
    KeyParameter,
    ExpressionParameter,
    ExpressionParameter,
    TwoShorts,
    Int,
    Short,
    Short,
    TwoShorts,
    ExpressionParameter,
    ExpressionParameter,
    ExpressionParameter,
    Extension,
    Int,
    Short,
    Short,
    ExpressionParameter,
    Short,
    Short,
    ExpressionParameter,
    Filename,
    String,
    CharacterEncoding,
    CharacterEncoding
]

parameter_names = {
    1: 'OBJECT',
    2: 'TIME',
    3: 'SHORT',
    4: 'SHORT',
    5: 'INT',
    6: 'SAMPLE',
    7: 'SAMPLE',
    9: 'CREATE',
    10: 'SHORT',
    11: 'SHORT',
    12: 'SHORT',
    13: 'Every',
    14: 'KEY',
    15: 'EXPRESSION',
    16: 'POSITION',
    17: 'JOYDIRECTION',
    18: 'SHOOT',
    19: 'ZONE',
    21: 'SYSCREATE',
    22: 'EXPRESSION',
    23: 'COMPARISON',
    24: 'COLOUR',
    25: 'BUFFER4',
    26: 'FRAME',
    27: 'SAMLOOP',
    28: 'MUSLOOP',
    29: 'NEWDIRECTION',
    31: 'TEXTNUMBER',
    32: 'Click',
    33: 'PROGRAM',
    34: 'OLDPARAM_VARGLO',
    35: 'CNDSAMPLE',
    36: 'CNDMUSIC',
    37: 'REMARK',
    38: 'GROUP',
    39: 'GROUPOINTER',
    40: 'FILENAME',
    41: 'STRING',
    42: 'CMPTIME',
    43: 'PASTE',
    44: 'VMKEY',
    45: 'EXPSTRING',
    46: 'CMPSTRING',
    47: 'INKEFFECT',
    48: 'MENU',
    49: 'GlobalValue',
    50: 'AlterableValue',
    51: 'FLAG',
    52: 'VARGLOBAL_EXP',
    53: 'AlterableValueExpression',
    54: 'FLAG_EXP',
    55: 'EXTENSION',
    56: '8DIRECTIONS',
    57: 'MVT',
    58: 'GlobalString',
    59: 'STRINGGLOBAL_EXP',
    60: 'PROGRAM2',
    61: 'ALTSTRING',
    62: 'ALTSTRING_EXP',
    63: 'FILENAME',
    64: 'FASTLOOPNAME',
    65: 'CHAR_ENCODING_INPUT',
    66: 'CHAR_ENCODING_OUTPUT'
}


def get_name(id):
    return parameter_names[id]
