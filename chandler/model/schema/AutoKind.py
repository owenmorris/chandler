
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item
from model.schema.Kind import Kind
from model.schema.Attribute import Attribute


class AutoKind(object):
    """A second superclass for items to ease programmatic creation of schema.

    AutoKind is to be used as an additional superclass for items to ease the
    programmatic creation of schema information for attributes. This is the
    supported way of creating ad-hoc attributes, that is attributes that are
    not originally described in outside schema XML files.

    Unless the item is already of a kind specific to its class, that is, the
    item's current kind 'python' mapping for its 'classes' attribute is the
    item's class, AutoKind creates a kind, specific to the item's class,
    named after this class, as a subkind of the item's current kind, unless
    it exists already. This new kind is created as a sibling of the item's
    current kind and can be used to create more items of the same kind and
    class.
    
    AutoKind comes with one public API, createAttribute() which takes a
    name and a number of keyword arguments which describe the aspects and
    initial value of the attribute to create as listed below:

    For an attribute intended to contain one or several literal values:
        - cardinality: one of 'single', 'dict', or 'list'.
                       Defaults to 'single'.
        - type: a type item such as //Schema/Model/Integer.
                       Defaults to no type being set.
        - defaultValue: a value to return as default when no value is set
                        for this attribute. By default, an attribute has no
                        default value and it is an error to attempt to
                        retrieve the non-existent value of an attribute.
        - persist: False to make values for this attribute be transient,
                   that is, not persisted. Defaults to True, values for this
                   attribute are persisted when the item is saved.
        - required: True to make this attribute to be required to have a
                    value. Defaults to False.

    For an attribute intended to contain one or several item reference
    values:
        - cardinality: one of 'single' or 'list'. Defaults to 'single.
        - persist: see above
        - required: see above
        - otherName: the name of the attribute on the referenced item to use
                     to attach to. This attribute is required.
        - otherCardinality: when the attribute on the referenced item to use
                            to attach to is not defined, this aspect
                            describes the cardinality to use to create the
                            other attribute. This is required only when the
                            other attribute does not exist and needs to be
                            created with a non-default cardinality.

    To specify the initial value of an attribute use the 'value' keyword.
    It is an error to redefine aspects on an existing attribute. That is,
    createAttribute() can be called repeatedly with the same attribute name
    as long as no existing aspects change.

    For example:
        - create a single valued String typed attribute named 'foo' and
          assigned it the initial value 'bar'.
        item.createAttribute('foo', value='bar',
                              type=repository.find('//Schema/Model/String'))

        - create a list valued Integer typed attributed named 'foo' and assign
          it the initial value 5.
        item.createAttribute('foo', value=5, cardinality='list',
                              type=repository.find('//Schema/Model/Integer'))

        - create a reference from i1 to i2 attaching it to 'foo' on i1 and
          'bar' on i2.
        i1.createAttribute('foo', value=i2, otherName='bar')

        - create a list reference from i1 to i2 attaching it to 'foo' on i1 and
          'bar' on i2.
        i1.createAttribute('foo', value=i2, otherName='bar',
                            cardinality='list')

        - create a list reference from i1 to i2 attaching it to 'foo' on i1 and
          a multi-valued attribute 'bar' on i2.
        i1.createAttribute('foo', value=i2, otherName='bar',
                            cardinality='list', otherCardinality='list')
    """

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

        parent = superKind.getItemParent()
        kind = parent.getItemChild(kindName)

        if kind is not None:
            if kind.getItemClass() is not cls:
                raise ValueError, 'kind %s/%s already exists but is not specific to class %s.%s' %(parent.getItemPath(), kindName, cls.__module__, kindName)
        else:
            kind = Kind(kindName, parent, superKind._kind)
            
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
