__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

class DocumentFactory:
    def __init__(self, rep, parent=None):
        if not parent:
            self._container = rep.find("//Document")
        else:
            self._container = parent
        self._kind = rep.find("//Schema/DocumentSchema/Document")
        
    def NewItem(self, name="", type="document", content=None,
                style=None, notifications=None):
        item = Document(name, self._container, self._kind)
        item.setAttributeValue("blocktype", type)
        item.setAttributeValue("contentspec", content or {})
        item.setAttributeValue("style", style or {})
        item.setAttributeValue("notifications", notifications or {})
        
        return item


class Document(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(Document, self).__init__(name, parent, kind, **_kwds)
