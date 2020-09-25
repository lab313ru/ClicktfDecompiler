import os
from typing import List

from CTF_ByteIO import ByteIO
# from Chunks.Events import Events
from Chunks.Common import Rectangle
from Chunks.Paramerers.Parameters import Int
from Chunks.StringChunks import StringChunk
from Chunks.Transitions import FadeIn, FadeOut
from Loader import DataLoader
from bitdict import BitDict


class FrameName(StringChunk):
    pass


class FramePassword(StringChunk):
    pass


class FrameHeader(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.width = 0
        self.height = 0
        self.flags = BitDict(
            'DisplayName',
            'GrabDesktop',
            'KeepDisplay',
            'FadeIn',
            'FadeOut',
            'TotalCollisionMask',
            'Password',
            'ResizeAtStart',
            'DoNotCenter',
            'ForceLoadOnCall',
            'NoSurface',
            'Reserved_1',
            'Reserved_2',
            'RecordDemo',
            None,
            'TimedMovements'
        )
        self.background = None

    def read(self):
        reader = self.reader
        self.width = reader.read_int32()
        self.height = reader.read_int32()
        self.background = reader.read_fmt('BBBB')
        self.flags.setFlags(reader.read_uint32())

    def write(self, reader: ByteIO):
        reader.write_int32(self.width)
        reader.write_int32(self.height)
        reader.write_fmt('BBBB', self.background)
        reader.write_uint32(self.flags.getFlags())


class VirtualSize(Rectangle):
    pass


class ObjectInstances(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.unk = 0
        self.items = []

    def read(self):
        reader = self.reader
        count = reader.read_uint32()
        for _ in range(count):
            item = self.new(self.__class__, reader)
            item.read()
            self.items.append(item)
        self.unk = reader.read_int32()  # XXX figure out

    def write(self, reader: ByteIO):
        reader.write_uint32(len(self.items))
        for item in self.items:
            item.write(reader)
        reader.write_uint32(0)  # TODO

    def from_handle(self, handle):
        handle = [item for item in self.items if item.handle == handle]
        return handle


class Layer(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.name = ''
        self.flags = BitDict(
            'XCoefficient',
            'YCoefficient',
            'DoNotSaveBackground',
            None,  # Wrap (Obsolete)
            'Visible',  # visible
            'WrapHorizontally',
            'WrapVertically',
            None, None, None, None,
            None, None, None, None, None,
            'Redraw',
            'ToHide',
            'ToShow'
        )
        self.x_coefficient = 0
        self.y_coefficient = 0
        self.number_of_backgrounds = 0
        self.background_index = 0

    def read(self):
        reader = self.reader
        value = reader.read_uint32()
        self.flags.setFlags(value)
        self.x_coefficient = reader.read_float()
        self.y_coefficient = reader.read_float()
        self.number_of_backgrounds = reader.read_int32()
        self.background_index = reader.read_int32()
        self.name = reader.read_ascii_string()

    def write(self, reader: ByteIO):
        reader.write_uint32(self.flags.getFlags())
        reader.write_float(self.x_coefficient)
        reader.write_float(self.y_coefficient)
        reader.write_int32(self.number_of_backgrounds)
        reader.write_int32(self.background_index)
        reader.write_ascii_string(self.name)

    def get_backgrounds(self, objectInstances):
        return objectInstances.items[
               self.background_index:self.background_index + self.number_of_backgrounds]

    def get_instances(self, objectInstances):
        return self.parent.getObjectInstances(self,
                                              objectInstances)


class Layers(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []

    def get_object_instances(self, layer, object_instances):
        layer_index = self.items.index(layer)
        try:
            return [instance for instance in object_instances.items
                    if instance.layer == layer_index]
        except AttributeError:
            return []

    def read(self):
        reader = self.reader
        self.items = [self.new(Layer, reader)
                      for _ in range(reader.read_uint32())]

    def write(self, reader: ByteIO):
        reader.write_uint32(len(self.items))
        for item in self.items:
            item.write(reader)


class FramePalette(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.items = []

    def read(self):
        reader = self.reader
        # XXX figure this out
        reader.skip(4)

        self.items = []
        for _ in range(256):
            self.items.append(reader.read_fmt('BBBB'))

    def write(self, reader: ByteIO):
        reader.write_bytes('\x00' * 4)

        for item in self.items:
            reader.write_fmt('BBBB', item)


class MovementTimerBase(Int):
    pass


class Frame(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.name = ''

        self.password = ''

        self.width = 0
        self.height = 0
        self.background = None
        self.flags = 0

        self.top = 0
        self.bottom = 0
        self.left = 0
        self.right = 0

        self.movementTimer = None

        self.instances = None
        self.maxObjects = None

        self.layers = None

        self.events = None
        self.palette = None

        self.checksum = 0

        self.fade_in = 0
        self.fade_out = 0
        self.chunks = []

    def read(self):
        from ChunkList import ChunkList
        reader = self.reader
        chunks = ChunkList(reader)
        chunks.verbose = True
        chunks.read()

        self.chunks = chunks.chunks
        name = chunks.get_chunk(FrameName)
        if name:
            self.name = name.value
        password = chunks.get_chunk(FramePassword)
        if password:
            self.password = password.value
        #
        new_header = chunks.get_chunk(FrameHeader)

        self.width = new_header.width
        self.height = new_header.height
        self.background = new_header.background
        self.flags = new_header.flags

        new_virtual = chunks.get_chunk(VirtualSize)
        self.top = new_virtual.top
        self.bottom = new_virtual.bottom
        self.left = new_virtual.left
        self.right = new_virtual.right

        self.instances = chunks.get_chunk(ObjectInstances)

        self.layers = chunks.get_chunk(Layers)

        self.events = chunks.get_chunk(Events)  # type:Events
        self.maxObjects = 50000
        # self.events.max_objects

        self.palette = chunks.get_chunk(FramePalette)

        try:
            self.movementTimer = chunks.get_chunk(MovementTimerBase)
            if self.movementTimer:
                self.movementTimer = self.movementTimer.value
            else:
                self.movementTimer = 0
        except IndexError:
            pass

        self.fade_in = chunks.get_chunk(FadeIn)
        self.fade_out = chunks.get_chunk(FadeOut)
        for chunk in chunks.chunks:
            os.makedirs(os.path.join(self.settings['dump_path'], 'CHUNKS', 'FRAMES', self.name), exist_ok=True)
            with open(os.path.join(self.settings['dump_path'], 'CHUNKS', 'FRAMES', self.name, f'{chunk.name}.chunk'),
                      'wb') as fp:
                a = chunk.raw_data
                fp.write(a)


class FrameHandles(DataLoader):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.handles = []  # type:List[int]

    def read(self):
        reader = self.reader
        self.handles = [reader.read_uint16() for _ in range(len(reader) // 2)]

    def write(self):
        reader = self.reader
        for handle in self.handles:
            reader.write_int16(handle)
