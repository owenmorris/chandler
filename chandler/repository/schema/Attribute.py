
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from model.schema.Kind import Kind


class Attribute(Item):

    def refName(self, name):

        if name == 'Attributes' or name == 'InheritedAttributes':
            return self._name

        return super(Attribute, self).refName(name)

    def hasAspect(self, name):

        return self.hasAttribute(name)

    def getAspect(self, name, default=None):

        if self.hasAttribute(name):
            return self.getAttribute(name)

        if self.hasAttribute('SuperAttribute'):
            return self.getAttribute('SuperAttribute').getAspect(name, default)

        return default

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.items():
            if self.getAttributeAspect(attr[0], 'Persist', True):
                attr[1]._saveValue(attr[0], self, generator, withSchema)
