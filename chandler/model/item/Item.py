
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax

from ItemRef import ItemRef
from ItemRef import Attributes, References, RefDict

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
        separate dictionary and need to be added first with Item.setAttribute()
        before they can be accessed or set with the '.' operator.
        When an item is persisted only the Chandler attributes are saved.'''
        
        super(Item, self).__init__()

        self._status = 0
        self._uuid = _kwds.get('_uuid') or UUID()

        attributes = _kwds.get('_attributes')
        if attributes is not None:
            attributes._setItem(self)
            self._attributes = attributes
        else:
            self._attributes = Attributes(self)

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
            self._setRoot(parent._addItem(self), _kwds.get('_loading', False))
        else:
            self._parent = None

        self._kind = None
        self._setKind(kind, loading=_kwds.get('_loading', False))

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

        return self.getAttribute(name)

    def __setattr__(self, name, value):

        if name[0] != '_':
            if self._attributes.has_key(name):
                self.setAttribute(name, value, _attrDict=self._attributes)
                return
            elif self._references.has_key(name):
                self.setAttribute(name, value, _attrDict=self._references)
                return

        super(Item, self).__setattr__(name, value)

    def __delattr__(self, name):

        if self._attributes.has_key(name):
            self.removeAttribute(name, _attrDict=self._attributes)
        elif self._references.has_key(name):
            self.removeAttribute(name, _attrDict=self._references)
        else:
            super(Item, self).__delattr__(name)

    def _otherName(self, name):

        otherName = self.getAttrAspect(name, 'OtherName')

        if otherName is None:
            if name.endswith('__for'):
                otherName = name[:-5]
            else:
                otherName = name + '__for'
            print 'Warning: Undefined endpoint for %s.%s' %(self.getPath(),
                                                            name)

        return otherName

    def hasAttrAspect(self, name, aspect):

        if self._kind is not None:
            attrDef = self._kind.getAttrDef(name)
            if attrDef is not None:
                return attrDef.hasAspect(aspect)

        return False

    def getAttrAspect(self, name, aspect, default=None):

        if self._kind is not None:
            attrDef = self._kind.getAttrDef(name)
            if attrDef is not None:
                return attrDef.getAspect(aspect, default)

        return default

    def setAttribute(self, name, value=None, _attrDict=None):
        """Create and/or set a Chandler attribute.

        This method is only required when the Chandler attribute doesn't yet
        exist or when there is an ambiguity between a python and a Chandler
        attribute, a situation best avoided."""

        isItem = isinstance(value, Item)
        isRef = not isItem and (isinstance(value, ItemRef) or
                                isinstance(value, RefDict))

        if _attrDict is None:
            if self._attributes.has_key(name):
                _attrDict = self._attributes
            elif self._references.has_key(name):
                _attrDict = self._references

        if _attrDict is self._references:
            if not (isItem or isRef):
                del _attrDict[name]
            else:
                old = _attrDict.get(name)

                if isinstance(old, ItemRef):
                    old.reattach(_attrDict, self, name,
                                 old.other(self), value, self._otherName(name))
                    return
                else:
                    old.clear()

        elif (isItem or isRef) and _attrDict is self._attributes:
            del _attrDict[name]

        if isItem:
            otherName = self._otherName(name)
            card = self.getAttrAspect(name, 'Cardinality', 'single')

            if card == 'dict':
                refs = self._refDict(name, otherName)
                value = ItemRef(refs, self, name, value, otherName)
                refs[value._getItem().refName(name)] = value
                value = refs
            elif card == 'list':
                refs = self._refDict(name, otherName, True)
                value = ItemRef(refs, self, name, value, otherName)
                refs[value._getItem().refName(name)] = value
                value = refs
            else:
                value = ItemRef(self._references, self, name, value, otherName)

            self._references[name] = value

        elif isRef:
            self._references[name] = value

        else:
            self._attributes[name] = value

    def getAttribute(self, name, _attrDict=None, **kwds):
        """Return the named Chandler attribute value.

        If the attribute is not set then attempt to inherit a value if the
        attribute's InheritFrom aspect is set, attempt to return the value
        of the optional 'default' keyword passed to this method, attempt to
        return the value of its Default aspect if set, or finally raise 
        AttributeError. 
        Calling this method is only required when there is a name ambiguity
        between a python and a Chandler attribute, a situation best avoided."""

        try:
            if (_attrDict is self._attributes or
                _attrDict is None and self._attributes.has_key(name)):
                return self._attributes[name]

            elif (_attrDict is self._references or
                  _attrDict is None and self._references.has_key(name)):
                value = self._references[name]
                if isinstance(value, ItemRef):
                    return value.other(self)
                return value

        except KeyError:
            pass

        inherit = self.getAttrAspect(name, 'InheritFrom', None)
        if inherit is not None:
            value = self
            for attr in inherit.split('.'):
                value = value.getAttribute(attr)

            return value

        elif kwds.has_key('default'):
            return kwds['default']

        elif self.hasAttrAspect(name, 'Default'):
            return self.getAttrAspect(name, 'Default')

        raise AttributeError, name

    def removeAttribute(self, name, _attrDict=None):
        'Remove a Chandler attribute.'

        if _attrDict is None:
            if self._attributes.has_key(name):
                _attrDict = self._attributes
            elif self._references.has_key(name):
                _attrDict = self._references

        if _attrDict is self._attributes:
            del _attrDict[name]
        elif _attrDict is self._references:
            value = _attrDict[name]
            del _attrDict[name]

            if isinstance(value, ItemRef):
                value.detach(_attrDict, self, name,
                             value.other(self), self._otherName(name))
            elif isinstance(value, RefDict):
                value.clear()

    def attributes(self, attributesOnly=False, referencesOnly=False):
        '''Get a generator of (name, value) tuples for attributes of this item.

        By setting attributesOnly to True, no item references are returned.
        By setting referencesOnly to True, only references are returned.'''

        if not referencesOnly:
            for attr in self._attributes.iteritems():
                yield attr

        if not attributesOnly:
            for ref in self._references.iteritems():
                if isinstance(ref[1], ItemRef):
                    yield (ref[0], ref[1].other(self))
                else:
                    yield ref

    def getValue(self, attribute, key, default=None, _attrDict=None):
        'Get a value from a multi-valued attribute.'

        if _attrDict is None:
            value = (self._attributes.get(attribute, None) or
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
                _attrDict = self._attributes

        attrValue = _attrDict.get(attribute, None)
            
        if attrValue is None:
            card = self.getAttrAspect(attribute, 'Cardinality', 'single')
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
                _attrDict = self._attributes
                
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

        value = (self._attributes.get(attribute, None) or
                 self._references.get(attribute, None))

        if isinstance(value, dict):
            return value.has_key(key)
        elif isinstance(value, list):
            return 0 <= key and key < len(value)
        elif value is not None:
            raise TypeError, "%s is not multi-valued" %(attribute)

        return False

    def hasValue(self, attribute, value):
        'Tell whether a multi-valued attribute has a given value.'

        attrValue = (self._attributes.get(attribute, None) or
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
        When the cardinality of the attribute is 'list' and its values are
        references, key must be an integer or the refName of the item value
        to remove."""

        self.setDirty()

        if _attrDict is not None:
            value = _attrDict.get(attribute, None)
        else:
            value = (self._attributes.get(attribute, None) or
                     self._references.get(attribute, None))

        card = self.getAttrAspect(attribute, 'Cardinality', 'single')
        
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

    def hasAttribute(self, name, _attrDict=None):
        'Check for existence of a Chandler attribute.'

        if _attrDict is None:
            return (self._attributes.has_key(name) or
                    self._references.has_key(name))
        else:
            return _attrDict.has_key(name)

    def isDeleted(self):

        return (self._status & Item.DELETED) != 0
    
    def isDirty(self):

        return (self._status & Item.DIRTY) != 0

    def setDirty(self):

        if self._status & Item.DIRTY == 0:
            self.getRepository().addTransaction(self)
            self._status |= Item.DIRTY

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

            self._attributes.clear()

            for name in self._references.keys():
                policy = self.getAttrAspect(name, 'DeletePolicy', 'remove')
                if policy == 'cascade':
                    value = self._references[name]
                    if value is not None:
                        if isinstance(value, ItemRef):
                            others.append(value.other(self))
                        elif isinstance(value, RefDict):
                            others.extend(value.others())
                    
                self.removeAttribute(name, _attrDict=self._references)

            self._parent._removeItem(self)
            self._setRoot(None)

            self._status |= Item.DELETED
            self._status &= ~Item.DELETING

            for other in others:
                if other.refCount() == 0:
                    other.delete()
        
    def getName(self):
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
                policy = self.getAttrAspect(name, 'CountPolicy', 'none')
                if policy == 'count':
                    count += self._references[name]._refCount()

        return count
        
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

    def _setRoot(self, root, loading=False):

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

                if not loading:
                    self.setDirty()

        for child in self:
            child._setRoot(root, loading)

    def getParent(self):
        """Return this item's container parent.

        To change the parent, use Item.move()."""

        return self._parent

    def _setKind(self, kind, loading=False):

        if self._kind is not None:
            self._kind.detach('Items', self)

        self._kind = kind

        if self._kind is not None:
            ref = ItemRef(self._references, self, 'Kind',
                          self._kind, 'Items', 'dict',
                          loading)
            self._references.__setitem__('Kind', ref, loading)

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

    def move(self, parent, loading=False):
        'Move this item under another container or make it a root.'

        if self._parent is not parent:
            self._parent._removeItem(self)
            self._setRoot(parent._addItem(self), loading)
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

        del self._children[item.getName()]

    def getChild(self, name):
        'Return the child as named or None if not found.'

        if self.__dict__.has_key('_children'):
            return self._children.get(name)

        return None

    def IsRemote(self):
        '''by default, an item is not remote'''
        return False

    def find(self, spec, _index=0):
        '''Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the item unless the path is absolute.'''

        if isinstance(spec, Path):
            l = len(spec)

            if l == 0 or _index >= l:
                return None

            if _index == 0:
                if spec[0] == '//':
                    return self.getRepository().find(spec, 1)

                elif spec[0] == '/':
                    if self._root is self:
                        return self.find(spec, 1)
                    else:
                        return self._root.find(spec, 1)

            if spec[_index] == '.':
                if _index == l - 1:
                    return self
                return self.find(spec, _index + 1)

            if spec[_index] == '..':
                if _index == l - 1:
                    return self._parent
                return self._parent.find(spec, _index + 1)

            child = self.getChild(spec[_index])
            if child is not None:
                if _index == l - 1:
                    return child
                return child.find(spec, _index + 1)

        elif isinstance(spec, UUID):
            return self.getRepository().find(spec)

        elif isinstance(spec, str) or isinstance(spec, unicode):
            if (spec[0] != '/' and
                (len(spec) == 36 and spec[8] == '-' or len(spec) == 22)):
                return self.find(UUID(spec))

            return self.find(Path(spec))

        return None

    def _saveItem(self, generator, withSchema=False):

        kind = self._kind
        generator.startElement('item', { 'uuid': self._uuid.str64() })

        self._xmlTag('name', {}, self._name, generator)

        if not withSchema and kind is not None:
            self._xmlTag('kind', { 'type': 'uuid' },
                         kind.getUUID().str64(), generator)

        if withSchema or kind is None or kind.Class is not type(self):
            self._xmlTag('class', { 'module': self.__module__ },
                         type(self).__name__, generator)

        if self._root is not self:
            self._xmlTag('parent', { 'type': 'uuid' },
                         self._parent.getUUID().str64(), generator)

        self._saveAttrs(generator, withSchema)
        self._saveRefs(generator, withSchema)

        generator.endElement('item')

    def _saveAttrs(self, generator, withSchema):

        for attr in self._attributes.iteritems():
            if self.getAttrAspect(attr[0], 'Persist', True):
                attrType = self.getAttrAspect(attr[0], 'Type')
                attrCard = self.getAttrAspect(attr[0], 'Cardinality', 'single')
                self._xmlValue(attr[0], attr[1], 'attribute',
                               attrType, attrCard, generator, withSchema)

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.iteritems():
            if self.getAttrAspect(attr[0], 'Persist', True):
                attr[1]._saveValue(attr[0], self, generator, withSchema)

    def _xmlTag(self, tag, attrs, value, generator):

        generator.startElement(tag, attrs)
        generator.characters(value)
        generator.endElement(tag)

    def _xmlValue(self, name, value, tag, attrType, attrCard,
                  generator, withSchema):

        attrs = {}
            
        if name is not None:
            if isinstance(name, UUID):
                attrs['nameType'] = "uuid"
                attrs['name'] = name.str64()
            elif not isinstance(name, str) and not isinstance(name, unicode):
                attrs['nameType'] = ItemHandler.typeName(name)
                attrs['name'] = str(name)
            else:
                attrs['name'] = name

        if attrCard == 'single':
            if not isinstance(value, str):
                if attrType is None:
                    attrs['type'] = ItemHandler.typeName(value)
                elif withSchema:
                    attrs['type'] = attrType.handlerName()
        else:
            attrs['cardinality'] = attrCard

        generator.startElement(tag, attrs)

        if isinstance(value, dict):
            for val in value.iteritems():
                self._xmlValue(val[0], val[1], 'value', attrType, 'single',
                               generator, withSchema)
        elif isinstance(value, list):
            for val in value:
                self._xmlValue(None, val, 'value', attrType, 'single',
                               generator, withSchema)
        else:
            if withSchema or attrType is None:
                generator.characters(ItemHandler.makeString(value))
            else:
                attrType.typeXML(value, generator)

        generator.endElement(tag)

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
    
    def __init__(self, repository, parent, afterLoadHooks, loading):

        self.repository = repository
        self.parent = parent
        self.afterLoadHooks = afterLoadHooks
        self.loading = loading

    def startDocument(self):

        self.tagAttrs = []
        self.tags = []
        self.delegates = []
        self.fields = None
        
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

        attrDef = self.getAttrDef(attrs['name'])
        self.attrDefs.append(attrDef)

        cardinality = self.getCardinality(attrDef, attrs)
        typeName = attrs.get('type')
        
        if cardinality == 'dict' or typeName == 'dict':
            self.collections.append({})
        elif cardinality == 'list' or typeName == 'list':
            self.collections.append([])
        else:
            self.setupTypeDelegate(attrs)

    def refStart(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            name = attrs['name']
            attrDef = self.getAttrDef(name)
            self.attrDefs.append(attrDef)

            cardinality = self.getCardinality(attrDef, attrs)

            if cardinality != 'single':
                otherName = self.getOtherName(name, attrDef, attrs)
                refDict = self.repository.createRefDict(None, name, otherName,
                                                        cardinality == 'list')
                self.collections.append(refDict)

    def itemStart(self, itemHandler, attrs):

        self.attributes = Attributes(None)
        self.references = References(None)
        self.refs = []
        self.collections = []
        self.attrDefs = []
        self.name = None
        self.kind = None
        self.cls = None
        self.parentRef = None
                
    def itemEnd(self, itemHandler, attrs):

        cls = (self.cls or
               self.kind and getattr(self.kind, 'Class', Item) or
               Item)

        if self.parentRef is not None:
            parent = self.repository.find(self.parentRef)
        else:
            parent = self.parent

        self.item = item = cls(self.name, parent, self.kind,
                               _uuid = UUID(attrs.get('uuid')),
                               _attributes = self.attributes,
                               _references = self.references,
                               _afterLoadHooks = self.afterLoadHooks,
                               _loading=self.loading)

        if parent is None:
            self.repository._addOrphan(self.parentRef, item)

        for ref in self.refs:
            if isinstance(ref[1], UUID):
                other = self.repository.find(ref[1])
            else:
                other = item.find(ref[1])
            
            if len(ref) == 3:
                attrName = refName = ref[0][0]
                otherName = ref[0][1]
                valueDict = item._references
                otherCard = ref[2]
            else:
                attrName = ref[2]._name
                refName = ref[0]
                if refName is None:
                    if other is None:
                        raise ValueError, "refName to %s is unspecified, %s should be loaded before %s" %(ref[1], ref[1], item.getPath())
                    else:
                        refName = other.refName(attrName)
                otherName = ref[2]._otherName
                valueDict = ref[2]
                otherCard = ref[3]

            if other is not None:
                value = other._references.get(otherName)
                if value is None:
                    ref = ItemRef(valueDict, item, attrName,
                                  other, otherName, otherCard,
                                  self.loading)
                    valueDict.__setitem__(refName, ref, self.loading)
                elif isinstance(value, ItemRef):
                    if value._other is None:
                        value._other = item
                        valueDict[refName] = value
                        if not self.loading:
                            valueDict._attach(value, other, otherName,
                                              item, attrName)
                elif isinstance(value, RefDict):
                    otherRefName = item.refName(otherName)
                    if value.has_key(otherRefName):
                        value = value._getRef(otherRefName)
                        if value._other is None:
                            value._other = item
                            valueDict.__setitem__(refName, value, self.loading)
                            if not self.loading:
                                valueDict._attach(value, other, otherName,
                                                  item, attrName)
                    else:
                        ref = ItemRef(valueDict, item, attrName,
                                      other, otherName, otherCard,
                                      self.loading)
                        valueDict.__setitem__(refName, ref, self.loading)
            else:
                value = ItemRef(valueDict, item, attrName,
                                other, otherName, otherCard, self.loading)
                valueDict.__setitem__(refName, value, self.loading)
                self.repository._appendRef(item, attrName,
                                           ref[1], otherName, otherCard,
                                           value, valueDict)

    def kindEnd(self, itemHandler, attrs):

        if attrs['type'] == 'uuid':
            kindRef = UUID(self.data)
        else:
            kindRef = Path(self.data)

        self.kind = self.repository.find(kindRef)
        if self.kind is None:
            raise ValueError, "Kind %s not found" %(str(kindRef))

    def classEnd(self, itemHandler, attrs):

        self.cls = Item.loadClass(self.data, attrs['module'])

    def nameEnd(self, itemHandler, attrs):

        self.name = self.data

    def parentEnd(self, itemHandler, attrs):

        if attrs['type'] == 'uuid':
            self.parentRef = UUID(self.data)
        else:
            self.parentRef = Path(self.data)

    def attributeEnd(self, itemHandler, attrs, **kwds):

        attrDef = self.attrDefs.pop()
        cardinality = self.getCardinality(attrDef, attrs)

        if kwds.has_key('value'):
            value = kwds['value']
        elif cardinality == 'single':
            value = self.makeValue(attrs.get('type', 'str'), self.data)
        else:
            value = self.collections.pop()
            
        self.attributes[attrs['name']] = value

    def refEnd(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            attrDef = self.attrDefs.pop()
            cardinality = self.getCardinality(attrDef, attrs)
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
                if attrs.has_key('name'):
                    name = self.makeValue(attrs.get('nameType', 'str'),
                                          attrs['name'])
                else:
                    name = None
                self.refs.append((name, ref, self.collections[-1], otherCard))
            else:
                name = attrs['name']
                otherName = self.getOtherName(name, self.getAttrDef(name),
                                              attrs)
                self.refs.append(((name, otherName), ref, otherCard))

        else:
            value = self.collections.pop()
            self.references[attrs['name']] = value

    def dbEnd(self, itemHandler, attrs):

        refDict = self.collections[-1]
        refDict._prepareKey(UUID(self.tagAttrs[-2]['uuid']), UUID(self.data))

        otherCard = self.tagAttrs[-1].get('otherCard', None)

        for ref in refDict._dbRefs():
            self.refs.append((ref[0], ref[1], refDict, otherCard))

    def valueStart(self, itemHandler, attrs):

        self.setupTypeDelegate(attrs)

    def valueEnd(self, itemHandler, attrs, **kwds):

        typeName = attrs.get('type', 'str')

        if typeName == 'dict' or typeName == 'list':
            value = self.collections.pop()
        elif kwds.has_key('value'):
            value = kwds['value']
        else:
            value = self.makeValue(typeName, self.data)

        name = attrs.get('name')
        if name is None:
            self.collections[-1].append(value)
        else:
            name = self.makeValue(attrs.get('nameType', 'str'), name)
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
            print 'Warning: Undefined endpoint for %s.%s' %(item.getPath(),
                                                            name)

        return otherName

    def getAttrDef(self, name):

        if self.kind is not None:
            return self.kind.getAttrDef(name)
        else:
            return None

    def setupTypeDelegate(self, attrs):
        
        if self.attrDefs[-1]:
            attrType = self.attrDefs[-1].getAspect('Type')
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
            
    typeName = classmethod(typeName)
    makeString = classmethod(makeString)
