
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax
from ItemRef import ItemRef
from ItemRef import RefDict

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

        self._setRoot(parent._addItem(self))

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

        if name.endswith('__for'):
            return name[:-5]
        else:
            return name + '__for'

    def setAttribute(self, name, value=None):
        '''Create and/or set a Chandler attribute.

        This method is only required when the Chandler attribute doesn't yet
        exist or when there is an ambiguity between a python and a Chandler
        attribute, a situation best avoided.'''

        old = self._attributes.get(name)
        otherName = self._otherName(name)
        isItem = isinstance(value, Item)
            
        if isinstance(old, ItemRef):
            if isItem:
                old._reattach(self, old.other(self), value, otherName)
            else:
                old._detach(self, old.other(self), otherName)
        else:
            if isItem:
                value = ItemRef(self, value, otherName)
            
            self._attributes[name] = value

    def getAttribute(self, name):
        '''Return the named Chandler attribute value or raise KeyError when not found.

        This method is only required when there is an ambiguity between a
        python and a Chandler attribute, a situation best avoided.'''

        value = self._attributes[name]

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

    def _removeRef(self, name):

        del self._attributes[name]

    def hasAttribute(self, name):
        'Check for existence of a Chandler attribute.'

        return self._attributes.has_key(name)
    
    def delete(self):
        '''Delete this item and disconnect all its item references.

        A deleted item is no longer reachable through the repository or other
        items. It is an error to access deleted item reference.'''

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

    def getParent(self):
        '''Return this item's container parent.

        To change the parent, use Item.move().'''

        return self._parent

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
    
    def find(self, spec, _index=0):
        '''Find an item as specified or return None if not found.

        If the item is not a container and a path is specified then the search
        is performed relative to the item's parent container.'''
        
        if isinstance(spec, Path):
            if _index > 0 and _index == len(spec):
                if spec[_index - 1] == self._name:
                    return self
                else:
                    return None

        elif isinstance(spec, UUID):
            return self.getRepository().find(spec)

        return self._parent.find(spec, _index)

    def save(self, generator):
        'Generate the XML for the saving this item.'

        generator.startElement('item', { 'uuid': str(self._uuid) })

        generator.characters('\n    ')
        generator.startElement('name', {})
        generator.characters(self._name)
        generator.endElement('name')

        if self._root is not self:
            generator.characters('\n    ')
            generator.startElement('parent', { 'type': 'uuid' })
            generator.characters(str(self._parent.getUUID()))
            generator.endElement('parent')
            
        generator.characters('\n    ')
        generator.startElement('class', { 'module': self.__module__ })
        generator.characters(type(self).__name__)
        generator.endElement('class')

        for attr in self._attributes.iteritems():
            self._saveValue(attr[0], attr[1], 'attribute', '\n    ', generator)

        generator.characters('\n')
        generator.endElement('item')

    def _saveValue(self, name, value, tag, indent, generator):

        def _typeName(value):

            if isinstance(value, UUID):
                return 'uuid'
            elif isinstance(value, Path):
                return 'path'
            elif isinstance(value, RefDict):
                return 'refs'
            else:
                return type(value).__name__
            
        if isinstance(value, ItemRef):
            self._saveValue(name, value.other(self).getUUID(), 'ref', indent,
                            generator)
        else:
            attrs = {}

            if name is not None:
                attrs['name'] = str(name)
                if not isinstance(name, str) and not isinstance(name, unicode):
                    attrs['nameType'] = _typeName(value)

            if not isinstance(value, str):
                attrs['type'] = _typeName(value)

            generator.characters(indent)
            generator.startElement(tag, attrs)

            if isinstance(value, dict):
                i = indent + '    '
                for val in value.iteritems():
                    self._saveValue(val[0], val[1], 'value', i, generator)
                generator.characters(indent)
            elif isinstance(value, list):
                i = indent + '    '
                for val in value:
                    self._saveValue(None, val, 'value', i, generator)
                generator.characters(indent)
            else:
                generator.characters(str(value))

            generator.endElement(tag)


class ItemHandler(xml.sax.ContentHandler):
    'A SAX ContentHandler implementation responsible for loading items.'
    
    def __init__(self, repository, parent):

        self.repository = repository
        self.parent = parent

    def startDocument(self):

        self.tagMethods = []
        self.tagAttrs = []
        self.attributes = {}
        self.refs = []
        self.collections = []
        
    def startElement(self, tag, attrs):

        self.data = ''
        self.tagMethods.append(getattr(ItemHandler, tag + 'Tag'))
        self.tagAttrs.append(attrs)

        typeName = attrs.get('type')
        if typeName == 'dict':
            self.collections.append({})
        elif typeName == 'refs':
            self.collections.append(RefDict(None, attrs['name']))
        elif typeName == 'list':
            self.collections.append([])
                
    def characters(self, data):

        self.data += data

    def endElement(self, tag):

        self.tagMethods.pop()(self, self.tagAttrs.pop())

    def itemTag(self, attrs):

        self.item = item = self.cls(self.name, self.repository, None,
                                    _uuid = UUID(attrs.get('uuid')),
                                    _attributes = self.attributes)

        for value in item._attributes.itervalues():
            if isinstance(value, RefDict):
                value._item = item

        if hasattr(self, 'parentRef'):
            item._parentRef = self.parentRef
        elif self.parent is not None:
            item.move(self.parent)

        for ref in self.refs:
            other = item.find(ref[1])

            if len(ref) == 2:
                otherName = item._otherName(ref[0])
                valueDict = item._attributes
            else:
                otherName = item._otherName(ref[2]._name)
                item._attributes[ref[2]._name] = ref[2]
                valueDict = ref[2]
                valueDict._item = item
                
            if other is not None:
                value = other._attributes[otherName]
                if isinstance(value, ItemRef):
                    value._other = item
                elif isinstance(value, RefDict):
                    refName = item.refName(ref[0])
                    if value.has_key(refName):
                        value = value[refName]
                        value._other = item
                    else:
                        value = ItemRef(item, other, otherName)
            else:
                value = ItemRef(item, other, otherName)

            valueDict[ref[0]] = value

    def classTag(self, attrs):

        self.cls = getattr(__import__(attrs['module'], {}, {}, self.data),
                           self.data)

    def nameTag(self, attrs):

        self.name = self.data

    def parentTag(self, attrs):

        if attrs['type'] == 'uuid':
            self.parentRef = UUID(self.data)
        else:
            self.parentRef = Path(self.data)

    def attributeTag(self, attrs):

        typeName = attrs.get('type', 'str')

        if typeName == 'dict' or typeName == 'list' or typeName == 'refs':
            value = self.collections.pop()
        else:
            value = self.makeValue(typeName, self.data)
            
        self.attributes[attrs['name']] = value

    def valueTag(self, attrs):

        typeName = attrs.get('type', 'str')

        if typeName == 'dict' or typeName == 'list':
            value = self.collections.pop()
        else:
            value = self.makeValue(typeName, self.data)

        name = attrs.get('name')
        if name is None:
            self.collections[-1].append(value)
        else:
            name = self.makeValue(attrs.get('nameType', 'str'), name)
            self.collections[-1][name] = value

    def refTag(self, attrs):

        typeName = attrs.get('type', 'path')

        if typeName == 'path':
            ref = Path(self.data)
        else:
            ref = UUID(self.data)

        if self.collections:
            name = self.makeValue(attrs.get('nameType', 'str'), attrs['name'])
            self.refs.append((name, ref, self.collections[-1]))
        else:
            self.refs.append((attrs['name'], ref))

    def makeValue(self, typeName, data):

        if typeName == 'str':
            return data

        if typeName == 'uuid':
            return UUID(data)
        
        if typeName == 'path':
            return Path(data)

        if typeName == 'bool':
            return data != 'False'
        
        return getattr(__import__('__builtin__', {}, {}, typeName),
                       typeName)(data)
