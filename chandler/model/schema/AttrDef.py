
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from Kind import Kind

class AttrDef(Item):

    def refName(self, name):

        if name == 'AttrDefs' or name == 'InheritedAttrDefs':
            return self._name

        return super(AttrDef, self).refName(name)

    def hasAspect(self, name):

        return self.hasAttribute(name)

    def getAspect(self, name, default=None):

        if self.hasAttribute(name):
            return self.getAttribute(name)

        return default

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.items():
            if self.getAttrAspect(attr[0], 'Persist', True):
                attr[1]._xmlValue(attr[0], self, '\n  ',
                                  generator, withSchema)
