__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

class BlockFactory:
    def __init__(self, rep, parent=None):
        if not parent:
            self._container = rep.find("//Document")
        else:
            self._container = parent
        self._kind = rep.find("//Schema/DocumentSchema/Block")
        
    def NewItem(self, name="", type="", content=None,
                style=None, notifications=None, isOpen=False,
                positionInParent=0):
        item = Block(name, self._container, self._kind)
        item.setAttributeValue("blocktype", type)
        item.setAttributeValue("contentspec", content or {})
        item.setAttributeValue("style", style or {})
        item.setAttributeValue("notifications", notifications or {})
        item.setAttributeValue("isOpen", isOpen)
        item.setAttributeValue("positionInParent", positionInParent)
        
        return item


class Block(Item):
    pass
