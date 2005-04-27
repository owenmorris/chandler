
import repository.schema.Types as CoreTypes
import wx

class SizeType(object):
    __slots__ = 'width', 'height'
    
    def __repr__(self):
        return "(%sw, %sh)" % (self.width, self.height)
    
class SizeStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (width, height) = data.split(",")
        size = SizeType()
        setattr (size, 'width', float(width))
        setattr (size, 'height', float(height))
        return size


class PositionType(object):
    __slots__ = 'x', 'y'
    
    def __repr__(self):
        return "(%sx, %sy)" % (self.x, self.y)
    
class PositionStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (x, y) = data.split(",")
        position = PositionType()
        setattr (position, 'x', float(x))
        setattr (position, 'y', float(y))
        return position


class RectType(object):
    __slots__ = 'top', 'left', 'bottom', 'right'

    def __repr__(self):
        return "(%st, %sl, %sb, %sr)" % (self.top, self.left, self.bottom, self.right)

class RectStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (top, left, bottom, right) = data.split(",")
        rect = RectType()
        setattr (rect, 'top', float(top))
        setattr (rect, 'left', float(left))
        setattr (rect, 'bottom', float(bottom))
        setattr (rect, 'right', float(right))
        return rect


class ColorType(object):
    __slots__ = 'red', 'green', 'blue', 'alpha'
    def wxColor(self):
        # Make a wx color
        return wx.Color(self.red, self.green, self.blue)

    def __repr__(self):
        return "(%sr, %sg, %sb, %sa)" % (self.red, self.green, self.blue, self.alpha)
        
class ColorStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (red, green, blue, alpha) = data.split(",")
        color = ColorType()
        setattr (color, 'red', int(red))
        setattr (color, 'green', int(green))
        setattr (color, 'blue', int(blue))
        setattr (color, 'alpha', int(alpha))
        return color

    def makeString(self, value):
        return "%d,%d,%d,%d" % (int(value.red), int(value.green), 
                                int(value.blue), int(value.alpha))
    