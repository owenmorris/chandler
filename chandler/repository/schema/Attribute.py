
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.item.ItemRef import RefDict
from repository.schema.Kind import Kind


class Attribute(Item):
    
    def __init__(self, name, parent, kind):

        super(Attribute, self).__init__(name, parent, kind)
        self._status |= Item.SCHEMA | Item.PINNED

    def _fillItem(self, name, parent, kind, **kwds):

        super(Attribute, self)._fillItem(name, parent, kind, **kwds)
        self._status |= Item.SCHEMA | Item.PINNED
        
    def hasAspect(self, name):

        return self.hasAttributeValue(name)

    def getAspect(self, name, **kwds):

        if self.hasAttributeValue(name):
            return self.getAttributeValue(name)

        if self.hasAttributeValue('superAttribute'):
            return self.getAttributeValue('superAttribute').getAspect(name,
                                                                      **kwds)

        if self._kind is not None:
            aspectAttr = self._kind.getAttribute(name)
            if aspectAttr.hasAttributeValue('defaultValue'):
                return aspectAttr.getAttributeValue('defaultValue')
        
        return kwds.get('default', None)
