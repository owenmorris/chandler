
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.item as ItemPackage

from repository.item.PersistentCollections import PersistentCollection
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict
from repository.item.ItemRef import RefArgs, NoneRef
from repository.item.Values import Values, References, ItemValue

from repository.util.SingleRef import SingleRef
from repository.util.UUID import UUID
from repository.util.Path import Path
from repository.util.ClassLoader import ClassLoader
from repository.util.SAX import ContentHandler


class ItemHandler(ContentHandler):
    'A SAX ContentHandler implementation responsible for loading items.'
    
    typeHandlers = {}
    
    def __init__(self, repository, parent, afterLoadHooks, instance=None):

        ContentHandler.__init__(self)

        self.repository = repository
        self.parent = parent
        self.afterLoadHooks = afterLoadHooks
        self.item = None
        self.instance = instance

        if repository not in ItemHandler.typeHandlers:
            ItemHandler.typeHandlers[repository] = {}
        
    def startDocument(self):

        self.tagAttrs = []
        self.tags = []
        self.delegates = []
        self.fields = None
        self.tagCounts = []

    def startElement(self, tag, attrs):

        self.data = ''
        if attrs is None:
            attrs = {}
            
        if self.delegates:
            delegate = self.delegates[-1]
            delegateClass = type(delegate)
        else:
            delegate = self
            delegateClass = ItemHandler
            
        method = getattr(delegateClass, tag + 'Start', None)
        if method is not None:
            method(delegate, self, attrs)

        self.tags.append(tag)
        self.tagAttrs.append(attrs)

    def endElement(self, tag):
 
        withValue = False

        if self.delegates:
            delegate = self.delegates[-1]
            if delegate.isValueReady(self):
                self.delegates.pop()
                value = delegate.getParsedValue(self, self.data)
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

    def refStart(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            name = attrs['name']
            attribute = self.getAttribute(name)
            self.attributes.append(attribute)

            flags = attrs.get('flags', None)
            if flags is not None:
                flags = int(flags)
                self.values._setFlags(name, flags)
                readOnly = flags & Values.READONLY
            else:
                readOnly = False

            cardinality = self.getCardinality(attribute, attrs)

            if cardinality != 'single':
                if cardinality == 'dict':
                    self.repository.logger.warning("Warning, 'dict' cardinality for reference attribute %s on %s is deprecated, use 'list' instead",
                                                   name, self.name)

                otherName = self.getOtherName(name, attribute, attrs)
                refDict = self.repository.createRefDict(None, name, otherName,
                                                        True, readOnly)
                
                if attrs.has_key('first'):
                    firstKey = self.makeValue(attrs.get('firstType', 'str'),
                                              attrs['first'])
                    refDict._firstKey = firstKey
                if attrs.has_key('last'):
                    lastKey = self.makeValue(attrs.get('lastType', 'str'),
                                             attrs['last'])
                    refDict._lastKey = lastKey
                if attrs.has_key('count'):
                    refDict._count = int(attrs['count'])

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
        self.previous = self.next = None
        self.first = self.last = None
        self.withSchema = attrs.get('withSchema', 'False') == 'True'
        self.uuid = UUID(attrs.get('uuid'))
        self.version = long(attrs.get('version', '0L'))
        
    def itemEnd(self, itemHandler, attrs):

        cls = self.cls
        if cls is None:
            if self.kind is None:
                cls = ItemPackage.Item.Item
            else:
                cls = self.kind.getItemClass()

        if self.instance is not None:
            if cls is not type(self.instance):
                raise TypeError, 'Class for item has changed from %s to %s' %(type(instance), cls)
            item = self.item = self.instance
            pinned = item._status & item.PINNED
            item._status = item.RAW
            self.instance = None
        else:
            item = self.item = cls.__new__(cls)
            pinned = 0
            
        item._fillItem(self.name, self.parent, self.kind, uuid = self.uuid,
                       values = self.values, references = self.references,
                       previous = self.previous, next = self.next,
                       afterLoadHooks = self.afterLoadHooks,
                       version = self.version)
        if pinned:
            item._status |= item.PINNED

        if self.first or self.last:
            item._children = ItemPackage.Item.Children(item)
            item._children._firstKey = self.first
            item._children._lastKey = self.last

        self.repository._registerItem(item)

        for attribute, value in self.values.iteritems():
            if isinstance(value, PersistentCollection):
                companion = item.getAttributeAspect(attribute, 'companion',
                                                    default=None)
                value._setItem(item, attribute, companion)
            elif isinstance(value, ItemValue):
                value._setItem(item, attribute)

        for refArgs in self.refs:
            refArgs.attach(item, self.repository)

        if self.afterLoadHooks is not None:
            if hasattr(cls, 'onItemLoad'):
                self.afterLoadHooks.append(self._onItemLoad)

    def kindEnd(self, itemHandler, attrs):

        assert not self.item

        if attrs['type'] == 'uuid':
            self.kindRef = UUID(self.data)
        else:
            self.kindRef = Path(self.data)

        self.kind = self.repository._findKind(self.kindRef, self.withSchema)
        if self.kind is None:
            if self.withSchema:
                if self.afterLoadHooks is not None:
                    self.afterLoadHooks.append(self._setKind)
            else:
                raise ValueError, "While loading %s, kind %s not found" %(self.name, self.kindRef)

    def _setKind(self):

        if self.item._kind is None:
            self.kind = self.repository.find(self.kindRef)
            if self.kind is None:
                raise ValueError, 'Kind %s not found' %(self.kindRef)
            else:
                self.item._kind = self.kind

    def _onItemLoad(self):

        self.item.onItemLoad()

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

    def containerEnd(self, itemHandler, attrs):

        self.parentRef = UUID(self.data)
        self.previous = attrs.get('previous')
        self.next = attrs.get('next')
        self.first = attrs.get('first')
        self.last = attrs.get('last')

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
                self.item.move(self.parent, self.previous, self.next)

    def classEnd(self, itemHandler, attrs):

        self.cls = ClassLoader.loadClass(self.data, attrs['module'])

    def nameEnd(self, itemHandler, attrs):

        self.name = self.data

    def refEnd(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            attribute = self.attributes.pop()
            cardinality = self.getCardinality(attribute, attrs)
            otherCard = attrs.get('otherCard', None)
        else:
            cardinality = 'single'
            otherCard = self.tagAttrs[-1].get('otherCard', None)

        if cardinality == 'single':     # cardinality of tag
            typeName = attrs.get('type', 'path')

            if typeName == 'path':
                ref = Path(self.data)
            elif typeName == 'none':
                self.references[attrs['name']] = NoneRef
                return
            else:
                ref = UUID(self.data)

            if self.collections:
                name = self.refName(attrs, 'name')
                previous = self.refName(attrs, 'previous')
                next = self.refName(attrs, 'next')

                self.refs.append(RefArgs(self.collections[-1]._name, name,
                                         ref, self.collections[-1]._otherName,
                                         otherCard, self.collections[-1],
                                         previous, next, attrs.get('alias')))
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
        refDict._prepareBuffers(self.uuid, UUID(self.data))

    def attributeStart(self, itemHandler, attrs):

        attribute = self.getAttribute(attrs['name'])
        self.attributes.append(attribute)

        cardinality = self.getCardinality(attribute, attrs)
        typeName = self.getTypeName(attribute, attrs, 'str')
        
        if cardinality == 'list':
            self.collections.append(PersistentList(None, None, None))
        elif cardinality == 'dict':
            self.collections.append(PersistentDict(None, None, None))
        else:
            self.valueStart(itemHandler, attrs)

    def valueStart(self, itemHandler, attrs):

        if self.setupTypeDelegate(attrs):
            return

        if (self.tags[-1] == 'attribute' and
            self.setupTypeDelegate(self.tagAttrs[-1])):
            return

        typeName = None

        if attrs.has_key('type'):
            typeName = attrs['type']
        elif (self.tags[-1] == 'attribute' and
              self.tagAttrs[-1].has_key('type')):
            typeName = self.tagAttrs[-1]['type']

        if typeName == 'dict':
            self.collections.append(PersistentDict(None, None, None))
        elif typeName == 'list':
            self.collections.append(PersistentList(None, None, None))

    # valueEnd is called when parsing 'dict' or 'list' cardinality values of
    # one type (type specified with cardinality) or of unspecified type
    # (type specified with value) or 'dict' or 'list' type values of 'single'
    # or unspecified cardinality or values of type 'Dictionary' or 'List' of
    # any cardinality. A mess of overloading.
    
    def attributeEnd(self, itemHandler, attrs, **kwds):

        if kwds.has_key('value'):
            value = kwds['value']
        else:
            attribute = self.attributes.pop()
            cardinality = self.getCardinality(attribute, attrs)

            if cardinality == 'dict' or cardinality == 'list':
                value = self.collections.pop()
            else:
                typeName = self.getTypeName(attribute, attrs, 'str')
                if typeName == 'dict' or typeName == 'list':
                    value = self.collections.pop()
                else:
                    value = self.makeValue(typeName, self.data)
                    if attrs.has_key('eval'):
                        typeHandler = self.typeHandler(self.repository, value)
                        value = typeHandler.eval(value)
            
        if self.delegates:
            raise ValueError, "while loading '%s.%s' type delegates didn't pop: %s" %(self.name, attrs['name'], self.delegates)

        self.values[attrs['name']] = value

        flags = attrs.get('flags', None)
        if flags is not None:
            flags = int(flags)
            self.values._setFlags(attrs['name'], flags)
            if flags & Values.READONLY:
                if isinstance(value, PersistentCollection):
                    value.setReadOnly()
                elif isinstance(value, ItemValue):
                    value._setReadOnly()

    def valueEnd(self, itemHandler, attrs, **kwds):

        if kwds.has_key('value'):
            value = kwds['value']
        else:
            typeName = self.getTypeName(self.attributes[-1], attrs, None)
            if typeName is None:
                if self.tags[-1] == 'attribute':
                    typeName = self.getTypeName(self.attributes[-1],
                                                self.tagAttrs[-1], 'str')
                else:
                    typeName = 'str'
                
            if typeName == 'dict' or typeName == 'list':
                value = self.collections.pop()
            else:
                value = self.makeValue(typeName, self.data)
                if attrs.has_key('eval'):
                    typeHandler = self.typeHandler(self.repository, value)
                    value = typeHandler.eval(value)

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
                cardinality = attribute.getAspect('cardinality',
                                                  default='single')

        return cardinality

    def getTypeName(self, attribute, attrs, default):

        if attrs.has_key('typeid'):
            try:
                return self.repository[UUID(attrs['typeid'])].handlerName()
            except KeyError:
                raise TypeError, "Type %s not found" %(attrs['typeid'])

        if attrs.has_key('typepath'):
            typeItem = self.repository.find(Path(attrs['typepath']))
            if typeItem is None:
                raise TypeError, "Type %s not found" %(attrs['typepath'])
            return typeItem.handlerName()

        if attrs.has_key('type'):
            return attrs['type']

        if attribute is not None:
            attrType = attribute.getAspect('type', default=None)
            if attrType is not None:
                return attrType.handlerName()

        return default

    def refName(self, attrs, attr):

        if attrs.has_key(attr):
            return self.makeValue(attrs.get(attr + 'Type', 'str'), attrs[attr])
        else:
            return None

    def getOtherName(self, name, attribute, attrs):

        otherName = attrs.get('otherName')

        if otherName is None and attribute is not None:
            otherName = attribute.getAspect('otherName')

        if otherName is None:
            raise TypeError, 'Undefined other endpoint for %s/%s.%s of kind %s' %(self.parent.itsPath, self.name, name, self.kind.itsPath)

        return otherName

    def getAttribute(self, name):

        if self.withSchema is False and self.kind is not None:
            return self.kind.getAttribute(name)
        else:
            return None

    def setupTypeDelegate(self, attrs):

        if attrs.has_key('typeid'):
            try:
                attrType = self.repository[UUID(attrs['typeid'])]
            except KeyError:
                raise TypeError, "Type %s not found" %(attrs['typeid'])

            self.delegates.append(attrType)
            attrType.startValue(self)

            return True
        
        elif self.attributes[-1]:
            attrType = self.attributes[-1].getAspect('type')
            if attrType is not None and not attrType.isAlias():
                self.delegates.append(attrType)
                attrType.startValue(self)

                return True

        return False
    
    def makeValue(cls, typeName, data):

        try:
            return ItemHandler.typeDispatch[typeName](data)
        except KeyError:
            raise ValueError, "Unknown type %s for data: %s" %(typeName, data)

    def typeHandler(cls, repository, value):

        try:
            for uuid in cls.typeHandlers[repository][type(value)]:
                t = repository[uuid]
                if t.recognizes(value):
                    return t
        except KeyError:
            pass

        typeKind = repository[cls.typeHandlers[repository][None]]
        types = typeKind.findTypes(value)
        if types:
            return types[0]
            
        raise TypeError, 'No handler for values of type %s' %(type(value))

    def typeName(cls, repository, value):

        return cls.typeHandler(repository, value).handlerName()

    def makeString(cls, repository, value):

        return cls.typeHandler(repository, value).makeString(value)
    
    def xmlValue(cls, repository, name, value, tag,
                 attrType, attrCard, attrId, flags,
                 generator, withSchema):

        attrs = {}
            
        if name is not None:
            if not isinstance(name, str) and not isinstance(name, unicode):
                attrs['nameType'] = cls.typeName(repository, name)
                attrs['name'] = cls.makeString(repository, name)
            else:
                attrs['name'] = name

        if attrId is not None:
            attrs['id'] = attrId.str64()

        if attrCard == 'single':
            if attrType is not None and attrType.isAlias():
                aliasType = attrType.type(value)
                if aliasType is None:
                    raise TypeError, "%s does not alias type of value '%s' of type %s" %(attrType.itsPath, value, type(value))
                attrType = aliasType
                attrs['typeid'] = attrType._uuid.str64()

            elif withSchema or attrType is None:
                attrType = cls.typeHandler(repository, value)
                attrs['typeid'] = attrType._uuid.str64()

        else:
            attrs['cardinality'] = attrCard

        if flags:
            attrs['flags'] = str(flags)

        generator.startElement(tag, attrs)

        if attrCard == 'single':
            if isinstance(value, ItemPackage.Item.Item):
                raise TypeError, "item %s cannot be stored as a literal value" %(value.itsPath)

            if value is ItemPackage.Item.Item.Nil:
                raise ValueError, 'Cannot persist Item.Nil'

            if attrType is not None:
                if not attrType.recognizes(value):
                    raise TypeError, "value '%s' of type %s is not recognized by type %s" %(value, type(value), attrType.itsPath)
                else:
                    attrType.typeXML(value, generator, withSchema)
            else:
                generator.characters(cls.makeString(repository, value))
            
        elif attrCard == 'list':
            for val in value._itervalues():
                cls.xmlValue(repository,
                             None, val, 'value', attrType, 'single',
                             None, 0, generator, withSchema)

        elif attrCard == 'dict':
            for key, val in value._iteritems():
                cls.xmlValue(repository,
                             key, val, 'value', attrType, 'single',
                             None, 0, generator, withSchema)
        else:
            raise ValueError, attrCard

        generator.endElement(tag)

    typeName = classmethod(typeName)
    typeHandler = classmethod(typeHandler)
    makeString = classmethod(makeString)
    makeValue = classmethod(makeValue)
    xmlValue = classmethod(xmlValue)

    typeDispatch = {
        'str': str,
        'unicode': unicode,
        'uuid': UUID,
        'path': Path,
        'ref': lambda(data): SingleRef(UUID(data)),
        'bool': lambda(data): data != 'False',
        'int': int,
        'long': long,
        'float': float,
        'complex': complex,
        'class': lambda(data): ClassLoader.loadClass(data),
        'none': lambda(data): None,
    }


class ItemsHandler(ContentHandler):

    def __init__(self, repository, parent, afterLoadHooks):

        ContentHandler.__init__(self)

        self.repository = repository
        self.parent = parent
        self.afterLoadHooks = afterLoadHooks

    def startDocument(self):

        self.itemHandler = None
        self.items = []
        
    def startElement(self, tag, attrs):

        if self.exception is None:
            if tag == 'item':
                self.itemHandler = ItemHandler(self.repository, self.parent,
                                               self.afterLoadHooks)
                self.itemHandler.startDocument()

            if self.itemHandler is not None:
                try:
                    self.itemHandler.startElement(tag, attrs)
                except Exception:
                    self.saveException()
                    return

    def characters(self, data):

        if self.exception is None and self.itemHandler is not None:
            self.itemHandler.characters(data)

    def endElement(self, tag):

        if self.exception is None:
            if self.itemHandler is not None:
                try:
                    self.itemHandler.endElement(tag)
                except Exception:
                    self.saveException()
                    return
            
            if tag == 'item':
                item = self.itemHandler.item
                self.items.append(self.itemHandler.item)
                self.itemHandler.endDocument()
                self.itemHandler = None
