
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax

from ItemRef import ItemRef
from ItemRef import RefDict
from ItemRef import RefList

from model.util.UUID import UUID
from model.util.Path import Path


class Item(object):
    'The root class for all items.'
    
    def __init__(self, name, parent, kind, **_kwds):
        '''Construct an Item.

        All items require a parent item unless they are a repository root in
        which case the parent argument should be the repository.
        Kind can be None for schema-less operation.
        Items have two sets of attributes: the regular implementation python
        attributes and the Chandler attributes. The latter are kept in a
        separate dictionary and need to be added first with Item.setAttribute()
        before they can be accessed or set with the '.' operator.
        When an item is persisted only the Chandler attributes are saved.'''
        
        super(Item, self).__init__()

        self._deleted = False
        self._attributes = _kwds.get('_attributes') or {}
        self._uuid = _kwds.get('_uuid') or UUID()
        
        self._name = name
        self._root = None
        self._parent = parent
        self._kind = kind
        
        self._setRoot(parent._addItem(self))

    def __iter__(self):

        class nullIter(object):
            def next(self): raise StopIteration
        
        if hasattr(self, '_children'):
            return self._children.itervalues()

        return nullIter()
    
    def __repr__(self):

        return ("<" + type(self).__name__ + ": " +
                self._name + " " + str(self._uuid) + ">")

    def __getattr__(self, name):

        if self._deleted:
            raise ValueError, "item is deleted " + str(self)

        return self.getAttribute(name)

    def __setattr__(self, name, value):

        if name[0] != '_' and self._attributes.has_key(name):
            self.setAttribute(name, value)
        else:
            super(Item, self).__setattr__(name, value)

    def __delattr__(self, name):

        if self._attributes.has_key(name):
            self.removeAttribute(name)
        else:
            super(Item, self).__delattr__(name)

    def _otherName(self, name):

        otherName = self.getAttrAspect(name, 'OtherName')

        if otherName is None:
            if name.endswith('__for'):
                otherName = name[:-5]
            else:
                otherName = name + '__for'

        return otherName

    def getAttrAspect(self, name, aspect, default=None):

        if self._kind is not None:
            attrDef = self._kind.getAttrDef(name)
            if attrDef is not None:
                return attrDef.getAspect(aspect, default)

        return default

    def setAttribute(self, name, value=None):
        '''Create and/or set a Chandler attribute.

        This method is only required when the Chandler attribute doesn't yet
        exist or when there is an ambiguity between a python and a Chandler
        attribute, a situation best avoided.'''

        old = self._attributes.get(name)

        if isinstance(old, ItemRef):
            if isinstance(value, Item):
                old._reattach(self, old.other(self), value,
                              self._otherName(name))
            else:
                old._detach(self, old.other(self), self._otherName(name))
        else:
            if isinstance(old, RefDict):
                old.clear()

            if isinstance(value, Item):
                otherName = self._otherName(name)
                value = ItemRef(self, value, otherName)
                card = self.getAttrAspect(name, 'Cardinality', 'single')

                if card == 'dict':
                    refs = RefDict(self, name, otherName)
                    refs[value._item.refName(name)] = value
                    value = refs
                elif card == 'list':
                    refs = RefList(self, name, otherName)
                    refs[value._item.refName(name)] = value
                    value = refs
                    
            self._attributes[name] = value

    def getAttribute(self, name):
        '''Return the named Chandler attribute value or raise KeyError when not found.

        This method is only required when there is an ambiguity between a
        python and a Chandler attribute, a situation best avoided.'''

        try:
            value = self._attributes[name]
        except KeyError:
            value = self.getAttrAspect(name, 'Default', None)
            if value is None:
                raise

        if isinstance(value, ItemRef):
            return value.other(self)
        else:
            return value

    def removeAttribute(self, name):
        'Remove a Chandler attribute.'
        
        value = self._attributes[name]
        del self._attributes[name]

        if isinstance(value, ItemRef):
            value._detach(self, value.other(self), self._otherName(name))
        elif isinstance(value, RefDict):
            value.clear()

    def getValue(self, attribute, key, default=None):
        'Get a value from a multi-valued attribute.'

        value = self._attributes.get(attribute, None)

        if value is None:
            return default

        if isinstance(value, dict):
            return value.get(key, default)

        if isinstance(value, list):
            if len(value) < key:
                return value[key]
            else:
                return default

        raise TypeError, attribute + " is not multi-valued"

    def setValue(self, attribute, value, key):
        'Set a value for a multi-valued attribute for a given key.'

        attrValue = self._attributes.get(attribute, None)

        if attrValue is None:
            card = self.getAttrAspect(attribute, 'Cardinality', 'single')
            isItem = isinstance(value, Item)

            if card == 'dict':
                if isItem:
                    attrValue = RefDict(self, attribute,
                                        self._otherName(attribute))
                else:
                    attrValue = {key: value}
                    return
            elif card == 'list':
                if isItem:
                    attrValue = RefList(self, attribute,
                                        self._otherName(attribute))
                else:
                    attrValue = [value]
                    return
            else:
                raise TypeError, attribute + " is not multi-valued"

            self._attributes[attribute] = attrValue

        attrValue[key] = value

    def addValue(self, attribute, value, key=None):
        'Add a value for a multi-valued attribute for a given optional key.'

        attrValue = self._attributes.get(attribute, None)

        if attrValue is None:
            self.setValue(attribute, key, value)
        elif isinstance(attrValue, dict):
            attrValue[key] = value
        elif isinstance(attrValue, list):
            attrValue.append(value)
        else:
            self.setAttribute(attribute, value)

    def hasKey(self, attribute, key):
        'Tell where a multi-valued attribute has a value for a given key.'

        value = self._attributes.get(attribute, None)

        if isinstance(value, dict):
            return value.has_key(key)
        elif isinstance(value, list):
            return 0 <= key and key < len(value)
        elif value is not None:
            raise TypeError, attribute + " is not multi-valued"

        return False

    def hasValue(self, attribute, value):
        'Tell where a multi-valued attribute has a given value.'

        attrValue = self._attributes.get(attribute, None)

        if isinstance(attrValue, dict):
            for v in attrValue.itervalues():
                if v == value:
                    return True
        elif isinstance(attrValue, list):
            try:
                return attrValue.index(value) >= 0
            except ValueError:
                return False
        elif value is not None:
            raise TypeError, attribute + " is not multi-valued"

        return False

    def removeValue(self, attribute, key):
        'Remove a value from multi-valued attribute for a given key.'

        value = self._attributes.get(attribute, None)

        if isinstance(value, dict):
            del value[key]
        elif isinstance(value, list):
            value.pop(key)
        elif value is not None:
            self.removeAttribute(attribute)

    def attach(self, attribute, item):
        '''Attach an item to attribute.

        The item is added to the endpoint if it is multi-valued. The item
        replaces the endpoint if it is single-valued.'''
        
        self.addValue(attribute, item, item.refName(attribute))

    def detach(self, attribute, item):
        'Detach an item from an attribute.'

        self.removeValue(attribute, item.refName(attribute))

    def _removeRef(self, name):

        del self._attributes[name]

    def hasAttribute(self, name):
        'Check for existence of a Chandler attribute.'

        return self._attributes.has_key(name)
    
    def delete(self):
        '''Delete this item and disconnect all its item references.

        If this item has children, they are recursively deleted first.
        A deleted item is no longer reachable through the repository or other
        items. It is an error to access deleted item reference.'''

        if hasattr(self, '_children'):
            for item in self._children.values():
                item.delete()

        for attr in self._attributes.keys():
            self.__delattr__(attr)

        self._parent._removeItem(self)
        self._setRoot(None)

        self._deleted = True
        
    def getName(self):
        '''Return this item's name.

        The item name is used to lookup an item in its parent container and
        construct the item's path in the repository.
        To rename an item use Item.rename().'''

        return self._name

    def refName(self, name):
        '''Return the reference name for this item.

        The reference name is used as a key into multi-valued attribute
        dictionaries storing ItemRefs to this and other items.'''
        
        return self._uuid

    def getUUID(self):
        'Return the Universally Unique ID for this item.'
        
        return self._uuid

    def getPath(self, path=None):
        'Return the path to this item relative to its repository.'

        if path is None:
            path = Path()
            
        self._parent.getPath(path)
        path.append(self._name)

        return path

    def getRoot(self):
        '''Return this item's repository root.

        All single-slash rooted paths are expressed relative to this root.'''
        
        return self._root

    def _setRoot(self, root):

        oldRepository = self.getRepository()
        self._root = root
        newRepository = self.getRepository()

        if oldRepository is not newRepository:
            if oldRepository is not None:
                oldRepository._unregisterItem(self)
            if newRepository is not None:
                newRepository._registerItem(self)

        for child in self:
            child._setRoot(root)

    def getParent(self):
        '''Return this item's container parent.

        To change the parent, use Item.move().'''

        return self._parent

    def getKind(self):
        '''Return this item's kind.'''

        return getattr(self, '_kind', None)

    def getRepository(self):
        '''Return this item's repository.

        The item's repository is defined as the item root's parent.'''

        if self._root is None:
            return None
        else:
            return self._root._parent

    def rename(self, name):
        'Rename this item.'
        
        self._parent._removeItem(self)
        self._name = name
        self._parent._addItem(self)

    def move(self, parent):
        'Move this item under another container or make it a root.'

        if self._parent is not parent:
            self._parent._removeItem(self)
            self._setRoot(parent._addItem(self))
            self._parent = parent
    
    def _addItem(self, item):

        name = item._name
        
        if hasattr(self, '_children'):

            current = self._children.get(name)
            if current is not None:
                current.delete()

            self._children[name] = item

        else:
            self._children = { name: item }
            
        return self._root

    def _removeItem(self, item):

        del self._children[item.getName()]

    def getChild(self, name):
        'Return the child as named or None if not found.'

        if hasattr(self, '_children'):
            return self._children.get(name)

        return None

    def find(self, spec, _index=0):
        '''Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the item unless the path is absolute.'''

        if isinstance(spec, Path):
            l = len(spec)

            if _index == l:
                if spec[_index - 1] == self._name:
                    return self
                else:
                    return None

            if _index > l:
                return None

            if _index == 0:
                if spec[0] == '//':
                    return self.getRepository().find(spec)

                elif spec[0] == '/':
                    if self._root is self:
                        return self.find(spec, _index=1)
                    else:
                        return self._root.find(spec, _index=0)

            child = self.getChild(spec[_index])
            if child is not None:
                return child.find(spec, _index + 1)

        elif isinstance(spec, UUID):
            return self.getRepository().find(spec)

        elif isinstance(spec, str):
            if len(spec) == 36 and spec[8] == '-' or len(spec) == 22:
                return self.find(UUID(spec))

            return self.find(Path(spec))

        return None

    def save(self, repository, **args):

        repository.saveItem(self, **args)

        for child in self:
            child.save(repository, **args)

    def toXML(self, generator, withSchema=False):
        'Generate the XML representation for this item.'

        kind = self._kind
        generator.startElement('item', { 'uuid': str(self._uuid) })

        self._xmlTag('name', {}, self._name, generator)

        if kind is not None:
            self._xmlTag('kind', { 'type': 'uuid' },
                         str(kind.getUUID()), generator)

        if withSchema or kind is None or kind.Class is not type(self):
            self._xmlTag('class', { 'module': self.__module__ },
                         type(self).__name__, generator)

        if self._root is not self:
            self._xmlTag('parent', { 'type': 'uuid' },
                         str(self._parent.getUUID()), generator)

        for attr in self._attributes.iteritems():
            if self.getAttrAspect(attr[0], 'Persist', True):
                attrType = self.getAttrAspect(attr[0], 'Type')
                attrCard = self.getAttrAspect(attr[0], 'Cardinality', 'single')
                self._xmlValue(attr[0], attr[1], 'attribute',
                               attrType, attrCard, '\n    ',
                               generator, withSchema)

        generator.characters('\n')
        generator.endElement('item')

    def _xmlTag(self, tag, attrs, value, generator):

        generator.characters('\n    ')
        generator.startElement(tag, attrs)
        generator.characters(value)
        generator.endElement(tag)

    def _xmlValue(self, name, value, tag, attrType, attrCard,
                  indent, generator, withSchema):

        def typeName(value):

            typeHandler = ItemHandler.typeHandlers.get(type(value))

            if typeHandler is not None:
                return typeHandler.handlerName()
            elif isinstance(value, UUID):
                return 'uuid'
            elif isinstance(value, Path):
                return 'path'
            else:
                return type(value).__name__
            
        if isinstance(value, ItemRef):
            self._xmlValue(name, value.other(self).getUUID(), 'ref',
                           attrType, 'single', indent, generator, withSchema)
        else:
            attrs = {}
            
            if name is not None:
                attrs['name'] = str(name)
                if not isinstance(name, str) and not isinstance(name, unicode):
                    attrs['nameType'] = typeName(value)

            if tag != 'value':
                if attrCard != 'single':
                    attrs['cardinality'] = attrCard
                if withSchema and tag == 'ref':
                    attrs['otherName'] = self._otherName(name)

            if isinstance(value, RefDict):
                tag = 'ref'
                if withSchema:
                    attrs['otherName'] = self._otherName(name)
                    withSchema = False
            elif not isinstance(value, str):
                if (tag == 'value' or
                    ((tag == 'attribute' or
                      tag == 'ref') and attrCard == 'single')):
                    if attrType is None:
                        attrs['type'] = typeName(value)
                    elif withSchema:
                        attrs['type'] = attrType.handlerName()

            generator.characters(indent)
            generator.startElement(tag, attrs)

            if isinstance(value, dict):
                i = indent + '    '
                for val in value.iteritems():
                    self._xmlValue(val[0], val[1], 'value', attrType, 'single',
                                   i, generator, withSchema)
                generator.characters(indent)
            elif isinstance(value, list):
                i = indent + '    '
                for val in value:
                    self._xmlValue(None, val, 'value', attrType, 'single',
                                   i, generator, withSchema)
                generator.characters(indent)
            else:
                if attrType is None:
                    typeHandler = ItemHandler.typeHandlers.get(type(value))

                    if typeHandler is not None:
                        value = typeHandler.makeString(value)
                    else:
                        value = str(value)
                else:
                    value = attrType.serialize(value, withSchema)
                generator.characters(value)

            generator.endElement(tag)


class ItemHandler(xml.sax.ContentHandler):
    'A SAX ContentHandler implementation responsible for loading items.'
    
    typeHandlers = {}
    
    def __init__(self, repository, parent):

        self.repository = repository
        self.parent = parent

    def startDocument(self):

        self.tagMethods = []
        self.tagAttrs = []
        self.tags = []
        self.attributes = {}
        self.refs = []
        self.collections = []
        self.attrDefs = []
        self.kind = None
        self.cls = None
        
    def startElement(self, tag, attrs):

        self.data = ''
        self.tagMethods.append(getattr(ItemHandler, tag + 'End'))
        self.tagAttrs.append(attrs)

        method = getattr(ItemHandler, tag + 'Start', None)
        if method is not None:
            method(self, attrs)

        self.tags.append(tag)

    def endElement(self, tag):

        self.tags.pop()
        self.tagMethods.pop()(self, self.tagAttrs.pop())

    def characters(self, data):

        self.data += data

    def attributeStart(self, attrs):

        attrDef = self.getAttrDef(attrs['name'])
        self.attrDefs.append(attrDef)

        cardinality = self.getCardinality(attrDef, attrs)
        typeName = attrs.get('type')
        
        if cardinality == 'dict' or typeName == 'dict':
            self.collections.append({})
        elif cardinality == 'list' or typeName == 'list':
            self.collections.append([])

    def refStart(self, attrs):

        if self.tags[-1] == 'item':
            name = attrs['name']
            attrDef = self.getAttrDef(attrs['name'])
            self.attrDefs.append(attrDef)

            cardinality = self.getCardinality(attrDef, attrs)

            if cardinality != 'single':
                otherName = self.getOtherName(name, attrDef, attrs)
                
                if cardinality == 'dict':
                    self.collections.append(RefDict(None, name, otherName))
                elif cardinality == 'list':
                    self.collections.append(RefList(None, name, otherName))
                
    def itemEnd(self, attrs):

        cls = self.cls or (self.kind and self.kind.Class) or Item
        self.item = item = cls(self.name, self.repository, self.kind,
                               _uuid = UUID(attrs.get('uuid')),
                               _attributes = self.attributes)

        for value in item._attributes.itervalues():
            if isinstance(value, RefDict):
                value._item = item

        if hasattr(self, 'parentRef'):
            item._parentRef = self.parentRef
        elif self.parent is not None:
            item.move(self.parent)

        if hasattr(self, 'kindRef'):
            item._kindRef = self.kindRef
            self.repository.kindRefs.append(item)

        for ref in self.refs:
            other = item.find(ref[1])
            
            if len(ref) == 2:
                name = ref[0][0]
                otherName = ref[0][1]
                valueDict = item._attributes
            else:
                name = ref[0]
                if name is None:
                    if other is None:
                        raise ValueError, "refName to " + ref[1] + " is None, it should be loaded before " + item.getPath()
                    else:
                        name = other.refName(ref[2]._name)
                otherName = ref[2]._otherName
                valueDict = ref[2]
                valueDict._item = item
                
            if other is not None:
                value = other._attributes.get(otherName)
                if value is None:
                    value = ItemRef(item, other, otherName)
                elif isinstance(value, ItemRef):
                    value._other = item
                elif isinstance(value, RefDict):
                    refName = item.refName(otherName)
                    if value.has_key(refName):
                        value = value._getRef(refName)
                        value._other = item
                    else:
                        value = ItemRef(item, other, otherName)
            else:
                value = ItemRef(item, other, otherName)
                self.repository.itemRefs.append((item, ref[1],
                                                 otherName, value))

            valueDict[name] = value

    def kindEnd(self, attrs):

        if attrs['type'] == 'uuid':
            kindRef = UUID(self.data)
        else:
            kindRef = Path(self.data)

        self.kind = self.repository.find(kindRef)
        if self.kind is None:
            self.kindRef = kindRef

    def classEnd(self, attrs):

        self.cls = getattr(__import__(attrs['module'], {}, {}, self.data),
                           self.data)
        if self.kind is None:
            self.kind = getattr(self.cls, 'kind', None)

    def nameEnd(self, attrs):

        self.name = self.data

    def parentEnd(self, attrs):

        if attrs['type'] == 'uuid':
            self.parentRef = UUID(self.data)
        else:
            self.parentRef = Path(self.data)

    def attributeEnd(self, attrs):

        attrDef = self.attrDefs.pop()
        cardinality = self.getCardinality(attrDef, attrs)

        if cardinality == 'single':
            value = self.makeValue(attrDef, attrs.get('type', 'str'),
                                   self.data)
        else:
            value = self.collections.pop()
            
        self.attributes[attrs['name']] = value

    def refEnd(self, attrs):

        if self.tags[-1] == 'item':
            attrDef = self.attrDefs.pop()
            cardinality = self.getCardinality(attrDef, attrs)
        else:
            cardinality = 'single'

        if cardinality == 'single':
            typeName = attrs.get('type', 'path')

            if typeName == 'path':
                ref = Path(self.data)
            else:
                ref = UUID(self.data)

            if self.collections:
                if attrs.has_key('name'):
                    name = self.makeValue(None, attrs.get('nameType', 'str'),
                                          attrs['name'])
                else:
                    name = None
                self.refs.append((name, ref, self.collections[-1]))
            else:
                name = attrs['name']
                otherName = self.getOtherName(name, self.getAttrDef(name),
                                              attrs)
                self.refs.append(((name, otherName), ref))
        else:
            value = self.collections.pop()
            self.attributes[attrs['name']] = value

    def valueEnd(self, attrs):

        typeName = attrs.get('type', 'str')

        if typeName == 'dict' or typeName == 'list':
            value = self.collections.pop()
        else:
            value = self.makeValue(self.attrDefs[-1], typeName, self.data)

        name = attrs.get('name')
        if name is None:
            self.collections[-1].append(value)
        else:
            name = self.makeValue(None, attrs.get('nameType', 'str'), name)
            self.collections[-1][name] = value

    def getCardinality(self, attrDef, attrs):

        cardinality = attrs.get('cardinality')

        if cardinality is None:
            if attrDef is None:
                cardinality = 'single'
            else:
                cardinality = attrDef.getAspect('Cardinality', 'single')

        return cardinality

    def getOtherName(self, name, attrDef, attrs):

        otherName = attrs.get('otherName')

        if otherName is None and attrDef is not None:
            otherName = attrDef.getAspect('OtherName')

        if otherName is None:
            if name.endswith('__for'):
                otherName = name[:-5]
            else:
                otherName = name + '__for'

        return otherName

    def getAttrDef(self, name):
        
        if self.kind is not None:
            return self.kind.getAttrDef(name)
        else:
            return None

    def makeValue(self, attrDef, typeName, data):

        if attrDef is not None:
            type = attrDef.getAspect('Type')
            if type is not None:
                return type.unserialize(data)

        if typeName.find('.') > 0:
            try:
                typeHandler = ItemHandler.typeHandlers[typeName]
            except KeyError:
                lastDot = typeName.rindex('.')
                module = typeName[:lastDot]
                name = typeName[lastDot+1:]
        
                typeHandler = getattr(__import__(module, {}, {}, name), name)
                ItemHandler.typeHandlers[typeName] = typeHandler

            return typeHandler.makeValue(data)

        if typeName == 'str' or typeName == 'unicode':
            return data

        if typeName == 'uuid':
            return UUID(data)
        
        if typeName == 'path':
            return Path(data)

        if typeName == 'bool':
            return data != False

        if typeName == 'int':
            return int(data)

        if typeName == 'long':
            return long(data)

        if typeName == 'float':
            return float(data)

        if typeName == 'complex':
            return complex(data)

        raise ValueError, "Unknown type: " + typeName
