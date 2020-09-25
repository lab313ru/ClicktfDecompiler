from CTF_ByteIO import ByteIO
from Loader import DataLoader

MOVEMENT_TYPES = [
    'Static',
    'Mouse',
    'Race',
    'EightDirections',
    'Ball',
    'Path',
    'Intelligent',
    'Pinball',
    'List',
    'Platform',
    'GoMovement',  # wtf!?
    'Disappear',  # wtf!?!?!?
    'Appear',
    'Bullet',
    'Extension'
]


class Static(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader


class Mouse(DataLoader):
    x1 = None
    x2 = None
    y1 = None
    y2 = None
    unusedFlags = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.x1 = self.reader.read_int16()
        self.x2 = self.reader.read_int16()
        self.y1 = self.reader.read_int16()
        self.y2 = self.reader.read_int16()
        unusedFlags = self.reader.read_int16()


class Race(DataLoader):
    speed = None
    acceleration = None
    deceleration = None
    rotationSpeed = None
    bounceFactor = None
    reverseEnabled = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.speed = self.reader.read_int16()
        self.acceleration = self.reader.read_int16()
        self.deceleration = self.reader.read_int16()
        self.rotationSpeed = self.reader.read_int16()
        self.bounceFactor = self.reader.read_int16()
        self.angles = self.reader.read_int16()
        self.reverseEnabled = self.reader.read_int16()


class EightDirections(DataLoader):
    speed = None
    acceleration = None
    deceleration = None
    bounceFactor = None  # as stated in Cncf.h
    directions = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.speed = self.reader.read_int16()
        self.acceleration = self.reader.read_int16()
        self.deceleration = self.reader.read_int16()
        self.bounceFactor = self.reader.read_int16()
        self.directions = self.reader.read_int32()


class Ball(DataLoader):
    speed = None
    randomizer = None
    angles = None
    security = None
    deceleration = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.speed = self.reader.read_int16()
        self.randomizer = self.reader.read_int16()
        self.angles = self.reader.read_int16()
        self.security = self.reader.read_int16()
        self.deceleration = self.reader.read_int16()


class Path(DataLoader):
    minimumSpeed = None
    maximumSpeed = None
    loop = None
    repositionAtEnd = None
    reverseAtEnd = None

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.steps = []
        count = self.reader.read_int16()
        self.minimumSpeed = self.reader.read_int16()
        self.maximumSpeed = self.reader.read_int16()
        self.loop = self.reader.read_int8()
        self.repositionAtEnd = self.reader.read_int8()
        self.reverseAtEnd = self.reader.read_int8()
        self.reader.read_bytes(1)  # "free"
        for _ in range(count):
            currentPosition = self.reader.tell()

            self.reader.read_bytes(1)
            size = self.reader.read_uint8()
            self.steps.append(Step(self.reader))

            self.reader.seek(currentPosition + size)


class Step(DataLoader):
    speed = None
    direction = None
    # destination positions relative to the last step
    destinationX = None
    destinationY = None
    cosinus = None
    sinus = None
    length = None
    pause = None
    name = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.speed = self.reader.read_uint8()
        self.direction = self.reader.read_int8()
        self.destinationX = self.reader.read_int16()
        self.destinationY = self.reader.read_int16()
        self.cosinus = self.reader.read_int16() / 16384.0
        self.sinus = self.reader.read_int16() / 16384.0
        self.length = self.reader.read_int16()
        self.pause = self.reader.read_int16()
        name = self.reader.read_ascii_string()
        if len(name) > 0:
            self.name = name


CONTROLS = [
    'NoJump',
    'WhileWalking',
    'Button1',
    'Button2'
]


class Platform(DataLoader):
    speed = None
    acceleration = None
    deceleration = None
    control = None
    gravity = None
    jumpStrength = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.speed = self.reader.read_int16()
        self.acceleration = self.reader.read_int16()
        self.deceleration = self.reader.read_int16()
        self.control = self.reader.read_int16()
        self.gravity = self.reader.read_int16()
        self.jumpStrength = self.reader.read_int16()

    def getControl(self):
        return CONTROLS[self.control]

    def setControl(self, name):
        self.control = CONTROLS.index(name)


class Extension(DataLoader):
    id = None
    data = None
    name = None

    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.data = self.reader.read(self.settings['dataSize'])


MOVEMENT_CLASSES = {
    0: Static,
    1: Mouse,
    2: Race,
    3: EightDirections,
    4: Ball,
    5: Path,
    9: Platform,
    14: Extension
}


class Movements(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader

        self.items = []

        rootPosition = self.reader.tell()
        count = self.reader.read_uint32()
        currentPosition = self.reader.tell()
        for _ in range(count):
            self.items.append(Movement(self.reader, rootPosition=rootPosition))
            self.reader.seek(currentPosition + 16)
            currentPosition = self.reader.tell()


class Movement(DataLoader):
    player = None
    type = None
    movingAtStart = None
    directionAtStart = None
    loader = None

    def __init__(self, reader: ByteIO, rootPosition):
        self.reader = reader

        # extension stuff (if extension, that is)
        rootPosition = self.settings['rootPosition']

        nameOffset = self.reader.read_int32()
        movementId = self.reader.read_int32()
        newOffset = self.reader.read_int32()
        dataSize = self.reader.read_int32()

        self.reader.seek(rootPosition + newOffset)
        self.player = self.reader.read_int16()
        self.type = self.reader.read_int16()
        self.movingAtStart = self.reader.read_int8()

        self.reader.read_bytes(3)  # free

        self.directionAtStart = self.reader.read_int32()

        if self.getName() == 'Extension':
            self.reader.read_bytes(14)
            dataSize -= 14

        self.loader = MOVEMENT_CLASSES[self.type](self.reader,
                                                  dataSize=dataSize - 12)

        if self.getName() == 'Extension':
            self.reader.seek(rootPosition + nameOffset)
            self.loader.name = self.reader.read_ascii_string()[:-4]
            self.loader.id = movementId

    def getName(self):
        return MOVEMENT_TYPES[self.type]

    def setName(self, name):
        self.type = MOVEMENT_TYPES.index(name)
