
import repository.schema.Types as CoreTypes

class SizeType(object):
    __slots__ = 'width', 'height'
    
class SizeStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (width, height) = data.split(",")
        size = SizeType()
        setattr (size, 'width', float(width))
        setattr (size, 'height', float(height))
        return size


class RectType(object):
    __slots__ = 'top', 'left', 'bottom', 'right'

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

class ColorStruct(CoreTypes.Struct):

    def makeValue(Struct, data):
        (red, green, blue, alpha) = data.split(",")
        color = ColorType()
        setattr (color, 'red', int(red))
        setattr (color, 'green', int(green))
        setattr (color, 'blue', int(blue))
        setattr (color, 'alpha', int(alpha))
        return color
