
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import cStringIO

from ItemRef import ItemRef, RefArgs
from ItemRef import Values, References, RefDict
from ItemHandler import ItemHandler

from model.util.UUID import UUID
from model.util.Path import Path
from model.util.LinkedMap import LinkedMap


class Item(object):
    'The root class for all items.'
    
    def __init__(self, name, parent, kind):
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
        self._uuid = UUID()

        self._values = Values(self)
        self._references = References(self)
        
        self._name = name or self._uuid.str64()
        self._kind = None
        self._root = None

        self._setParent(parent)
        self._setKind(kind)

    def _fillItem(self, name, parent, kind, **kwds):

        self._uuid = kwds['uuid']
        self._name = name or self._uuid.str64()
        self._kind = None
        self._root = None
        self._status = 0

        kwds['values']._setItem(self)
        self._values = kwds['values']
        
        kwds['references']._setItem(self)
        self._references = kwds['references']

        self._setParent(parent, kwds.get('previous'), kwds.get('next'))
        self._setKind(kind)

    def __iter__(self):

        return self.iterChildren()
    
    def __repr__(self):

        if self._status & Item.RAW:
            return super(Item, self).__repr__()
        
        return "<%s: %s %s>" %(type(self).__name__, self._name,
                               self._uuid.str16())

    def __getattr__(self, name):

        if self._status & Item.DELETED:
            raise ValueError, "item is deleted: %s" %(self)

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

        otherName = self.getAttributeAspect(name, 'otherName')
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
            card = self.getAttributeAspect(name, 'cardinality', 'single')

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
        attribute's inheritFrom aspect is set, attempt to return the value
        of the optional 'default' keyword passed to this method, attempt to
        return the value of its defaultValue aspect if set, or finally raise 
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

        inherit = self.getAttributeAspect(name, 'inheritFrom', None)
        if inherit is not None:
            value = self
            for attr in inherit.split('.'):
                value = value.getAttributeValue(attr)

            return value

        elif kwds.has_key('default'):
            return kwds['default']

        elif self.hasAttributeAspect(name, 'defaultValue'):
            return self.getAttributeAspect(name, 'defaultValue')

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

    def hasChild(self, name, load=True):

        return (self.__dict__.has_key('_children') and
                self._children.has_key(name))

    def iterChildren(self, load=True):

        if not load:
            if self.__dict__.has_key('_children'):
                for child in self._children._itervalues():
                    yield child

        elif self.__dict__.has_key('_children'):
            for child in self._children:
                yield child

    def iterAttributes(self, valuesOnly=False, referencesOnly=False):
        """Get a generator of (name, value) tuples for attributes of this item.

        By setting valuesOnly to True, no item references are returned.
        By setting referencesOnly to True, only references are returned."""

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

        for ref in self.iterAttributes(referencesOnly=True):
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
            card = self.getAttributeAspect(attribute, 'cardinality', 'single')
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

        card = self.getAttributeAspect(attribute, 'cardinality', 'single')
        
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
            
            for child in self:
                child.delete()

            self._values.clear()

            for name in self._references.keys():
                policy = self.getAttributeAspect(name, 'deletePolicy',
                                                 'remove')
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

    def getItemDisplayName(self):
        """Return this item's display name.

        By definition, the display name is, in order of precedence, the
        value of the 'displayName' attribute, the value of the attribute
        named by the item's Kind 'displayAttribute' attribute or the item's
        intrinsic name."""

        if self.hasAttributeValue('displayName'):
            return self.displayName

        if self._kind is not None:
            if self._kind.hasAttributeValue('displayAttribute'):
                displayAttribute = self._kind.displayAttribute
                if self.hasAttributeValue(displayAttribute):
                    return self.getAttributeValue(displayAttribute)
                
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
                policy = self.getAttributeAspect(name, 'countPolicy', 'none')
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

        for child in self.iterChildren(load=False):
            child._setRoot(root)

    def getItemParent(self):
        """Return this item's container parent.

        To change the parent, use Item.move()."""

        return self._parent

    def _setKind(self, kind):

        if self._kind is not None:
            self._kind.detach('items', self)

        self._kind = kind

        if self._kind is not None:
            ref = ItemRef(self, 'kind', self._kind, 'items', 'dict')
            self._references['kind'] = ref

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

    def move(self, parent, previous=None, next=None):
        'Move this item under another container or make it a root.'

        if self._parent is not parent:
            self._parent._removeItem(self)
            self._setRoot(parent._addItem(self, previous, next))
            self._parent = parent

    def _setParent(self, parent, previous=None, next=None):

        if parent is not None:
            self._parent = parent
            self._setRoot(parent._addItem(self, previous, next))
        else:
            self._parent = None

    def _addItem(self, item, previous=None, next=None):

        name = item._name
        
        if self.__dict__.has_key('_children'):

            loading = self.getRepository().isLoading()
            if loading:
                current = self._children.get(name)
            else:
                current = self.getItemChild(name)
                
            if current is not None:
                if loading:
                    print "Warning, deleting %s while loading" %(current)
                current.delete()

        else:
            self._children = Children(self)

        self._children.__setitem__(name, item, previous, next)

        if (self.__dict__.has_key('_notChildren') and
            self._notChildren.has_key(name)):
            del self._notChildren[name]
            
        return self._root

    def _removeItem(self, item):

        del self._children[item.getItemName()]

    def getItemChild(self, name, load=True):
        'Return the child as named or None if not found.'

        child = None
        if self.__dict__.has_key('_children'):
            child = self._children.get(name)

        if load and child is None:
            hasNot = self.__dict__.has_key('_notChildren')
            if not hasNot or not self._notChildren.has_key(name):
                child = self.getRepository()._loadChild(self, name)
                if child is None:
                    if not hasNot:
                        self._notChildren = { name: name }
                    else:
                        self._notChildren[name] = name

        return child

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

    def toXML(self):

        try:
            out = cStringIO.StringIO()
            generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')
            generator.startDocument()
            self._xmlItem(generator, self.getRoot().getItemName() == 'Schema')
            generator.endDocument()

            return out.getvalue()
        finally:
            out.close()

    def _saveItem(self, generator, withSchema='False'):

        self._xmlItem(generator, withSchema, 'save')

    def _xmlItem(self, generator, withSchema=False, mode='serialize'):

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

        attrs = {}

        if self._root is not self:
            parentID = self._parent.getUUID().str64()

            link = self._parent._children._get(self._name)
            if link._previousKey is not None:
                attrs['previous'] = link._previousKey
            if link._nextKey is not None:
                attrs['next'] = link._nextKey

        else:
            parentID = self.getRepository().ROOT_ID.str64()

        if self.__dict__.has_key('_children'):
            children = self._children
            if children._firstKey is not None:
                attrs['first'] = children._firstKey
            if children._lastKey is not None:
                attrs['last'] = children._lastKey

        xmlTag('container', attrs, parentID, generator)

        self._xmlAttrs(generator, withSchema, mode)
        self._xmlRefs(generator, withSchema, mode)

        generator.endElement('item')

    def _loadItem(self):

        return self

    def _xmlAttrs(self, generator, withSchema, mode):

        for attr in self._values.iteritems():
            if self.getAttributeAspect(attr[0], 'persist', True):
                attrType = self.getAttributeAspect(attr[0], 'type')
                attrCard = self.getAttributeAspect(attr[0], 'cardinality',
                                                   'single')
                ItemHandler.xmlValue(attr[0], attr[1], 'attribute',
                                     attrType, attrCard, generator,
                                     withSchema)

    def _xmlRefs(self, generator, withSchema, mode):

        for attr in self._references.iteritems():
            if self.getAttributeAspect(attr[0], 'persist', True):
                attr[1]._xmlValue(attr[0], self, generator, withSchema, mode)

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

    def __new__(cls, *args):

        item = object.__new__(cls, *args)
        item._status = Item.RAW

        return item


    loadClass = classmethod(loadClass)
    __new__ = classmethod(__new__)
    
    DELETED  = 0x1
    DIRTY    = 0x2
    DELETING = 0x4
    RAW      = 0x8


class Children(LinkedMap):

    def __init__(self, item, dictionary=None):

        super(Children, self).__init__(dictionary)
        self._item = item
        
    def linkChanged(self, link):

        self._item.setDirty()
    
    def __repr__(self):

        buffer = cStringIO.StringIO()
        try:
            buffer.write('{(currenly loaded) ')
            first = True
            for key, value in self._iteritems():
                if not first:
                    buffer.write(', ')
                else:
                    first = False
                buffer.write(key.__repr__())
                buffer.write(': ')
                buffer.write(value.__repr__())
            buffer.write('}')

            return buffer.getvalue()
        finally:
            buffer.close()

    def _load(self, key):

        if self._item.getRepository()._loadChild(self._item, key) is not None:
            return True

        return False
