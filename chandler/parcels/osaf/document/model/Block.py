__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from application.Application import app
from wxPython.wx import *

class Block(Item):
    def __init__(self, name, parent=None, positionInParent=0, **_kwds):
        if not parent:
            self._container = app.repository.find('//Document')
        else:
            self._container = parent
        self._kind = app.repository.find(self.GetSchemaLocation())
        super(Block, self).__init__(name, self._container, 
                                    self._kind, **_kwds)
        
        self.positionInParent = positionInParent
        self.contentspec = {}
        self.style = {}
        self.notifications = {}
        self.isOpen = False
        self.style['label'] = ''
        self.style['id'] = -1
        self.style['orientation'] = wxVERTICAL
        self.style['value'] = ''
        self.style['choices'] = []
        self.style['dimensions'] = 1
        self.style['style'] = 0
        self.style['weight'] = 1
        self.style['flag'] = 0
        self.style['border'] = 0
        
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Block'
    