#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from application import schema
from chandlerdb.persistence.c import Record


class SizeType(schema.Struct):
    __slots__ = 'width', 'height'

    @classmethod
    def writeValue(cls, value, itemWriter, record):
        record += (Record.INT, value.width, Record.INT, value.height)
        return 0

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+2, cls(*data[offset:offset+2])


class PositionType(schema.Struct):
    __slots__ = 'x', 'y'

    @classmethod
    def writeValue(cls, value, itemWriter, record):
        record += (Record.INT, value.x, Record.INT, value.y)
        return 0

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+2, cls(*data[offset:offset+2])


class RectType(schema.Struct):
    __slots__ = 'top', 'left', 'bottom', 'right'

    @classmethod
    def writeValue(cls, value, itemWriter, record):
        record += (Record.INT, value.top, Record.INT, value.left,
                   Record.INT, value.bottom, Record.INT, value.right)
        return 0

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+4, cls(*data[offset:offset+4])


class ColorType(schema.Struct):
    __slots__ = 'red', 'green', 'blue', 'alpha'

    def wxColor(self):
        # Make a wx color
        return wx.Color(self.red, self.green, self.blue)

    def toTuple(self):
        # is there a more pythonic way of doing this?
        return (self.red, self.green, self.blue)

    @classmethod
    def writeValue(cls, value, itemWriter, record):
        record += (Record.BYTE, value.red, Record.BYTE, value.green,
                   Record.BYTE, value.blue, Record.BYTE, value.alpha)
        return 0

    @classmethod
    def readValue(cls, itemReader, offset, data):
        return offset+4, cls(*data[offset:offset+4])
