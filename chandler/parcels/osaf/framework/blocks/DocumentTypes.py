
import repository.schema.Types as CoreTypes

class Size:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __str__(self):
        return "%s,%s" % (self.width, self.height)

class SizeType(CoreTypes.Type):

    def makeValue(cls, data):
        (width, height) = data.split(",")
        return Size(float(width), float(height))

    def makeString(cls, data):
        return str(data)

    def recognizes(self, value):
        return isinstance(value, Size)

    def unserialize(self, data):
        return SizeType.makeValue(data)

    def getValue(self, itemHandler, data):
        fields = itemHandler.fields
        if fields:
            itemHandler.fields = None
        else:
            return self.unserialize(data)

        return Size(fields['width'], fields['height'])

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)

class Rect:
    def __init__(self, top, left, bottom, right):
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right

    def __str__(self):
        return "%s,%s,%s,%s" % (self.top, self.left, self.bottom, self.right)

class RectType(CoreTypes.Type):

    def makeValue(cls, data):
        (top, left, bottom, right) = data.split(",")
        return Rect(float(top), float(left), float(bottom), float(right))

    def makeString(cls, data):
        return str(data)

    def recognizes(self, value):
        return isinstance(value, Rect)

    def unserialize(self, data):
        return RectType.makeValue(data)

    def getValue(self, itemHandler, data):
        fields = itemHandler.fields
        if fields:
            itemHandler.fields = None
        else:
            return self.unserialize(data)

        return Rect(fields['top'], fields['left'], fields['bottom'], fields['right'])

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)

    
class Color:
    def __init__(self, red, green, blue, alpha):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def __str__(self):
        string = "%s,%s,%s,%s" % (self.red, self.green, self.blue, self.alpha)
        return string

class ColorType(CoreTypes.Type):

    def makeValue(cls, data):
        (red, green, blue, alpha) = data.split(",")
        return Color(int(red), int(green), int(blue), alpha=int(right))

    def makeString(cls, data):
        return str(data)

    def recognizes(self, value):
        return isinstance(value, Color)

    def unserialize(self, data):
        return ColorType.makeValue(data)

    def getValue(self, itemHandler, data):
        fields = itemHandler.fields
        if fields:
            itemHandler.fields = None
        else:
            return self.unserialize(data)

        return Color(fields['red'], fields['green'], fields['blue'], fields['alpha'])

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
