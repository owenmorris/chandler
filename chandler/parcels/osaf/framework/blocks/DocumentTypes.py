
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
        return Size(int(width), int(height))

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
