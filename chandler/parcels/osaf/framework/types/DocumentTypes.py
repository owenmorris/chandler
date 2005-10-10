
from struct import pack, unpack

import repository.schema.Types as CoreTypes
import wx
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
