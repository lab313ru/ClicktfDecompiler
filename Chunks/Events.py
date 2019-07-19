from CTF_ByteIO import ByteIO
from Chunks.Common import ObjectInfoMixin, AceCommon
from Chunks.Paramerers.Parameters import parameter_loaders, get_name
from Loader import DataLoader
from bitdict import BitDict

HEADER = b'ER>>'
EVENT_COUNT = b'ERes'
EVENTGROUP_DATA = b'ERev'
END = b'<<ER'

ACE_FLAGS = BitDict(
    'Repeat',
    'Done',
    'Default',
    'DoneBeforeFadeIn',
    'NotDoneInStart',
    'Always',
    'Bad',
    'BadObject',
    None,
    'Notable'
)

ACE_OTHERFLAGS = BitDict(
    'Not',
    'Notable',
    'Monitorable',
    'ToDelete',
    'NewSound'
)

GROUP_FLAGS = BitDict(
    'Once',
    'NotAlways',
    'Repeat',
    'NoMore',
    'Shuffle',
    'EditorMark',
    'UndoMark',
    'ComplexGroup',
    'Breakpoint',
    'AlwaysClean',
    'OrInGroup',
    'StopInGroup',
    'OrLogical',
    'Grouped',
    'Inactive',
    'NoGood'
)


class Qualifier(DataLoader, ObjectInfoMixin):

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.objectInfo = None
        self.type = None
        self.qualifier = None
        self.objects = None

    def read(self):
        reader = self.reader
        self.objectInfo = reader.read_uint16()
        self.type = reader.read_int16()
        self.qualifier = self.get_qualifier()

    def resolve_objects(self, frameItems):
        if self.objects:
            return self.objects
        objects = self.objects = []
        for item in frameItems.items:
            try:
                if  self.qualifier not in item.properties.loader.qualifiers:
                    continue
                if item.objectType != self.type:
                    continue
                objects.append(item.handle)
            except AttributeError:
                pass
        return objects

    def write(self, reader: ByteIO):
        reader.write_uint16(self.objectInfo)
        reader.write_int16(self.type)


class Parameter(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.code = 0
        self.loader = None

    def read(self):
        reader = self.reader
        current_position = reader.tell()
        size = reader.read_int16()
        self.code = reader.read_int16()
        print(self.code,len(parameter_loaders))
        self.loader = parameter_loaders[self.code]
        if self.loader:
            print('Parameter loader',self.loader)
            self.loader = self.loader(reader)
            self.loader.read()
        reader.seek(current_position + size)

    def get_name(self):
        return get_name(self.code)

    def write(self, reader: ByteIO):
        new_reader = ByteIO(mode='wb')
        new_reader.write_int16(self.code)
        self.loader.write(new_reader.read_bytes())
        reader.write_uint16(len(new_reader) + 2)
        reader.write_int16(new_reader)


class Action(AceCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = ACE_FLAGS.copy()
        self.other_flags = ACE_OTHERFLAGS.copy()
        self.def_type = 0
        self.object_info = 0
        self.num = 0
        self.object_info_list = 0
        self.object_type = 0
        self.items = []
        self.system_dict = action_system_dict
        self.extension_dict = action_extension_dict

    def read(self):
        reader = self.reader
        current_position = reader.tell()
        size = 50 #reader.read_uint16()
        self.object_type = reader.read_int16()
        self.num = reader.read_int16()
        self.object_info = reader.read_uint16()
        self.object_info_list = reader.read_int16()
        self.flags.setFlags(reader.read_uint8())
        self.other_flags.setFlags(reader.read_uint8())
        number_of_parameters = reader.read_int8()
        self.def_type = reader.read_int8()
        self.items = [self.new(Parameter, reader) for _ in range(number_of_parameters)]
        reader.seek(current_position + size)

    def write(self, reader: ByteIO):
        new_reader = ByteIO(mode='wb')
        new_reader.write_int16(self.object_type)
        new_reader.write_int16(self.num)
        new_reader.write_uint16(self.object_info)
        new_reader.write_int16(self.object_info_list)
        new_reader.write_uint8(self.flags.getFlags())
        new_reader.write_uint8(self.other_flags.getFlags())
        new_reader.write_int8(len(self.items))
        new_reader.write_int8(self.def_type)

        for item in self.items:
            item.write(new_reader)

        reader.write_uint16(len(new_reader) + 2)
        reader.write_bytes(new_reader.read_bytes())

    def get_extension_num(self):
        return self.num - 80


class Condition(AceCommon):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = ACE_FLAGS.copy()
        self.other_flags = ACE_OTHERFLAGS.copy()
        self.def_type = 0
        self.object_type = 0
        self.num = 0
        self.object_info = 0
        self.identifier = 0
        self.object_info_list = 0
        self.items = []
        self.system_dict = conditions_system_dict
        self.extension_dict = conditions_extension_dict

    def read(self):
        reader = self.reader
        current_position = reader.tell()
        size = reader.read_uint16()
        self.object_type = reader.read_int16()
        self.num = reader.read_int16()
        self.object_info = reader.read_uint16()
        self.object_info_list = reader.read_int16()
        self.flags.setFlags(reader.read_uint8())
        self.other_flags.setFlags(reader.read_uint8())
        number_of_parameters = reader.read_int8()
        self.def_type = reader.read_int8()
        self.identifier = reader.read_int16()  # Event identifier

        self.items = [self.new(Parameter, reader)
                      for _ in range(number_of_parameters)]

        reader.seek(current_position + size)

    def write(self, reader: ByteIO):
        new_reader = ByteIO()
        new_reader.write_int16(self.object_type)
        new_reader.write_int16(self.num)
        new_reader.write_uint16(self.object_info)
        new_reader.write_int16(self.object_info_list)
        new_reader.write_uint8(self.flags.getFlags())
        new_reader.write_uint8(self.other_flags.getFlags())
        new_reader.write_uint8(len(self.items))
        new_reader.write_int8(self.def_type)
        new_reader.write_int16(self.identifier)

        for item in self.items:
            item.write(new_reader)

        reader.write_int16(len(new_reader) + 2)
        reader.write_bytes(new_reader.read_bytes())

    def get_extension_num(self):
        return - self.num - 80 - 1


class EventGroup(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.flags = GROUP_FLAGS.copy()
        self.is_restricted = 0
        self.restrictCpt = 0
        self.identifier = 0
        self.undo = 0
        self.conditions = []
        self.actions = []

    def read(self):
        reader = self.reader
        current_position = reader.tell()
        size = reader.read_int16() * -1

        number_of_conditions = reader.read_uint8()
        number_of_actions = reader.read_uint8()
        self.flags.setFlags(reader.read_uint8())

        compat = self.settings.get('compat', False)
        if self.settings['build'] >= 284 and not compat:
            reader.skip(2)
            self.is_restricted = reader.read_int32()
            self.restrictCpt = reader.read_int32()
        else:
            self.is_restricted = reader.read_int16()  # If the group is inhibited
            self.restrictCpt = reader.read_int16()  # Counter
            self.identifier = reader.read_int16()  # Unique identifier
            self.undo = reader.read_int16()  # Identifier for UNDO

        self.conditions = [self.new(Condition, reader)
                           for _ in range(number_of_conditions)]

        self.actions = [self.new(Action, reader) for _ in range(number_of_actions)]

        reader.seek(current_position + size)

    def write(self, reader: ByteIO):
        new_reader = ByteIO()

        new_reader.write_uint8(len(self.conditions))
        new_reader.write_uint8(len(self.actions))
        new_reader.write_uint16(self.flags.getFlags())
        new_reader.write_int16(self.is_restricted)
        new_reader.write_int16(self.restrictCpt)
        new_reader.write_int16(self.identifier)
        new_reader.write_int16(self.undo)

        for condition in self.conditions:
            condition.write(new_reader)

        for action in self.actions:
            action.write(new_reader)

        reader.write_int16((len(new_reader) + 2) * -1)
        reader.write_bytes(new_reader.read_bytes())


class Events(DataLoader):
    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.max_objects = 0
        self.max_object_info = 0
        self.number_of_players = 0
        self.qualifier_list = 0
        self.qualifiers = {}
        self.number_of_conditions = []
        self.items = []
        self.groups = []

    def read(self):
        reader = self.reader
        java = self.settings.get('java', False)
        while 1:
            identifier = reader.read_bytes(4)
            if identifier == HEADER:
                self.max_objects = max(300, reader.read_int16())
                self.max_object_info = reader.read_int16()
                self.number_of_players = reader.read_int16()
                self.number_of_conditions = [reader.read_int16()
                                             for _ in range(17)]
                self.qualifier_list = []
                self.qualifiers = qualifiers = {}
                qualifier_count = reader.read_int16()
                for _ in range(qualifier_count):
                    new_qualifier = self.new(Qualifier, reader)
                    self.qualifier_list.append(new_qualifier)
                    qualifiers[new_qualifier.qualifier] = new_qualifier

            elif identifier == EVENT_COUNT:
                # just ignoring here, we'll be getting
                # number of events in EVENTGROUP_DATA
                # anyway
                size = reader.read_int32()  # ignored
                if java:
                    if reader.read(4) == EVENTGROUP_DATA:  # iPhone
                        java = False
                        reader.rewind(4)

            elif identifier == EVENTGROUP_DATA:
                size = reader.read_int32()
                if java:
                    number_of_groups = reader.read_int32()
                    self.items.extend([self.new(EventGroup, reader)
                                       for _ in range(number_of_groups)])
                else:
                    end_position = reader.tell() + size
                    while 1:
                        self.items.append(self.new(EventGroup, reader))
                        if reader.tell() >= end_position:
                            break

            elif identifier == END:
                break
            else:
                import code

                code.interact(local=locals())
                raise NotImplementedError(
                    'identifier %r not implemented (%s)' % (identifier, reader.tell()))

    def write(self, reader: ByteIO):
        java = self.settings.get('java', False)

        event_reader = ByteIO(mode='wb')
        if java:
            event_reader.write_int32(len(self.items))
        for eventGroup in self.items:
            eventGroup.write(event_reader)

        reader.write_bytes(HEADER)
        reader.write_int16(self.max_objects)
        reader.write_int16(self.max_object_info)
        reader.write_int16(self.number_of_players)
        for item in self.number_of_conditions:
            reader.write_int16(item)
        reader.write_int16(len(self.qualifiers))
        for item in self.qualifiers:
            item.write(reader)

        reader.write_bytes(EVENT_COUNT)
        reader.write_int32(len(event_reader))
        if java:
            reader.write_int32(len(self.items))

        if self.items:
            reader.write_bytes(EVENTGROUP_DATA)
            reader.write_int32(len(event_reader))
            reader.write_bytes(event_reader.read_bytes())

        reader.write_bytes(END)


action_system_dict = {
    2: {
        80: 'PasteActive',
        81: 'BringToFront',  # BringActiveToFront
        82: 'BringToBack',  # BringActiveToBack
        83: 'AddBackdrop',
        84: 'ReplaceColor',
        85: 'SetScale',
        86: 'SetXScale',
        87: 'SetYScale',
        88: 'SetAngle',
        89: 'LoadActiveFrame'
    },
    3: {  # String
        80: 'EraseText',
        81: 'DisplayText',
        82: 'FlashText',
        83: 'SetTextColor',
        84: 'SetParagraph',
        85: 'PreviousParagraph',
        86: 'NextParagraph',
        87: 'DisplayAlterableString',
        88: 'SetString'
    },
    4: {
        80: 'AskQuestion'
    },
    7: {
        80: 'SetCounterValue',
        81: 'AddCounterValue',
        82: 'SubtractCounterValue',
        83: 'SetMinimumValue',
        84: 'SetMaximumValue',
        85: 'SetCounterColor1',
        86: 'SetCounterColor2'
    },
    8: {
        80: 'RTFSETXPOS',
        81: 'RTFSETYPOS',
        82: 'RTFSETZOOM',
        83: 'RTFSELECT_CLEAR',
        84: 'RTFSELECT_WORDSTRONCE',
        85: 'RTFSELECT_WORDSTRNEXT',
        86: 'RTFSELECT_WORDSTRALL',
        87: 'RTFSELECT_WORD',
        88: 'RTFSELECT_LINE',
        89: 'RTFSELECT_PARAGRAPH',
        90: 'RTFSELECT_PAGE',
        91: 'RTFSELECT_ALL',
        92: 'RTFSELECT_RANGE',
        93: 'RTFSELECT_BOOKMARK',
        94: 'RTFSETFOCUSWORD',
        95: 'RTFHLIGHT_OFF',
        96: 'RTFHLIGHTTEXT_COLOR',
        97: 'RTFHLIGHTTEXT_BOLD',
        98: 'RTFHLIGHTTEXT_ITALIC',
        99: 'RTFHLIGHTTEXT_UNDERL',
        100: 'RTFHLIGHTTEXT_OUTL',
        101: 'RTFHLIGHTBACK_COLOR',
        102: 'RTFHLIGHTBACK_RECT',
        103: 'RTFHLIGHTBACK_MARKER',
        104: 'RTFHLIGHTBACK_HATCH',
        105: 'RTFHLIGHTBACK_INVERSE',
        106: 'RTFDISPLAY',
        107: 'RTFSETFOCUSPREV',
        108: 'RTFSETFOCUSNEXT',
        109: 'RTFREMOVEFOCUS',
        110: 'RTFAUTOON',
        111: 'RTFAUTOOFF',
        112: 'RTFINSERTSTRING',
        113: 'RTFLOADTEXT',
        114: 'RTFINSERTTEXT'
    },
    9: {
        80: 'RestartSubApplication',
        81: 'RestartSubApplicationFrame',
        82: 'NextSubApplicationFrame',
        83: 'PreviousSubApplicationFrame',
        84: 'EndSubApplication',
        85: 'LoadApplication',
        86: 'JumpSubApplicationFrame',
        87: 'SetSubApplicationGlobalValue',
        88: 'ShowSubApplication',
        89: 'HideSubApplication',
        90: 'SetSubApplicationGlobalString',
        91: 'PauseSubApplication',
        92: 'ResumeSubApplication'
    },
    -1: {
        0: 'Skip',
        1: 'SKIPMONITOR',
        2: 'ExecuteFixedProgram',
        3: 'SetGlobalValue',
        4: 'SubtractGlobalValue',
        5: 'AddGlobalValue',
        6: 'ActivateGroup',
        7: 'DeactivateGroup',
        8: 'ActivateMenu',
        9: 'DeactivateMenu',
        10: 'CheckMenu',
        11: 'UncheckMenu',
        12: 'ShowMenu',
        13: 'HideMenu',
        14: 'StartLoop',
        15: 'StopLoop',
        16: 'SetLoopIndex',
        17: 'SetRandomSeed',
        18: 'SendMenuCommand',
        19: 'SetGlobalString',
        20: 'SetClipboard',
        21: 'ClearClipboard',
        22: 'ExecuteEvaluatedProgram',
        23: 'OpenDebugger',
        24: 'PauseDebugger',
        25: 'ExtractBinaryFile',
        26: 'ReleaseBinaryFile',
        27: 'SetGlobalValueInt',
        28: 'SetGlobalValue2',
        29: 'SetGlobalValueDouble',
        30: 'SetGlobalValue3',
        31: 'AddGlobalValueInt',
        32: 'AddGlobalValue2',
        33: 'AddGlobalValueDouble',
        34: 'AddGlobalValue3',
        35: 'SubtractGlobalValueInt',
        36: 'SubtractGlobalValue2',
        37: 'SubtractGlobalValueDouble',
        38: 'SubtractGlobalValue3'
    },
    -7: {
        0: 'SetScore',
        1: 'SetLives',
        2: 'IgnoreControls',
        3: 'RestoreControls',
        4: 'AddScore',
        5: 'AddLives',
        6: 'SubtractScore',
        7: 'SubtractLives',
        8: 'ChangeControlType',
        9: 'ChangeInputKey',
        10: 'SetPlayerName'
    },
    -6: {
        0: 'HideCursor',
        1: 'ShowCursor'
    },
    -5: {
        0: 'CreateObject',
        1: 'CreateObjectByName'
    },
    -4: {
        0: 'SetTimer',
        1: 'ScheduleEvent',
        2: 'ScheduleEventTimes'
    },
    -3: {
        0: 'NextFrame',
        1: 'PreviousFrame',
        2: 'JumpToFrame',
        3: 'PauseApplication',
        4: 'EndApplication',
        5: 'RestartApplication',
        6: 'RestartFrame',
        7: 'CenterDisplay',
        8: 'CenterDisplayX',
        9: 'CenterDisplayY',
        10: 'LOADGAME',
        11: 'SAVEGAME',
        12: 'ClearScreen',
        13: 'ClearZone',
        14: 'FullscreenMode',
        15: 'WindowedMode',
        16: 'SetFrameRate',
        17: 'PauseApplicationWithKey',
        18: 'PauseApplication',
        19: 'EnableVsync',
        20: 'DisableVsync',
        21: 'SetVirtualWidth',
        22: 'SetVirtualHeight',
        23: 'SetFrameBackgroundColor',
        24: 'DeleteCreatedBackdrops',
        25: 'DeleteAllCreatedBackdrops',
        26: 'SetFrameWidth',
        27: 'SetFrameHeight',
        28: 'SaveFrame',
        29: 'LoadFrame',
        30: 'LoadApplication',
        31: 'PlayDemo',
        32: 'SetFrameEffect',
        33: 'SetFrameEffectParameter',
        34: 'SetFrameEffectImage',
        35: 'SetFrameAlphaCoefficient',
        36: 'SetFrameRGBCoefficient'
    },
    -2: {  # Sound and Music
        0: 'PlaySample',
        1: 'StopAllSamples',
        2: 'PlayMusic',
        3: 'StopMusic',
        4: 'PlayLoopingSample',
        5: 'PlayLoopingMusic',
        6: 'StopSample',
        7: 'PauseSample',
        8: 'ResumeSample',
        9: 'PauseMusic',
        10: 'ResumeMusic',
        11: 'PlayChannelSample',
        12: 'PlayLoopingChannelSample',
        13: 'PauseChannel',
        14: 'ResumeChannel',
        15: 'StopChannel',
        16: 'SetChannelPosition',
        17: 'SetChannelVolume',
        18: 'SetChannelPan',
        19: 'SetSamplePosition',
        20: 'SetMainVolume',
        21: 'SetSampleVolume',
        22: 'SetMainPan',
        23: 'SetSamplePan',
        24: 'PauseAllSounds',
        25: 'ResumeAllSounds',
        26: 'PlayMusicFile',
        27: 'PlayLoopingMusicFile',
        28: 'PlayChannelFileSample',
        29: 'PlayLoopingChannelFileSample',
        30: 'LockChannel',
        31: 'UnlockChannel',
        32: 'SetChannelFrequency',
        33: 'SetSampleFrequency'
    }
}

action_extension_dict = {
    1: 'SetPosition',
    2: 'SetX',
    3: 'SetY',
    4: 'Stop',
    5: 'Start',
    6: 'SetSpeed',
    7: 'SetMaximumSpeed',
    8: 'Wrap',
    9: 'Bounce',
    10: 'Reverse',
    11: 'NextMovement',
    12: 'PreviousMovement',
    13: 'SelectMovement',
    14: 'LookAt',
    15: 'StopAnimation',
    16: 'StartAnimation',
    17: 'ForceAnimation',
    18: 'ForceDirection',
    19: 'ForceSpeed',
    20: 'RestoreAnimation',
    21: 'RestoreDirection',
    22: 'RestoreSpeed',
    23: 'SetDirection',
    24: 'Destroy',
    25: 'SwapPosition',
    26: 'Hide',
    27: 'Show',
    28: 'FlashDuring',
    29: 'Shoot',
    30: 'ShootToward',
    31: 'SetAlterableValue',
    32: 'AddToAlterable',
    33: 'SubtractFromAlterable',
    34: 'SpreadValue',
    35: 'EnableFlag',
    36: 'DisableFlag',
    37: 'ToggleFlag',
    38: 'SetInkEffect',
    39: 'SetSemiTransparency',
    40: 'ForceFrame',
    41: 'RestoreFrame',
    42: 'SetAcceleration',
    43: 'SetDeceleration',
    44: 'SetRotatingSpeed',
    45: 'SetDirections',
    46: 'BranchNode',
    47: 'SetGravity',
    48: 'GoToNode',
    49: 'SetAlterableString',
    50: 'SetFontName',
    51: 'SetFontSize',
    52: 'SetBold',
    53: 'SetItalic',
    54: 'SetUnderline',
    55: 'SetStrikeOut',
    56: 'SetTextColor',
    57: 'BringToFront',
    58: 'BringToBack',
    59: 'MoveBehind',
    60: 'MoveInFront',
    61: 'MoveToLayer',
    62: 'AddToDebugger',
    63: 'SetEffect',
    64: 'SetEffectParameter',
    65: 'SetAlphaCoefficient',
    66: 'SetRGBCoefficient',
    67: 'SetEffectImage',
    68: 'SetFriction',
    69: 'SetElasticity',
    70: 'ApplyImpulse',
    71: 'ApplyAngularImpulse',
    72: 'ApplyForce',
    73: 'ApplyTorque',
    74: 'SetLinearVelocity',
    75: 'SetAngularVelocity',
    76: 'Foreach',
    77: 'ForeachTwoObjects',
    78: 'StopForce',
    79: 'StopTorque',
    80: 'SetDensity',
    81: 'SetGravityScale'
}
conditions_system_dict = {
    2: {
        -81: 'ObjectClicked'  # SPRCLICK
    },
    4: {
        -83: 'AnswerMatches',
        -82: 'AnswerFalse',
        -81: 'AnswerTrue'
    },
    7: {
        -81: 'CompareCounter'
    },
    9: {
        -84: 'SubApplicationPaused',
        -83: 'SubApplicationVisible',
        -82: 'SubApplicationFinished',
        -81: 'SubApplicationFrameChanged'
    },
    -2: {
        -1: 'SampleNotPlaying',
        -9: 'ChannelPaused',
        -8: 'ChannelNotPlaying',
        -7: 'MusicPaused',
        -6: 'SamplePaused',
        -5: 'MusicFinished',
        -4: 'NoMusicPlaying',
        -3: 'NoSamplesPlaying',
        -2: 'SpecificMusicNotPlaying'
    },
    -7: {
        -1: 'PLAYERPLAYING',
        -6: 'PlayerKeyDown',
        -5: 'PlayerDied',
        -4: 'PlayerKeyPressed',
        -3: 'NumberOfLives',
        -2: 'CompareScore'
    },
    -6: {
        -2: 'KeyDown',
        -12: 'MouseWheelDown',
        -11: 'MouseWheelUp',
        -10: 'MouseVisible',
        -9: 'AnyKeyPressed',
        -8: 'WhileMousePressed',
        -7: 'ObjectClicked',
        -6: 'MouseClickedInZone',
        -5: 'MouseClicked',
        -4: 'MouseOnObject',
        -3: 'MouseInZone',
        -1: 'KeyPressed'
    },
    -5: {
        -2: 'AllObjectsInZone',  # AllObjectsInZone_Old
        -23: 'PickObjectsInLine',
        -22: 'PickFlagOff',
        -21: 'PickFlagOn',
        -20: 'PickAlterableValue',
        -19: 'PickFromFixed',
        -18: 'PickObjectsInZone',
        -17: 'PickRandomObject',
        -16: 'PickRandomObjectInZone',
        -15: 'CompareObjectCount',
        -14: 'AllObjectsInZone',
        -13: 'NoAllObjectsInZone',
        -12: 'PickFlagOff',  # PickFlagOff_Old
        -11: 'PickFlagOn',  # PickFlagOn_Old
        -8: 'PickAlterableValue',  # PickAlterableValue_Old
        -7: 'PickFromFixed',  # PickFromFixed_Old
        -6: 'PickObjectsInZone',  # PickObjectsInZone_Old
        -5: 'PickRandomObject',  # PickRandomObject_Old
        -4: 'PickRandomObjectInZoneOld',
        -3: 'CompareObjectCount',  # CompareObjectCount_Old
        -1: 'NoAllObjectsInZone'  # NoAllObjectsInZone_Old
    },
    -4: {
        -8: 'Every',
        -7: 'TimerEquals',
        -6: 'OnTimerEvent',
        -5: 'CompareAwayTime',
        -4: 'Every',
        -3: 'TimerEquals',
        -2: 'TimerLess',
        -1: 'TimerGreater'
    },
    -3: {
        -1: 'StartOfFrame',
        -10: 'FrameSaved',
        -9: 'FrameLoaded',
        -8: 'ApplicationResumed',
        -7: 'VsyncEnabled',
        -6: 'IsLadder',
        -5: 'IsObstacle',
        -4: 'EndOfApplication',
        -3: 'LEVEL',
        -2: 'EndOfFrame'
    },
    -1: {
        -1: 'Always',
        -2: 'Never',
        -3: 'Compare',
        -4: 'RestrictFor',
        -5: 'Repeat',
        -6: 'Once',
        -7: 'NotAlways',
        -8: 'CompareGlobalValue',
        -9: 'Remark',
        -10: 'NewGroup',
        -11: 'GroupEnd',
        -12: 'GroupActivated',
        -13: 'RECORDKEY',
        -14: 'MenuSelected',
        -15: 'FilesDropped',
        -16: 'OnLoop',
        -17: 'MenuChecked',
        -18: 'MenuEnabled',
        -19: 'MenuVisible',
        -20: 'CompareGlobalString',
        -21: 'CloseSelected',
        -22: 'ClipboardDataAvailable',
        -23: 'OnGroupActivation',
        -24: 'OrFiltered',
        -25: 'OrLogical',
        -26: 'Chance',
        -27: 'ElseIf',
        -28: 'CompareGlobalValueIntEqual',
        -29: 'CompareGlobalValueIntNotEqual',
        -30: 'CompareGlobalValueIntLessEqual',
        -31: 'CompareGlobalValueIntLess',
        -32: 'CompareGlobalValueIntGreaterEqual',
        -33: 'CompareGlobalValueIntGreater',
        -34: 'CompareGlobalValueDoubleEqual',
        -35: 'CompareGlobalValueDoubleNotEqual',
        -36: 'CompareGlobalValueDoubleLessEqual',
        -37: 'CompareGlobalValueDoubleLess',
        -38: 'CompareGlobalValueDoubleGreaterEqual',
        -39: 'CompareGlobalValueDoubleGreater',
        -40: 'RunningAs'
    }
}

conditions_extension_dict = {
    -1: 'AnimationFrame',
    -2: 'AnimationFinished',
    -3: 'AnimationPlaying',
    -4: 'IsOverlapping',
    -5: 'Reversed',
    -6: 'Bouncing',
    -7: 'MovementStopped',
    -8: 'FacingInDirection',
    -9: 'InsidePlayfield',
    -10: 'OutsidePlayfield',
    -11: 'EnteringPlayfield',
    -12: 'LeavingPlayfield',
    -13: 'OnBackgroundCollision',
    -14: 'OnCollision',
    -15: 'CompareSpeed',
    -16: 'CompareY',
    -17: 'CompareX',
    -18: 'CompareDeceleration',
    -19: 'CompareAcceleration',
    -20: 'NodeReached',
    -21: 'PathFinished',
    -22: 'NearWindowBorder',
    -23: 'IsOverlappingBackground',
    -24: 'FlagOff',
    -25: 'FlagOn',
    -26: 'CompareFixedValue',
    -27: 'CompareAlterableValue',
    -28: 'ObjectInvisible',
    -29: 'ObjectVisible',
    -30: 'ObjectsInZone',
    -31: 'NoObjectsInZone',
    -32: 'NumberOfObjects',
    -33: 'AllDestroyed',
    -34: 'PickRandom',
    -35: 'NamedNodeReached',
    -36: 'CompareAlterableString',
    -37: 'IsBold',
    -38: 'IsItalic',
    -39: 'IsUnderline',
    -40: 'IsStrikeOut',
    -41: 'OnObjectLoop',
    -42: 'CompareAlterableValueInt',
    -43: 'CompareAlterableValueDouble'
}


if __name__ == '__main__':
    reader = ByteIO(path=r"E:\PYTHON_STUFF\CTF_ReaderV2\DUMP\customnight\CHUNKS\FRAMES\Frame 21\FRAMEEVENTS.chunk")
    e = Events(reader)
    e.update_settings(build = 290)
    e.read()