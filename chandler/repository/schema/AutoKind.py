
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict
from repository.schema.Kind import Kind
from repository.schema.Types import Type
from repository.schema.Attribute import Attribute


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
        - deletePolicy: this aspect can be set to control what happens to a
                        referenced item when the referencing item is being
                        deleted. Possible values are 'remove', the default
                        and 'cascade', which causes the referenced item to
                        be deleted as well.
        - countPolicy: when the deletePolicy is 'cascade', the countPolicy
                       can be used to modify the delete behaviour to only 
                       delete the referenced item if its reference count is
                       0. The reference count of an item is defined by the
                       total number of references it holds in attributes
                       where the countPolicy is set to 'count'. By default,
                       the countPolicy is 'none'.

    To specify the initial value of an single-valued attribute use the 'value'
    keyword.
    To specify one or several initial values, or an empty collection, for a
    multi-valued attribute use the 'values' keyword instead. If 'values' is
    specified but 'cardinality' is not, the latter defaults to the type of
    'values', either 'list' or 'dict'.
    It is an error to redefine aspects on an existing attribute. That is,
    createAttribute() can be called repeatedly with the same attribute name
    as long as no existing aspects change.

    For example:
        - create a single valued String typed attribute named 'foo' and
          assigned it the initial value 'bar'.
        item.createAttribute('foo', value='bar',
                              type=repository.find('//Schema/Core/String'))

        - create a list valued Integer typed attributed named 'foo' and assign
          it the initial value 5.
        item.createAttribute('foo', value=5, cardinality='list',
                              type=repository.find('//Schema/Core/Integer'))

        - create a list valued Integer typed attributed named 'foo' and assign
          it the initial values 5, 6 and 7.
        item.createAttribute('foo', values=[5,6,7],
                              type=repository.find('//Schema/Core/Integer'))

        - create a dict valued Integer typed attributed named 'foo' and assign
          it the initial mapping values 'a': 5, 'b': 6 and 'c': 7.
        item.createAttribute('foo', values={'a':5,'b':6,'c':7},
                              type=repository.find('//Schema/Core/Integer'))

        - create a reference from i1 to i2 attaching it to 'foo' on i1 and
          'bar' on i2.
        i1.createAttribute('foo', value=i2, otherName='bar')

        - create a multi-valued reference from i1 to i2 attaching it to
          'foo' on i1 and  'bar' on i2.
        i1.createAttribute('foo', values=[i2], otherName='bar')

        - create a multi-valued reference from i1 to i2 attaching it to
          'foo' on i1 and 'bar' on i2.
        i1.createAttribute('foo', value=i2, otherName='bar',
                            cardinality='list')

        - create a single-valued reference attribute 'foo' on i1 that
          will attach to 'bar' on the other endpoint when set.
        i1.createAttribute('foo', otherName='bar')

        - create a multi-valued reference attribute 'foo' on i1 that
          will attach to 'bar' on the other endpoint when set.
        i1.createAttribute('foo', otherName='bar', cardinality='list')

        - create a multi-valued reference attribute 'foo' on i1 that
          will attach to 'bar' on the other endpoint when set, initializing
          its value to an empty collection.
        i1.createAttribute('foo', values=[], otherName='bar')

        - create a multi-valued reference from i1 to i2 attaching it to
          'foo' on i1 and a multi-valued attribute 'bar' on i2.
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

        if 'value' in kwds:
            self._setValue(name, attribute, kwds['value'], kwds)
        elif 'values' in kwds:
            self._setValues(name, attribute, kwds['values'], kwds)

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
            if (aspect != 'value' and aspect != 'values' and
                aspect != 'otherCardinality'):
                attribute.setAttributeValue(aspect, value)

        if 'cardinality' not in kwds and 'values' in kwds:
            values = kwds['values']
            if isinstance(values, list):
                attribute.setAttributeValue('cardinality', 'list')
            elif isinstance(values, dict):
                attribute.setAttributeValue('cardinality', 'dict')
            else:
                raise TypeError, 'type of initial values, %s, not supported' %(type(values))

        if 'type' not in kwds and 'value' in kwds:
            value = kwds['value']
            if not isinstance(value, Item):
                if attribute.getAspect('cardinality') == 'single':
                    typeKind = kind._kind.getItemParent().getItemChild('Type')
                    if value is not None:
                        types = typeKind.findTypes(value)
                        if types:
                            attribute.setAttributeValue('type', types[0])

        kind.addValue('attributes', attribute)
        
        return attribute

    def _verifyAttribute(self, name, attribute, kwds):

        for aspect, value in kwds.iteritems():
            if (aspect != 'value' and aspect != 'values' and 
                aspect != 'otherCardinality'):
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

    def _setValues(self, name, attribute, values, kwds):

        cardinality = attribute.getAspect('cardinality', default='single')
        
        if isinstance(values, list):
            if cardinality == 'list':
                if values == []:
                    if 'otherName' in kwds:
                        self._references[name] = self._refDict(name)
                    else:
                        self._values[name] = PersistentList(self)
                else:
                    self._setValue(name, attribute, values[0], kwds)
                    for value in values[1:]:
                        self.addValue(name, value)
            else:
                raise TypeError, "Specified a list of initial values but cardinality of attribute %s is %s" %(name, cardinality)

        elif isinstance(values, dict):
            if cardinality == 'dict':
                if 'otherName' in kwds:
                    raise ValueError, "Cardinality 'dict' not supported for references, use 'list' instead."
                self._values[name] = PersistentDict(self, **values)
            else:
                raise TypeError, "Specified a dictionary of initial values but cardinality of attribute %s is %s" %(name, cardinality)

        else:
            raise TypeError, 'type of initial values, %s, not supported' %(type(values))
