#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import wx
from struct import pack, unpack
from application import schema


class SizeType(schema.Struct):
    __slots__ = 'width', 'height'

    @classmethod
    def writeValue(cls, value, itemWriter, buffer):
        bytes = pack('>ii', value.width, value.height)
        buffer.append(bytes)
        return 8

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+8, cls(*unpack('>ii', data[offset:offset+8]))


class PositionType(schema.Struct):
    __slots__ = 'x', 'y'

    @classmethod
    def writeValue(cls, value, itemWriter, buffer):
        bytes = pack('>ii', value.x, value.y)
        buffer.append(bytes)
        return 8

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+8, cls(*unpack('>ii', data[offset:offset+8]))


class RectType(schema.Struct):
    __slots__ = 'top', 'left', 'bottom', 'right'

    @classmethod
    def writeValue(cls, value, itemWriter, buffer):
        bytes = pack('>iiii', value.top, value.left, value.bottom, value.right)
        buffer.append(bytes)
        return 16

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+16, cls(*unpack('>iiii', data[offset:offset+16]))


class ColorType(schema.Struct):
    __slots__ = 'red', 'green', 'blue', 'alpha'

    def wxColor(self):
        # Make a wx color
        return wx.Color(self.red, self.green, self.blue)

    def toTuple(self):
        # is there a more pythonic way of doing this?
        return (self.red, self.green, self.blue)

    @classmethod
    def writeValue(cls, value, itemWriter, buffer):
        bytes = pack('BBBB', value.red, value.green, value.blue, value.alpha)
        buffer.append(bytes)
        return 4

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+4, cls(*unpack('BBBB', data[offset:offset+4]))
