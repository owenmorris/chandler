__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from application.Application import app
from wxPython.wx import *

class Block(Item):
    def __init__(self, name, parent=None,
                 label=None,
                 id=-1,
                 orientation=None,
                 value=None,
                 choices=None,
                 dimensions=1,
                 style=0,
                 weight=1,
                 flag=wxEXPAND,
                 border=0,
                 fontpoint=12,
                 fontfamily=wxSWISS,
                 fontstyle=wxNORMAL,
                 fontweight=wxNORMAL,
                 fontunderline=False,
                 fontname=None,
                 
                 contentspec=None,
                 notifications=None,
                 isOpen=False,
                 **_kwds):
        if not parent:
            self._container = app.repository.find('//Document')
        else:
            self._container = parent
        self._kind = app.repository.find(self.GetSchemaLocation())
        super(Block, self).__init__(name, self._container, 
                                    self._kind, **_kwds)
        
        self.style = {}

        self.style['label'] = label or ''
        self.style['id'] = id
        self.style['orientation'] = orientation or wxVERTICAL
        self.style['value'] = value or ''
        self.style['choices'] = choices or []
        self.style['dimensions'] = 1
        self.style['style'] = style
        self.style['weight'] = weight
        self.style['flag'] = flag
        self.style['border'] = border

        self.style['fontpoint'] = fontpoint
        self.style['fontfamily'] = fontfamily
        self.style['fontstyle'] = fontstyle
        self.style['fontweight'] = fontweight
        self.style['fontunderline'] = fontunderline
        self.style['fontname'] = fontname or 'Arial'


        self.contentspec = contentspec or {}
        self.notifications = notifications or {}
        self.isOpen = isOpen
        
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Block'
    
    def AddToSizer(self, item, sizer):
        if sizer != None:
            sizer.Add(item, self.style['weight'], self.style['flag'],
                      self.style['border'])
    