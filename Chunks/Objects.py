from Chunks.ObjectInfo import *
from Chunks.Transitions import FadeIn, FadeOut
from Loader import DataLoader
from bitdict import BitDict

LINE_SHAPE = 1
RECTANGLE_SHAPE = 2
ELLIPSE_SHAPE = 3

SHAPE_TYPES = {
    1: 'Line',
    2: 'Rectangle',
    3: 'Ellipse'
}

NONE_FILL = 0
SOLID_FILL = 1
GRADIENT_FILL = 2
MOTIF_FILL = 3

FILL_TYPES = [
    'None',
    'Solid',
    'Gradient',
    'Motif'
]

HORIZONTAL_GRADIENT = 0
VERTICAL_GRADIENT = 1

GRADIENT_TYPES = [
    'Horizontal',
    'Vertical'
]

SHAPE_FLAGS = BitDict(
    'InverseX',
    'InverseY'
)


class AlterableValues(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = [self.reader.read_int32()
                      for _ in range(self.reader.read_uint16())]


class AlterableStrings(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = [self.reader.read_ascii_string()
                      for _ in range(self.reader.read_uint16())]


class Shape(DataLoader):
    def __init__(self, reader: ByteIO, width=32, height=32):
        self.reader = reader
        self.width = width
        self.height = height
        self.lineFlags = SHAPE_FLAGS.copy()
        self.borderSize = self.reader.read_int16()
        self.borderColor = [self.reader.read_uint8() for _ in range(4)]
        self.shape = self.reader.read_int16()
        self.fillType = self.reader.read_int16()
        if self.shape == LINE_SHAPE:
            self.lineFlags.setFlags(self.reader.read_uint16())
        elif self.fillType == SOLID_FILL:
            self.color1 = [self.reader.read_uint8() for _ in range(4)]
        elif self.fillType == GRADIENT_FILL:
            self.color1 = [self.reader.read_uint8() for _ in range(4)]
            self.color2 = [self.reader.read_uint8() for _ in range(4)]
            self.gradientFlags = self.reader.read_int16()
        elif self.fillType == MOTIF_FILL:
            self.image = self.reader.read_int16()


NONE_OBSTACLE = 0
SOLID_OBSTACLE = 1
PLATFORM_OBSTACLE = 2
LADDER_OBSTACLE = 3
TRANSPARENT_OBSTACLE = 4

OBSTACLE_TYPES = [
    'None',
    'Solid',
    'Platform',
    'Ladder',
    'Transparent'
]

FINE_COLLISION = 0
BOX_COLLISION = 1

COLLISION_MODES = [
    'Fine',
    'Box'
]


class _Background:

    def get_collision_mode(self):
        return COLLISION_MODES[self.collision_mode]

    def get_obstacle_type(self):
        return OBSTACLE_TYPES[self.obstacle_type]


class QuickBackdrop(DataLoader, _Background):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        size = self.reader.read_uint32()

        self.obstacle_type = self.reader.read_int16()
        self.collision_mode = self.reader.read_int16()
        self.width = self.reader.read_int32()
        self.height = self.reader.read_int32()

        if size < 12 + 16:
            return
        self.shape = Shape(self.reader, width=self.width,
                           height=self.height)


class Backdrop(DataLoader, _Background):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        size = self.reader.read_int32()
        self.obstacle_type = self.reader.read_int16()
        self.collision_mode = self.reader.read_int16()
        self.width = self.reader.read_int32()
        self.height = self.reader.read_int32()
        self.image = self.reader.read_int16()


HAS_SINGLE_SPEED = [
    0, 3, 4, 6
]


class AnimationDirection(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.minSpeed = self.reader.read_uint8()
        self.maxSpeed = self.reader.read_uint8()
        if self.settings['index'] in HAS_SINGLE_SPEED:
            self.minSpeed = self.maxSpeed
            self.hasSingle = True
        self.repeat = self.reader.read_int16()
        self.backTo = self.reader.read_int16()
        self.frames = [self.reader.read_int16()
                       for _ in range(self.reader.read_int16())]


ANIMATION_NAMES = [
    'Stopped',
    'Walking',
    'Running',
    'Appearing',
    'Disappearing',
    'Bouncing',
    'Shooting',
    'Jumping',
    'Falling',
    'Climbing',
    'Crouch down',
    'Stand up',
    'User defined 1',
    'User defined 2',
    'User defined 3',
    'User defined 4'
]


def getClosestDirection(direction, directionDict):
    try:
        return directionDict[direction]
    except KeyError:
        pass

    # (directionObject, distance)
    forward = None
    backward = None

    # get closest in back
    position = direction
    distance = 0
    while 1:
        position -= 1
        distance += 1
        if position < 0:
            position = 31
        if position in directionDict:
            backward = (directionDict[position], distance)
            break

    # get closest ahead
    position = direction
    distance = 0
    while 1:
        position = (position + 1) % 32
        distance += 1
        if position in directionDict:
            forward = (directionDict[position], distance)
            break

    # backward has priority
    if backward[1] >= forward[1]:
        return forward[0]
    else:
        return backward[0]


class Animation(DataLoader):
    def __init__(self, reader: ByteIO, index):
        self.reader = reader
        self.index = index
        self.directions = []
        self.loadedDirections = {}
        # self.index = self.settings['index']
        current_position = self.reader.tell()

        offsets = [self.reader.read_int16() for _ in range(32)]

        direction_dict = self.loadedDirections = {}
        for index, offset in enumerate(offsets):
            if offset != 0:
                self.reader.seek(current_position + offset)
                direction_dict[index] = AnimationDirection(self.reader)

        for index in range(32):
            self.directions.append(getClosestDirection(index,
                                                       direction_dict))

    def getIndex(self):
        return self.index

    def getName(self):
        index = self.getIndex()
        try:
            return ANIMATION_NAMES[index]
        except:
            return 'User defined %s' % (index - 12 + 1)


STOPPED = 0
WALKING = 1
RUNNING = 2
APPEARING = 3
DISAPPEARING = 4
BOUNCING = 5
SHOOTING = 6
JUMPING = 7
FALLING = 8
CLIMBING = 9
CROUCH_DOWN = 10
STAND_UP = 11

ANIMATION_ALTERNATIVES = {
    STOPPED: [APPEARING, WALKING, RUNNING],
    WALKING: [RUNNING],
    RUNNING: [WALKING],
    APPEARING: [WALKING, RUNNING],
    BOUNCING: [WALKING, RUNNING],
    SHOOTING: [WALKING, RUNNING],
    JUMPING: [WALKING, RUNNING],
    FALLING: [WALKING, RUNNING],
    CLIMBING: [WALKING, RUNNING],
    CROUCH_DOWN: [WALKING, RUNNING],
    STAND_UP: [WALKING, RUNNING]
}


def getClosestAnimation(index, animationDict, count):
    try:
        return animationDict[index]
    except KeyError:
        pass
    try:
        for alternative in ANIMATION_ALTERNATIVES[index]:
            if alternative in animationDict:
                return animationDict[alternative]
    except KeyError:
        pass
    for i in range(count):
        if i in animationDict:
            return animationDict[i]
    raise IndexError('no animation could be found for %r' % (
        ANIMATION_NAMES[index]))


class AnimationHeader(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.loadedAnimations = {}
        self.items = []

        currentPosition = self.reader.tell()

        size = self.reader.read_int16()

        count = self.reader.read_int16()

        offsets = [self.reader.read_int16() for _ in range(count)]

        self.loadedAnimations = animationDict = {}
        for index, offset in enumerate(offsets):
            if offset != 0:
                self.reader.seek(currentPosition + offset)
                animationDict[index] = Animation(self.reader, index=index)

        for index in range(count):
            self.items.append(getClosestAnimation(index, animationDict, count))

    def fromName(self, name):
        index = ANIMATION_NAMES.index(name)
        return self.items[index]


HIDDEN = 0
NUMBERS = 1
VERTICAL_BAR = 2
HORIZONTAL_BAR = 3
ANIMATION = 4
TEXT_COUNTER = 5

DISPLAY_NAMES = [
    'Hidden',
    'Numbers',
    'VerticalBar',
    'HorizontalBar',
    'Animation',
    'Text'
]

COUNTER_FRAMES = [
    '0',
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    '-',
    '+',
    '.',
    'e'
]


class InvalidFont(object):
    handle = None
    checksum = None
    references = None
    value = None


INVALID_FONT = InvalidFont()
INT_DIGITS_MASK = 0xF
FLOAT_DIGITS_MASK = 0xF0
FORMAT_FLOAT = 0x0200
FLOAT_DIGITS_SHIFT = 4
USE_DECIMALS = 0x0400
FLOAT_DECIMALS_MASK = 0xF000
FLOAT_DECIMALS_SHIFT = 12
FLOAT_PAD = 0x0800


class Counters(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        size = self.reader.read_uint32()
        self.width = self.reader.read_uint32()
        self.height = self.reader.read_uint32()
        self.player = self.reader.read_uint16()
        self.displayType = self.reader.read_int16()
        self.flags = self.reader.read_int16()

        self.integerDigits = self.flags & INT_DIGITS_MASK
        self.formatFloat = self.flags & FORMAT_FLOAT != 0
        self.floatDigits = ((self.flags & FLOAT_DIGITS_MASK
                             ) >> FLOAT_DIGITS_SHIFT) + 1
        self.useDecimals = self.flags & USE_DECIMALS != 0
        self.decimals = ((self.flags & FLOAT_DECIMALS_MASK
                          ) >> FLOAT_DECIMALS_SHIFT)
        self.addNulls = self.flags & FLOAT_PAD != 0

        self.inverse = byteflag.getFlag(self.flags, 8)
        self.font = self.reader.read_uint16()
        if self.displayType == HIDDEN:
            pass
        elif self.displayType in (NUMBERS, ANIMATION):
            self.frames = [self.reader.read_int16()
                           for _ in range(self.reader.read_uint16())]
        elif self.displayType in (VERTICAL_BAR, HORIZONTAL_BAR, TEXT_COUNTER):
            self.shape = Shape(self.reader)

    def getFont(self, fonts):
        try:
            return fonts.from_handle(self.font)
        except (ValueError, AttributeError):
            return INVALID_FONT

    def getImage(self, name, images):
        return images.from_handle(self.frames[COUNTER_FRAMES.index(name)])

    def getDisplayType(self):
        return DISPLAY_NAMES[self.displayType]


PARAGRAPH_FLAGS = BitDict(
    'HorizontalCenter',
    'RightAligned',
    'VerticalCenter',
    'BottomAligned',
    None, None, None, None,
    'Correct',
    'Relief'
)


class Text(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.flags = PARAGRAPH_FLAGS.copy()

        self.font = self.reader.read_uint16()
        self.flags.setFlags(self.reader.read_uint16())
        self.color = [self.reader.read_uint8() for _ in range(4)]
        self.value = self.reader.read_ascii_string()

    def getFont(self, fonts):
        try:
            return fonts.from_handle(self.font)
        except (ValueError, AttributeError):
            return INVALID_FONT


class Paragraph(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.items = []
        currentPosition = self.reader.tell()
        size = self.reader.read_int32()
        self.width = self.reader.read_int32()
        self.height = self.reader.read_int32()

        itemOffsets = [self.reader.read_int32()
                       for _ in range(self.reader.read_int32())]

        for offset in itemOffsets:
            self.reader.seek(currentPosition + offset)
            self.items.append(Paragraph(self.reader))


class RTFObject(DataLoader):
    RTF_FLAGS = BitDict(
        'Transparent',
        'VerticalSlider',
        'HorizontalSlider'
    )

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.options = self.RTF_FLAGS.copy()

        size = self.reader.read_int32()
        self.version = self.reader.read_int32()
        self.options.setFlags(self.reader.read_int32())
        self.backColor = [self.reader.read_uint8() for _ in range(4)]
        self.width = self.reader.read_int32()
        self.height = self.reader.read_int32()
        self.reader.read_bytes(4)
        self.value = self.reader.read(self.reader.read_int32())


DOCK_POSITIONS = {
    (False, False): 'Left',
    (True, False): 'Top',
    (False, True): 'Right',
    (True, True): 'Bottom'
}

SUBAPPLICATION_FLAGS = BitDict(
    'ShareGlobals',
    'ShareLives',
    'ShareScores',
    None,  # 'SHARE_WINATTRIB',
    'Stretch',
    'Popup',
    'Caption',
    'ToolCaption',
    'Border',
    'Resizable',
    'SystemMenu',
    'DisableClose',
    'Modal',
    'DialogFrame',
    'Internal',  # 'INTERNAL',
    'HideOnClose',
    'CustomableSize',
    None,  # 'INTERNALABOUTBOX',
    'ClipSiblings',
    'SharePlayerControls',
    'MDIChild',
    'Docked',
    'Docked1',
    'Docked2',
    'Reopen',
    'RunEvenIfNotActive'
)


class SubApplication(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.options = SUBAPPLICATION_FLAGS.copy()

        size = self.reader.read_int32()
        self.width = self.reader.read_int32()
        self.height = self.reader.read_int32()
        self.version = self.reader.read_int16()
        self.startFrame = self.reader.read_int16()
        self.options.setFlags(self.reader.read_uint32())
        self.iconOffset = self.reader.read_int32()
        self.reader.read_bytes(4)  # "free"
        self.name = self.reader.read_ascii_string()

    def getDockedPosition(self):
        docked1 = self.options['Docked1']
        docked2 = self.options['Docked2']
        return DOCK_POSITIONS[(docked1, docked2)]


class Counter(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        size = self.reader.read_int16()
        self.initial = self.reader.read_int32()
        self.minimum = self.reader.read_int32()
        self.maximum = self.reader.read_int32()


# free(Villy)
# everything's good now! thanks Villy!

NEW_OBJECT_FLAGS = BitDict(
    'DoNotSaveBackground',
    'SolidBackground',
    'CollisionBox',
    'VisibleAtStart',
    'ObstacleSolid',
    'ObstaclePlatform',
    'AutomaticRotation'
)

OBJECT_FLAGS = BitDict(
    'DisplayInFront',
    'Background',
    'Backsave',
    'RunBeforeFadeIn',
    'Movements',
    'Animations',
    'TabStop',
    'WindowProc',
    'Values',
    'Sprites',
    'InternalBacksave',
    'ScrollingIndependant',
    'QuickDisplay',
    'NeverKill',
    'NeverSleep',
    'ManualSleep',
    'Text',
    'DoNotCreateAtStart',
    'FakeSprite',
    'FakeCollisions'
)

OBJECT_PREFERENCES = BitDict(
    'Backsave',
    'ScrollingIndependant',
    'QuickDisplay',
    'Sleep',
    'LoadOnCall',
    'Global',
    'BackEffects',
    'Kill',
    'InkEffects',
    'Transitions',
    'FineCollisions',
    'AppletProblems'
)


class ObjectCommon(DataLoader):
    def __init__(self, reader: ByteIO, parent=None):
        self.reader = reader

        self.parent = parent
        self.qualifiers = []
        # OCFLAGS2
        self.newFlags = NEW_OBJECT_FLAGS.copy()
        # OEFLAG
        self.flags = OBJECT_FLAGS.copy()
        # OEPREF
        self.preferences = OBJECT_PREFERENCES.copy()

        currentPosition = self.reader.tell()
        size = self.reader.read_int32()
        newobj = (self.settings['build'] >= 284 and not self.settings.get('compat', False))
        newobj2 = True

        if newobj and newobj2:
            animationsOffset = self.reader.read_uint16()
            movementsOffset = self.reader.read_uint16()
            self.version = self.reader.read_int16()
            self.reader.read_bytes(2)  # "free"
            extensionOffset = self.reader.read_uint16()
            counterOffset = self.reader.read_uint16()
            self.flags.setFlags(self.reader.read_uint32())

            end = self.reader.tell() + 8 * 2

            for _ in range(8):
                qualifier = self.reader.read_int16()
                if qualifier == -1:
                    break
                self.qualifiers.append(qualifier)

            self.reader.seek(end)

            systemObjectOffset = self.reader.read_int16()

            valuesOffset = self.reader.read_int16()
            stringsOffset = self.reader.read_int16()
            self.newFlags.setFlags(self.reader.read_uint16())
            self.preferences.setFlags(self.reader.read_uint16())  # runtime data
            self.identifier = self.reader.read_int32()
            self.backColour = [self.reader.read_uint8() for _ in range(4)]
            fadeInOffset = self.reader.read_int32()
            fadeOutOffset = self.reader.read_int32()
        elif newobj:
            counterOffset = self.reader.read_int16()
            self.version = self.reader.read_int16()
            self.reader.read_bytes(2)  # "free"
            movementsOffset = self.reader.read_int16()
            extensionOffset = self.reader.read_int16()
            animationsOffset = self.reader.read_int16()
            self.flags.setFlags(self.reader.read_uint32())

            end = self.reader.tell() + 8 * 2

            for _ in range(8):
                qualifier = self.reader.read_int16()
                if qualifier == -1:
                    break
                self.qualifiers.append(qualifier)

            self.reader.seek(end)

            systemObjectOffset = self.reader.read_int16()

            valuesOffset = self.reader.read_int16()
            stringsOffset = self.reader.read_int16()
            self.newFlags.setFlags(self.reader.read_uint16())
            self.preferences.setFlags(self.reader.read_uint16())  # runtime data
            self.identifier = self.reader.read_int32()
            self.backColour = [self.reader.read_uint8() for _ in range(4)]
            fadeInOffset = self.reader.read_int32()
            fadeOutOffset = self.reader.read_int32()
        else:
            # start change
            movementsOffset = self.reader.read_uint16()
            animationsOffset = self.reader.read_int16()
            self.version = self.reader.read_int16()
            counterOffset = self.reader.read_int16()
            systemObjectOffset = self.reader.read_int16()
            self.reader.read_bytes(2)  # "free"
            # stop change

            self.flags.setFlags(self.reader.read_uint32())

            end = self.reader.tell() + 8 * 2

            for _ in range(8):
                qualifier = self.reader.read_int16()
                if qualifier == -1:
                    break
                self.qualifiers.append(qualifier)

            self.reader.seek(end)

            # can change
            extensionOffset = self.reader.read_int16()

            valuesOffset = self.reader.read_int16()
            stringsOffset = self.reader.read_int16()
            self.newFlags.setFlags(self.reader.read_uint16())
            self.preferences.setFlags(self.reader.read_uint16())  # runtime data
            self.identifier = self.reader.read_int32()
            self.backColour = [self.reader.read_uint8() for _ in range(4)]
            fadeInOffset = self.reader.read_int32()
            fadeOutOffset = self.reader.read_int32()

        if movementsOffset != 0:
            self.reader.seek(currentPosition + movementsOffset)
            self.movements = Movements(self.reader)

        if valuesOffset != 0:
            self.reader.seek(currentPosition + valuesOffset)
            self.values = AlterableValues(self.reader)

        if stringsOffset != 0:
            self.reader.seek(currentPosition + stringsOffset)
            self.strings = AlterableStrings(self.reader)

        if animationsOffset != 0:
            self.reader.seek(currentPosition + animationsOffset)
            self.animations = AnimationHeader(self.reader)

        if counterOffset != 0:
            self.reader.seek(currentPosition + counterOffset)
            self.counter = Counter(self.reader)

        if extensionOffset != 0:
            self.reader.seek(currentPosition + extensionOffset)

            dataSize = self.reader.read_int32() - 20
            self.reader.read_bytes(4)  # maxSize
            self.extensionVersion = self.reader.read_int32()
            self.extensionId = self.reader.read_int32()
            self.extensionPrivate = self.reader.read_int32()
            if dataSize != 0:
                self.extensionData = self.reader.read(dataSize)

        if fadeInOffset != 0:
            self.reader.seek(currentPosition + fadeInOffset)
            self.fadeIn = FadeIn(self.reader)

        if fadeOutOffset != 0:
            self.reader.seek(currentPosition + fadeOutOffset)
            self.fadeOut = FadeOut(self.reader)

        if systemObjectOffset != 0:
            self.reader.seek(currentPosition + systemObjectOffset)

            objectType = self.parent.objectType
            if objectType in (TEXT, QUESTION):
                self.text = Text(self.reader)
            elif objectType in (SCORE, LIVES, COUNTER):
                self.counters = Counters(self.reader)
            elif objectType == RTF:
                self.rtf = RTFObject(self.reader)
            elif objectType == SUBAPPLICATION:
                self.subApplication = SubApplication(self.reader)

    def isBackground(self):
        return self.flags['QuickDisplay'] or self.flags['Background']
