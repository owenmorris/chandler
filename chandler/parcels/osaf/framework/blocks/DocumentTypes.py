__parcel__ = 'osaf.framework.blocks'

import repository.schema.Types as CoreTypes
import wx
from application import schema

class SizeType(schema.Struct):
    __slots__ = 'width', 'height'

    def __repr__(self):
        return "(%sw, %sh)" % (self.width, self.height)

class SizeStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (width, height) = data.split(",")
        return SizeType(float(width),float(height))


class PositionType(schema.Struct):
    __slots__ = 'x', 'y'

    def __repr__(self):
        return "(%sx, %sy)" % (self.x, self.y)

class PositionStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (x, y) = data.split(",")
        return PositionType(float(x),float(y))


class RectType(schema.Struct):
    __slots__ = 'top', 'left', 'bottom', 'right'

    def __repr__(self):
        return "(%st, %sl, %sb, %sr)" % (self.top, self.left, self.bottom, self.right)

class RectStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (top, left, bottom, right) = data.split(",")
        return RectType(float(top), float(left), float(bottom), float(right))


class ColorType(schema.Struct):
    __slots__ = 'red', 'green', 'blue', 'alpha'
    def wxColor(self):
        # Make a wx color
        return wx.Color(self.red, self.green, self.blue)

    def __repr__(self):
        return "(%sr, %sg, %sb, %sa)" % (self.red, self.green, self.blue, self.alpha)

class ColorStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (red, green, blue, alpha) = data.split(",")
        return ColorType(int(red),int(green), int(blue), int(alpha))

    def makeString(self, value):
        return "%d,%d,%d,%d" % (int(value.red), int(value.green),
                                int(value.blue), int(value.alpha))
