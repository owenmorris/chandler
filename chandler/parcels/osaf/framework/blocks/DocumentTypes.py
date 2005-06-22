__parcel__ = 'osaf.framework.blocks'

import repository.schema.Types as CoreTypes
import wx
from application import schema


class SizeType(schema.Struct):
    __slots__ = 'width', 'height'


class PositionType(schema.Struct):
    __slots__ = 'x', 'y'


class RectType(schema.Struct):
    __slots__ = 'top', 'left', 'bottom', 'right'


class ColorType(schema.Struct):
    __slots__ = 'red', 'green', 'blue', 'alpha'

    def wxColor(self):
        # Make a wx color
        return wx.Color(self.red, self.green, self.blue)

