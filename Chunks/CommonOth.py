# Copyright (c) Mathias Kaerlev 2012.

# This file is part of Anaconda.

# Anaconda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Anaconda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Anaconda.  If not, see <http://www.gnu.org/licenses/>.

from Bytereader import ByteReader
import byteflag
from Loader import DataLoader

def isQualifier(objectInfo):
    return byteflag.getFlag(objectInfo, 15)

def getQualifier(objectInfo):
    return objectInfo & 0b11111111111
    
EXTENSION_BASE = -1
def initialize():
    if EXTENSION_BASE == -1:
        #global EXTENSION_BASE
        from Chunks.ObjectInfo import EXTENSION_BASE

class Empty(DataLoader):
    def read(self, reader):
        if reader.read() != '':
            raise Exception('expected empty chunk')
                
    def write(self, reader):
        return # nothing to write

class SingleByte(DataLoader):
    value = None

    def read(self, reader):
        self.value = reader.readByte()
    
    def write(self, reader):
        reader.writeByte(self.value)

class Rectangle(DataLoader):
    left = None
    top = None
    right = None
    bottom = None
    
    def read(self, reader):
        self.left = reader.readInt()
        self.top = reader.readInt()
        self.right = reader.readInt()
        self.bottom = reader.readInt()
    
    def write(self, reader):
        reader.writeInt(self.left)
        reader.writeInt(self.top)
        reader.writeInt(self.right)
        reader.writeInt(self.bottom)

class _ObjectInfoMixin:
    def getObjects(self, frameItems):
        return frameItems.fromHandle(self.objectInfo)
    
    def isQualifier(self):
        return isQualifier(self.objectInfo)
    
    def getQualifier(self):
        return getQualifier(self.objectInfo)

class _ObjectTypeMixin:
    def getType(self):
        initialize()
        if self.objectType < EXTENSION_BASE:
            return self.objectType
        return EXTENSION_BASE
    
    def getTypeName(self):
        from mmfparser.data.chunkloaders.objectinfo import getObjectType
        return getObjectType(self.objectType)
    
    def hasObjectInfo(self):
        return self.objectType >= 2
        
    def getExtension(self, extensionChunk):
        initialize()
        if self.getType() != EXTENSION_BASE:
            raise Exception('type is not an extension')
        return extensionChunk.fromHandle(
            self.objectType - EXTENSION_BASE)

def getType(_AceCommon):
    initialize()
    if self.objectType < EXTENSION_BASE:
        return self.objectType
    return EXTENSION_BASE

def _AceCommon(DataLoader):
    def getObjects(self, frameItems):
        return frameItems.fromHandle(self.objectInfo)
    
    def isQualifier(self):
        return isQualifier(self.objectInfo)
    
    def getQualifier(self):
        return getQualifier(self.objectInfo)
    
    def getName(self):
        if self.name is None:
            self.name = getName(self.objectType, self.num, 
                self.systemDict, self.extensionDict)
        return self.name
            
    def getType(self):
        return getType(self)
    
    def getTypeName(self):
        from mmfparser.data.chunkloaders.objectinfo import getObjectType
        return getObjectType(self.objectType)
    
    def hasObjectInfo(self):
        return self.objectType >= 2
        
    def getExtension(self, extensionChunk):
        initialize()
        if self.getType() != EXTENSION_BASE:
            raise Exception('type is not an extension')
        return extensionChunk.fromHandle(
            self.objectType - EXTENSION_BASE)

def getName(objectType, num, systemDict, extensionDict):
    if objectType in systemDict and num in systemDict[objectType]:
        return systemDict[objectType][num]
    elif num in extensionDict:
        return extensionDict[num]