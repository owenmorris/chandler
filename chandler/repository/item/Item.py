
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax

from ItemRef import ItemRef, RefArgs
from ItemRef import Values, References, RefDict

from model.util.UUID import UUID
from model.util.Path import Path


class Item(object):
    'The root class for all items.'
    
    def __init__(self, name, parent, kind, **_kwds):
        '''Construct an Item.

        All items require a parent item unless they are a repository root in
        which case the parent argument is the repository.
        Kind can be None for schema-less operation.
        Items have two sets of attributes: the regular implementation python
        attributes and the Chandler attributes. The latter are kept in a
        separate dictionary and need to be added first with
        Item.setAttributeValue() before they can be accessed or set with the
        '.' operator.
        When an item is persisted only the Chandler attributes are saved.'''
        
        super(Item, self).__init__()

        self._status = 0
        self._uuid = _kwds.get('_uuid') or UUID()

        values = _kwds.get('_values')
        if values is not None:
            values._setItem(self)
            self._values = values
        else:
            self._values = Values(self)

        references = _kwds.get('_references')
        if references is not None:
            references._setItem(self)
            self._references = references
        else:
            self._references = References(self)
        
        self._name = name or self._uuid.str64()
        self._root = None

        if parent is not None:
            self._parent = parent
            self._setRoot(parent._addItem(self))
        else:
            self._parent = None

        self._kind = None
        self._setKind(kind)

    def __iter__(self):

        class nullIter(object):
            def next(self): raise StopIteration
        
        if self.__dict__.has_key('_children'):
            return self._children.itervalues()

        return nullIter()
    
    def __repr__(self):

        return "<%s: %s %s>" %(type(self).__name__, self._name,
                               self._uuid.str16())

    def __getattr__(self, name):

        if self._status & Item.DELETED:
            raise ValueError, "item is deleted: %s" %(str(self))

        return self.getAttributeValue(name)

    def __setattr__(self, name, value):

        if name[0] != '_':
            if self._values.has_key(name):
                return self.setAttributeValue(name, value,
                                              _attrDict=self._values)
            elif self._references.has_key(name):
                return self.setAttributeValue(name, value,
                                              _attrDict=self._references)
            elif self._kind is not None and self._kind.hasAttribute(name):
                return self.setAttributeValue(name, value)

        return super(Item, self).__setattr__(name, value)

    def __delattr__(self, name):

        if self._values.has_key(name):
            self.removeAttributeValue(name, _attrDict=self._values)
        elif self._references.has_key(name):
            self.removeAttributeValue(name, _attrDict=self._references)
        else:
            super(Item, self).__delattr__(name)

    def _otherName(self, name):

        otherName = self.getAttributeAspect(name, 'OtherName')
        if otherName is None:
            raise TypeError, 'Undefined other endpoint for %s.%s' %(self.getItemPath(), name)

        return otherName

    def hasAttributeAspect(self, name, aspect):

        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                return attribute.hasAspect(aspect)

        return False

    def getAttributeAspect(self, name, aspect, default=None):

        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                return attribute.getAspect(aspect, default)

        return default

    def setAttributeValue(self, name, value=None, _attrDict=None):
        """Create and/or set a Chandler attribute.

        This method is only required when the Chandler attribute doesn't yet
        exist or when there is an ambiguity between a python and a Chandler
        attribute, a situation best avoided."""

        self.setDirty()

        isItem = isinstance(value, Item)
        isRef = not isItem and (isinstance(value, ItemRef) or
                                isinstance(value, RefDict))

        if _attrDict is None:
            if self._values.has_key(name):
                _attrDict = self._values
            elif self._references.has_key(name):
                _attrDict = self._references

        if _attrDict is self._references:
            if not (isItem or isRef):
                del _attrDict[name]
            else:
                old = _attrDict.get(name)

                if isinstance(old, ItemRef):
                    old.reattach(self, name,
                                 old.other(self), value, self._otherName(name))
                    return value
                elif isinstance(old, RefDict):
                    old.clear()
                elif old is not None:
                    raise ValueError, old

        elif (isItem or isRef) and _attrDict is self._values:
            del _attrDict[name]

        if isItem:
            otherName = self._otherName(name)
            card = self.getAttributeAspect(name, 'Cardinality', 'single')

            if card == 'dict' or card == 'list':
                refs = self._refDict(name, otherName, card == 'list')
                value = ItemRef(self, name, value, otherName)
                refs[value._getItem().refName(name)] = value
                value = refs
            else:
                value = ItemRef(self, name, value, otherName)

            self._references[name] = value

        elif isRef:
            self._references[name] = value

        else:
            self._values[name] = value

        return value

    def getAttributeValue(self, name, _attrDict=None, **kwds):
        """Return the named Chandler attribute value.

        If the attribute is not set then attempt to inherit a value if the
        attribute's InheritFrom aspect is set, attempt to return the value
        of the optional 'default' keyword passed to this method, attempt to
        return the value of its DefaultValue aspect if set, or finally raise 
        AttributeError. 
        Calling this method is only required when there is a name ambiguity
        between a python and a Chandler attribute, a situation best avoided."""

        try:
            if (_attrDict is self._values or
                _attrDict is None and self._values.has_key(name)):
                return self._values[name]

            elif (_attrDict is self._references or
                  _attrDict is None and self._references.has_key(name)):
                value = self._references[name]
                if isinstance(value, ItemRef):
                    return value.other(self)
                return value

        except KeyError:
            pass

        inherit = self.getAttributeAspect(name, 'InheritFrom', None)
        if inherit is not None:
            value = self
            for attr in inherit.split('.'):
                value = value.getAttributeValue(attr)

            return value

        elif kwds.has_key('default'):
            return kwds['default']

        elif self.hasAttributeAspect(name, 'DefaultValue'):
            return self.getAttributeAspect(name, 'DefaultValue')

        raise AttributeError, name

    def removeAttributeValue(self, name, _attrDict=None):
        "Remove a Chandler attribute's value."

        self.setDirty()

        if _attrDict is None:
            if self._values.has_key(name):
                _attrDict = self._values
            elif self._references.has_key(name):
                _attrDict = self._references

        if _attrDict is self._values:
            del _attrDict[name]
        elif _attrDict is self._references:
            value = _attrDict[name]
            del _attrDict[name]

            if isinstance(value, ItemRef):
                value.detach(self, name,
                             value.other(self), self._otherName(name))
            elif isinstance(value, RefDict):
                value.clear()
            else:
                raise ValueError, value

    def attributes(self, valuesOnly=False, referencesOnly=False):
        '''Get a generator of (name, value) tuples for attributes of this item.

        By setting valuesOnly to True, no item references are returned.
        By setting referencesOnly to True, only references are returned.'''

        if not referencesOnly:
            for attr in self._values.iteritems():
                yield attr

        if not valuesOnly:
            for ref in self._references.iteritems():
                if isinstance(ref[1], ItemRef):
                    yield (ref[0], ref[1].other(self))
                else:
                    yield ref

    def check(self):

        for ref in self.attributes(referencesOnly=True):
            if isinstance(ref[1], RefDict):
                refDict = ref[1]
                if refDict._ordered:
                    l = len(refDict)
                    for other in refDict:
                        l -= 1
                        if l < 0:
                            break;
                    if l != 0:
                        raise ValueError, "Iterator on %s.%s doesn't match length (%d left for %d total)" %(self.getItemPath(), ref[0], l, len(refDict))
                else:
                    for other in refDict:
                        pass
        
    def getValue(self, attribute, key, default=None, _attrDict=None):
        'Get a value from a multi-valued attribute.'

        if _attrDict is None:
            value = (self._values.get(attribute, None) or
                     self._references.get(attribute, None))
        else:
            value = _attrDict.get(attribute, None)
            
        if value is None:
            return default

        if isinstance(value, dict):
            return value.get(key, default)

        if isinstance(value, list):
            if len(value) < key:
                return value[key]
            else:
                return default

        raise TypeError, "%s is not multi-valued" %(attribute)

    def setValue(self, attribute, value, key=None, _attrDict=None):
        """Set a value for a multi-valued attribute, for an optional key.

        When the cardinality of the attribute is 'list' and its type is a
        literals, key must be an integer.
        When the cardinality of the attribute is 'list' and its values are
        references, key may be an integer or the refName of the item value
        to set."""

        self.setDirty()

        if _attrDict is None:
            if isinstance(value, Item):
                _attrDict = self._references
            else:
                _attrDict = self._values

        attrValue = _attrDict.get(attribute, None)
            
        if attrValue is None:
            card = self.getAttributeAspect(attribute, 'Cardinality', 'single')
            isItem = isinstance(value, Item)

            if card == 'dict':
                if isItem:
                    attrValue = self._refDict(attribute,
                                              self._otherName(attribute))
                else:
                    _attrDict[attribute] = { key: value }
                    return

            elif card == 'list':
                if isItem:
                    attrValue = self._refDict(attribute,
                                              self._otherName(attribute), True)
                else:
                    _attrDict[attribute] = [ value ]
                    return
            else:
                raise TypeError, "%s is not multi-valued" %(attribute)

            _attrDict[attribute] = attrValue

        attrValue[key] = value

    def addValue(self, attribute, value, key=None, _attrDict=None):
        "Add a value for a multi-valued attribute for a given optional key."

        if _attrDict is None:
            if isinstance(value, Item):
                _attrDict = self._references
            else:
                _attrDict = self._values
                
        attrValue = _attrDict.get(attribute, None)

        if attrValue is None:
            self.setValue(attribute, value, key, _attrDict=_attrDict)

        else:
            self.setDirty()

            if isinstance(attrValue, dict):
                attrValue[key] = value
            elif isinstance(attrValue, list):
                attrValue.append(value)
            else:
                raise TypeError, "%s is not multi-valued" %(attribute)

    def hasKey(self, attribute, key):
        """Tell where a multi-valued attribute has a value for a given key.

        When the cardinality of the attribute is 'list' and its type is a
        literal, key must be an integer.
        When the cardinality of the attribute is 'list' and its values are
        references, key must be an integer or the refName of the item value
        to remove."""

        value = (self._values.get(attribute, None) or
                 self._references.get(attribute, None))

        if isinstance(value, dict):
            return value.has_key(key)
        elif isinstance(value, list):
            return 0 <= key and key < len(value)
        elif value is not None:
            raise TypeError, "%s is not multi-valued" %(attribute)

        return False

    def hasValue(self, attribute, value, _attrDict=None):
        'Tell whether a multi-valued attribute has a given value.'

        if _attrDict is not None:
            attrValue = _attrDict.get(attribute, None)
        else:
            attrValue = (self._values.get(attribute, None) or
                         self._references.get(attribute, None))

        if isinstance(attrValue, RefDict) or isinstance(attrValue, list):
            return value in attrValue

        elif isinstance(attrValue, dict):
            for v in attrValue.itervalues():
                if v == value:
                    return True

        elif attrValue is not None:
            raise TypeError, "%s is not multi-valued" %(attribute)

        return False

    def removeValue(self, attribute, key, _attrDict=None):
        """Remove the value from a multi-valued attribute for a given key.

        When the cardinality of the attribute is 'list' and its type is a
        literal, key must be an integer.
        When the cardinality of the attribute is 'list' or 'dict' and its
        values are references, the detach() method should be called instead."""

        self.setDirty()

        if _attrDict is not None:
            value = _attrDict.get(attribute, None)
        else:
            value = (self._values.get(attribute, None) or
                     self._references.get(attribute, None))

        card = self.getAttributeAspect(attribute, 'Cardinality', 'single')
        
        if card == 'dict' or card == 'list':
            del value[key]
        else:
            raise TypeError, "%s is not multi-valued" %(attribute)

    def attach(self, attribute, item):
        """Attach an item to attribute.

        The item is added to the endpoint if it is multi-valued. The item
        replaces the endpoint if it is single-valued."""

        self.addValue(attribute, item, item.refName(attribute),
                      _attrDict = self._references)

    def detach(self, attribute, item):
        'Detach an item from an attribute.'

        self.removeValue(attribute, item.refName(attribute),
                         _attrDict = self._references)

    def _removeRef(self, name):

        del self._references[name]

    def hasAttributeValue(self, name, _attrDict=None):
        'Check for existence of a Chandler attribute.'

        if _attrDict is None:
            return (self._values.has_key(name) or
                    self._references.has_key(name))
        else:
            return _attrDict.has_key(name)

    def isDeleted(self):

        return (self._status & Item.DELETED) != 0
    
    def isDirty(self):

        return (self._status & Item.DIRTY) != 0

    def setDirty(self, dirty=True):

        if dirty:
            if self._status & Item.DIRTY == 0:
                repository = self.getRepository()
                if repository is not None and repository.addTransaction(self):
                    self._status |= Item.DIRTY
        else:
            self._status &= ~Item.DIRTY

    def delete(self):
        """Delete this item and disconnect all its item references.

        If this item has children, they are recursively deleted first.
        If this item has references to other items and the references delete
        policy is 'cascade' then these other items are deleted last.
        A deleted item is no longer reachable through the repository or other
        items. It is an error to access deleted item reference."""

        if (not (self._status & Item.DELETED) and
            not (self._status & Item.DELETING)):

            self.setDirty()
            self._status |= Item.DELETING
            others = []
            
            if self.__dict__.has_key('_children'):
                for item in self._children.values():
                    item.delete()

            self._values.clear()

            for name in self._references.keys():
                policy = self.getAttributeAspect(name, 'DeletePolicy', 'remove')
                if policy == 'cascade':
                    value = self._references[name]
                    if value is not None:
                        if isinstance(value, ItemRef):
                            others.append(value.other(self))
                        elif isinstance(value, RefDict):
                            others.extend(value.others())
                    
                self.removeAttributeValue(name, _attrDict=self._references)

            self._parent._removeItem(self)
            self._setRoot(None)

            self._status |= Item.DELETED
            self._status &= ~Item.DELETING

            for other in others:
                if other.refCount() == 0:
                    other.delete()
        
    def getItemName(self):
        '''Return this item's name.

        The item name is used to lookup an item in its parent container and
        construct the item's path in the repository.
        To rename an item use Item.rename().'''

        return self._name

    def refName(self, name):
        '''Return the reference name for this item.

        The reference name is used as a key into multi-valued attribute
        dictionaries storing ItemRefs to this and other items.
        By default, this name is the UUID of the item.'''
        
        return self._uuid

    def refCount(self):
        'Return the total ref count for counted references on this item.'

        count = 0

        if not (self._status & Item.DELETED):
            for name in self._references.iterkeys():
                policy = self.getAttributeAspect(name, 'CountPolicy', 'none')
                if policy == 'count':
                    count += self._references[name]._refCount()

        return count

    def getUUID(self):
        'Return the Universally Unique ID for this item.'
        
        return self._uuid

    def getItemPath(self, path=None):
        'Return the path to this item relative to its repository.'

        if path is None:
            path = Path()
            
        self._parent.getItemPath(path)
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

            if oldRepository is not None and newRepository is not None:
                raise NotImplementedError, 'changing repositories'

            if oldRepository is not None:
                oldRepository._unregisterItem(self)

            if newRepository is not None:
                newRepository._registerItem(self)

                self.setDirty()

        for child in self:
            child._setRoot(root)

    def getItemParent(self):
        """Return this item's container parent.

        To change the parent, use Item.move()."""

        return self._parent

    def _setKind(self, kind):

        if self._kind is not None:
            self._kind.detach('Items', self)

        self._kind = kind

        if self._kind is not None:
            ref = ItemRef(self, 'Kind', self._kind, 'Items', 'dict')
            self._references['Kind'] = ref

    def getRepository(self):
        """Return this item's repository.

        The item's repository is defined as the item root's parent."""

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
        
        if self.__dict__.has_key('_children'):

            current = self._children.get(name)
            if current is not None:
                current.delete()

            self._children[name] = item

        else:
            self._children = { name: item }
            
        return self._root

    def _removeItem(self, item):

        del self._children[item.getItemName()]

    def getItemChild(self, name, load=True):
        'Return the child as named or None if not found.'

        if self.__dict__.has_key('_children'):
            return self._children.get(name)

        return None

    def isRemote(self):
        'By default, an item is not remote.'

        return False

    # kludge for now until we settle on a casing convention
    def IsRemote(self):
        return self.isRemote()

    def find(self, spec, _index=0, load=True):
        """Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the item unless the path is absolute."""

        if isinstance(spec, Path):
            l = len(spec)

            if l == 0 or _index >= l:
                return None

            if _index == 0:
                if spec[0] == '//':
                    return self.getRepository().find(spec, 1, load)

                elif spec[0] == '/':
                    if self._root is self:
                        return self.find(spec, 1, load)
                    else:
                        return self._root.find(spec, 1, load)

            if spec[_index] == '.':
                if _index == l - 1:
                    return self
                return self.find(spec, _index + 1, load)

            if spec[_index] == '..':
                if _index == l - 1:
                    return self._parent
                return self._parent.find(spec, _index + 1, load)

            child = self.getItemChild(spec[_index], load)
            if child is not None:
                if _index == l - 1:
                    return child
                return child.find(spec, _index + 1, load)

        elif isinstance(spec, UUID):
            return self.getRepository().find(spec, 0, load)

        elif isinstance(spec, str) or isinstance(spec, unicode):
            if (spec[0] != '/' and
                (len(spec) == 36 and spec[8] == '-' or len(spec) == 22)):
                return self.find(UUID(spec), 0, load)

            return self.find(Path(spec), 0, load)

        return None

    def _saveItem(self, generator, withSchema=False):

        def xmlTag(tag, attrs, value, generator):

            generator.startElement(tag, attrs)
            generator.characters(value)
            generator.endElement(tag)

        kind = self._kind
        attrs = { 'uuid': self._uuid.str64() }
        if withSchema:
            attrs['withSchema'] = 'True'
        generator.startElement('item', attrs)

        xmlTag('name', {}, self._name, generator)

        if kind is not None:
            xmlTag('kind', { 'type': 'uuid' },
                   kind.getUUID().str64(), generator)

        if (withSchema or kind is None or
            kind.getItemClass() is not type(self)):
            xmlTag('class', { 'module': self.__module__ },
                   type(self).__name__, generator)

        if self._root is not self:
            xmlTag('parent', { 'type': 'uuid' },
                   self._parent.getUUID().str64(), generator)

        self._saveAttrs(generator, withSchema)
        self._saveRefs(generator, withSchema)

        generator.endElement('item')

    def _loadItem(self):

        return self

    def _saveAttrs(self, generator, withSchema):

        for attr in self._values.iteritems():
            if self.getAttributeAspect(attr[0], 'Persist', True):
                attrType = self.getAttributeAspect(attr[0], 'Type')
                attrCard = self.getAttributeAspect(attr[0], 'Cardinality',
                                                   'single')
                ItemHandler.xmlValue(attr[0], attr[1], 'attribute',
                                     attrType, attrCard, generator,
                                     withSchema)

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.iteritems():
            if self.getAttributeAspect(attr[0], 'Persist', True):
                attr[1]._saveValue(attr[0], self, generator, withSchema)

    def _refDict(self, name, otherName, ordered=False):

        return self.getRepository().createRefDict(self, name,
                                                  otherName, ordered)
        

    def loadClass(cls, name, module=None):

        if module is None:
            lastDot = name.rindex('.')
            module = name[:lastDot]
            name = name[lastDot+1:]

        m = __import__(module, {}, {}, name)

        try:
            cls = getattr(m, name)
            cls.__module__

            return cls

        except AttributeError:
            raise ImportError, "Module %s has no class %s" %(module, name)

    loadClass = classmethod(loadClass)
    
    DELETED  = 0x1
    DIRTY    = 0x2
    DELETING = 0x4
    

class ItemHandler(xml.sax.ContentHandler):
    'A SAX ContentHandler implementation responsible for loading items.'
    
    typeHandlers = {}
    
    def __init__(self, repository, parent, afterLoadHooks):

        self.repository = repository
        self.parent = parent
        self.afterLoadHooks = afterLoadHooks
        self.item = None
        
    def startDocument(self):

        self.tagAttrs = []
        self.tags = []
        self.delegates = []
        self.fields = None

        assert not self.item
        
    def startElement(self, tag, attrs):

        self.data = ''
        self.tagAttrs.append(attrs)

        if self.delegates:
            delegate = self.delegates[-1]
            delegateClass = type(delegate)
            self.delegates.append(delegate)
        else:
            delegate = self
            delegateClass = ItemHandler
            
        method = getattr(delegateClass, tag + 'Start', None)
        if method is not None:
            method(delegate, self, attrs)

        self.tags.append(tag)

    def endElement(self, tag):
 
        withValue = False

        if self.delegates:
            delegate = self.delegates.pop()
            if not self.delegates:
                value = delegate.getValue(self, self.data)
                withValue = True

        if self.delegates:
            delegate = self.delegates[-1]
            delegateClass = type(delegate)
        else:
            delegate = self
            delegateClass = ItemHandler
            
        attrs = self.tagAttrs.pop()
        method = getattr(delegateClass, self.tags.pop() + 'End', None)
        if method is not None:
            if withValue:
                method(delegate, self, attrs, value=value)
            else:
                method(delegate, self, attrs)

    def characters(self, data):

        self.data += data

    def attributeStart(self, itemHandler, attrs):

        attribute = self.getAttribute(attrs['name'])
        self.attributes.append(attribute)

        cardinality = self.getCardinality(attribute, attrs)
        typeName = self.getTypeName(attribute, attrs)
        
        if cardinality == 'dict' or typeName == 'dict':
            self.collections.append({})
        elif cardinality == 'list' or typeName == 'list':
            self.collections.append([])
        else:
            self.setupTypeDelegate(attrs)

    def refStart(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            name = attrs['name']
            attribute = self.getAttribute(name)
            self.attributes.append(attribute)

            cardinality = self.getCardinality(attribute, attrs)

            if cardinality != 'single':
                otherName = self.getOtherName(name, attribute, attrs)
                ordered = cardinality == 'list'
                refDict = self.repository.createRefDict(None, name, otherName,
                                                        ordered)
                self.collections.append(refDict)

    def itemStart(self, itemHandler, attrs):

        self.values = Values(None)
        self.references = References(None)
        self.refs = []
        self.collections = []
        self.attributes = []
        self.name = None
        self.kind = None
        self.cls = None
        self.kindRef = None
        self.parentRef = None
        self.withSchema = attrs.get('withSchema', 'False') == 'True'
                
    def itemEnd(self, itemHandler, attrs):

        cls = self.cls
        if cls is None:
            if self.kind is None:
                cls = Item
            else:
                cls = self.kind.getItemClass()

        self.item = item = cls(self.name, self.parent, self.kind,
                               _uuid = UUID(attrs.get('uuid')),
                               _values = self.values,
                               _references = self.references,
                               _afterLoadHooks = self.afterLoadHooks)

        self.repository._registerItem(item)

        for refArgs in self.refs:
            refArgs.attach(item, self.repository)

    def kindEnd(self, itemHandler, attrs):

        if attrs['type'] == 'uuid':
            self.kindRef = UUID(self.data)
        else:
            self.kindRef = Path(self.data)

        self.kind = self.repository.find(self.kindRef)
        if self.kind is None:
            if self.withSchema:
                if self.afterLoadHooks is not None:
                    self.afterLoadHooks.append(self._setKind)
            else:
                raise ValueError, "Kind %s not found" %(self.kindRef)

    def _setKind(self):

        if self.item._kind is None:
            self.kind = self.repository.find(self.kindRef)
            if self.kind is None:
                raise ValueError, 'Kind %s not found' %(self.kindRef)
            else:
                self.item._setKind(self.kind)

    def parentEnd(self, itemHandler, attrs):

        if attrs['type'] == 'uuid':
            self.parentRef = UUID(self.data)
        else:
            self.parentRef = Path(self.data)

        self.parent = self.repository.find(self.parentRef)
        if self.parent is None:
            if self.afterLoadHooks is not None:
                self.afterLoadHooks.append(self._move)
            else:
                raise ValueError, "Parent %s not found" %(self.parentRef)

    def _move(self):

        if self.item._parent is None:
            self.parent = self.repository.find(self.parentRef)
            if self.parent is None:
                raise ValueError, 'Parent %s not found' %(self.parentRef)
            else:
                self.item.move(self.parent)

    def classEnd(self, itemHandler, attrs):

        self.cls = Item.loadClass(self.data, attrs['module'])

    def nameEnd(self, itemHandler, attrs):

        self.name = self.data

    def attributeEnd(self, itemHandler, attrs, **kwds):

        if kwds.has_key('value'):
            value = kwds['value']
        else:
            attribute = self.attributes.pop()
            cardinality = self.getCardinality(attribute, attrs)
            typeName = self.getTypeName(attribute, attrs)

            if cardinality == 'dict' or typeName == 'dict':
                value = self.collections.pop()
            elif cardinality == 'list' or typeName == 'list':
                value = self.collections.pop()
            else:
                value = self.makeValue(typeName, self.data)
            
        self.values[attrs['name']] = value

    def refEnd(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            attribute = self.attributes.pop()
            cardinality = self.getCardinality(attribute, attrs)
            otherCard = attrs.get('otherCard', None)
        else:
            cardinality = 'single'
            otherCard = self.tagAttrs[-1].get('otherCard', None)

        if cardinality == 'single':
            typeName = attrs.get('type', 'path')

            if typeName == 'path':
                ref = Path(self.data)
            else:
                ref = UUID(self.data)

            if self.collections:
                name = self.refName(attrs, 'name')
                previous = self.refName(attrs, 'previous')
                next = self.refName(attrs, 'next')

                self.refs.append(RefArgs(self.collections[-1]._name, name,
                                         ref, self.collections[-1]._otherName,
                                         otherCard, self.collections[-1],
                                         previous, next))
            else:
                name = attrs['name']
                otherName = self.getOtherName(name, self.getAttribute(name),
                                              attrs)
                self.refs.append(RefArgs(name, name, ref, otherName, otherCard,
                                         self.references))
        else:
            value = self.collections.pop()
            self.references[attrs['name']] = value

    def dbEnd(self, itemHandler, attrs):
            
        if not self.collections:
            raise ValueError, self.tagAttrs[-1]['name']

        refDict = self.collections[-1]
        refDict._prepareKey(UUID(self.tagAttrs[-2]['uuid']), UUID(self.data))

        otherCard = self.tagAttrs[-1].get('otherCard', None)

        for ref in refDict._dbRefs():
            if refDict._ordered:
                args = RefArgs(refDict._name, ref[0], ref[1],
                               refDict._otherName, otherCard, refDict,
                               ref[2], ref[3])
            else:
                args = RefArgs(refDict._name, ref[0], ref[1],
                               refDict._otherName, otherCard, refDict)

            self.refs.append(args)

    def valueStart(self, itemHandler, attrs):

        typeName = attrs.get('type')
        if typeName == 'dict':
            self.collections.append({})
        elif typeName == 'list':
            self.collections.append([])
        else:
            self.setupTypeDelegate(attrs)

    # valueEnd is called when parsing 'dict' or 'list' cardinality values of
    # one type (type specified with cardinality) or of unspecified type
    # (type specified with value) or 'dict' or 'list' type values of 'single'
    # or unspecified cardinality or values of type 'Dictionary' or 'List' of
    # any cardinality. A mess of overloading.
    
    def valueEnd(self, itemHandler, attrs, **kwds):

        # case of parsing 'Dictionary' or 'List' of non 'single' cardinality
        if kwds.has_key('value'):
            value = kwds['value']
        else:
            typeName = attrs.get('type')
            if typeName == 'dict' or typeName == 'list':
                # case of parsing 'single' 'list' or 'dict' type value
                value = self.collections.pop()

            else:
                if typeName is None:
                    cardinality = self.getCardinality(self.attributes[-1],
                                                      self.tagAttrs[-1])
                    if cardinality == 'dict' or cardinality == 'list':
                        # case of parsing non 'single' 'list' or 'dict' type
                        # value of one type specified with cardinality
                        typeName = self.getTypeName(self.attributes[-1],
                                                    self.tagAttrs[-1])
                    else:
                        # case of parsing a collection value of type string
                        # which is unspecified
                        typeName = 'str'
                else:
                    # case of parsing a collection value of a specific type
                    pass

                value = self.makeValue(typeName, self.data)

        name = attrs.get('name')

        if name is None:
            self.collections[-1].append(value)
        else:
            name = self.makeValue(attrs.get('nameType', 'str'), name)
            self.collections[-1][name] = value

    def getCardinality(self, attribute, attrs):

        cardinality = attrs.get('cardinality')

        if cardinality is None:
            if attribute is None:
                cardinality = 'single'
            else:
                cardinality = attribute.getAspect('Cardinality', 'single')

        return cardinality

    def getTypeName(self, attribute, attrs):

        attrType = attrs.get('type')

        if attrType is None and attribute is not None:
            attrType = attribute.getAspect('Type', None)
            if attrType is not None:
                return type(attrType).__name__

        return attrType or 'str'

    def refName(self, attrs, attr):

        if attrs.has_key(attr):
            return self.makeValue(attrs.get(attr + 'Type', 'str'), attrs[attr])
        else:
            return None

    def getOtherName(self, name, attribute, attrs):

        otherName = attrs.get('otherName')

        if otherName is None and attribute is not None:
            otherName = attribute.getAspect('OtherName')

        if otherName is None:
            raise TypeError, 'Undefined other endpoint for %s' %(name)

        return otherName

    def getAttribute(self, name):

        if self.withSchema is False and self.kind is not None:
            return self.kind.getAttribute(name)
        else:
            return None

    def setupTypeDelegate(self, attrs):
        
        if self.attributes[-1]:
            attrType = self.attributes[-1].getAspect('Type')
            if attrType is not None:
                self.delegates.append(attrType)

    def makeValue(self, typeName, data):

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

        if typeName == 'str':
            return str(data)

        if typeName == 'unicode':
            return unicode(data)

        if typeName == 'uuid':
            return UUID(data)
        
        if typeName == 'path':
            return Path(data)

        if typeName == 'bool':
            return data != 'False'

        if typeName == 'int':
            return int(data)

        if typeName == 'long':
            return long(data)

        if typeName == 'float':
            return float(data)

        if typeName == 'complex':
            return complex(data)

        if typeName == 'class':
            return Item.loadClass(str(data))

        if typeName == 'NoneType':
            return None

        raise ValueError, "Unknown type: %s" %(typeName)

    def typeName(cls, value):

        typeHandler = cls.typeHandlers.get(type(value))

        if typeHandler is not None:
            return typeHandler.handlerName()
        elif isinstance(value, UUID):
            return 'uuid'
        elif isinstance(value, Path):
            return 'path'
        else:
            return type(value).__name__

    def makeString(cls, value):

        typeHandler = cls.typeHandlers.get(type(value))

        if typeHandler is not None:
            return typeHandler.makeString(value)
        else:
            return str(value)
            
    def xmlValue(cls, name, value, tag, attrType, attrCard,
                 generator, withSchema):

        attrs = {}
            
        if name is not None:
            if isinstance(name, UUID):
                attrs['nameType'] = 'uuid'
                attrs['name'] = name.str64()
            elif not isinstance(name, str) and not isinstance(name, unicode):
                attrs['nameType'] = cls.typeName(name)
                attrs['name'] = str(name)
            else:
                attrs['name'] = name

        if attrCard == 'single':
            if not isinstance(value, str) and not isinstance(value, unicode):
                if attrType is None:
                    attrs['type'] = cls.typeName(value)
                elif withSchema:
                    attrs['type'] = attrType.handlerName()
        else:
            attrs['cardinality'] = attrCard

        generator.startElement(tag, attrs)

        if withSchema or attrType is None or attrCard != 'single':
            if isinstance(value, dict):
                for val in value.iteritems():
                    cls.xmlValue(val[0], val[1], 'value', attrType, 'single',
                                 generator, withSchema)
            elif isinstance(value, list):
                for val in value:
                    cls.xmlValue(None, val, 'value', attrType, 'single',
                                 generator, withSchema)
            else:
                generator.characters(cls.makeString(value))
        else:
            attrType.typeXML(value, generator)

        generator.endElement(tag)

    typeName = classmethod(typeName)
    makeString = classmethod(makeString)
    xmlValue = classmethod(xmlValue)
