
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item
from model.schema.Kind import Kind
from model.schema.Attribute import Attribute


class AutoKind(object):

    def createAttribute(self, name, **kwds):

        kind = self._kind
        if kind is None:
            raise ValueError, 'Kind for %s cannot be None.' %(self)
        
        if kind.getItemClass() is not type(self):
            kind = self._createKind(kind)
            self._setKind(kind)

        attribute = kind.getAttribute(name)
        if attribute is None:
            attribute = self._createAttribute(kind, name, kwds)

        else:
            self._verifyAttribute(name, attribute, kwds)

        if kwds.has_key('value'):
            self._setValue(name, attribute, kwds['value'], kwds)

        return attribute

    def _createKind(self, superKind):

        cls = type(self)
        kindName = cls.__name__

        if superKind.getItemName() == kindName:
            raise ValueError, 'autokind %s for %s.%s would replace superKind %s' %(kindName, cls.__module__, kindName, superKind.getItemPath())
            
        kind = Kind(kindName, superKind.getItemParent(), superKind._kind)
        kind.addValue('superKinds', superKind)
        kind.setValue('classes', cls, 'python')

        return kind

    def _createAttribute(self, kind, name, kwds):

        attrKind = kind.getAttribute('kind')._kind
        attribute = Attribute(name, kind, attrKind)

        for aspect, value in kwds.iteritems():
            if aspect != 'value' and aspect != 'otherCardinality':
                attribute.setAttributeValue(aspect, value)

        kind.addValue('attributes', attribute, alias=name)
        
        return attribute

    def _verifyAttribute(self, name, attribute, kwds):

        for aspect, value in kwds.iteritems():
            if aspect != 'value' and aspect != 'otherCardinality':
                current = attribute.getAspect(aspect)
                if current != value:
                    raise ValueError, "redefining existing attribute %s's %s aspect from %s to %s" %(name, aspect, current, value)

    def _setValue(self, name, attribute, value, kwds):
        
        if isinstance(value, Item):
            otherName = kwds['otherName']
            if isinstance(value, AutoKind):
                cardinality = attribute.getAspect('cardinality')
                otherCardinality = kwds.get('otherCardinality', 'single')
                value.createAttribute(otherName,
                                      cardinality = otherCardinality,
                                      otherName = name)

            elif value.getAttributeAspect(otherName, 'otherName') != name:
                raise ValueError, "%s's otherName doesn't match %s's otherName" %(name, otherName)
                
        self.setValue(name, value)
