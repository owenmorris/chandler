
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import repository.item.Item

from repository.item.PersistentCollections import PersistentCollection
from repository.item.PersistentCollections import SingleRef
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict
from repository.item.ItemRef import Values, References, RefArgs

from repository.util.UUID import UUID
from repository.util.Path import Path


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
            self.collections.append(PersistentDict(None, None))
        elif cardinality == 'list' or typeName == 'list':
            self.collections.append(PersistentList(None, None))
        else:
            self.setupTypeDelegate(attrs)

    def refStart(self, itemHandler, attrs):

        if self.tags[-1] == 'item':
            name = attrs['name']
            attribute = self.getAttribute(name)
            self.attributes.append(attribute)

            cardinality = self.getCardinality(attribute, attrs)

            if cardinality != 'single':
                if cardinality == 'dict':
                    print "Warning, 'dict' cardinality for reference attribute %s on %s is deprecated, use 'list' instead" %(name, self.name)

                otherName = self.getOtherName(name, attribute, attrs)
                refDict = self.repository.createRefDict(None, name,
                                                        otherName, True)
                
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
                cls = repository.item.Item.Item
            else:
                cls = self.kind.getItemClass()

        self.item = item = cls.__new__(cls)
        item._fillItem(self.name, self.parent, self.kind, uuid = self.uuid,
                       values = self.values, references = self.references,
                       previous = self.previous, next = self.next,
                       afterLoadHooks = self.afterLoadHooks,
                       version = self.version)

        if self.first or self.last:
            item._children = repository.item.Item.Children(item)
            item._children._firstKey = self.first
            item._children._lastKey = self.last

        self.repository._registerItem(item)

        for attribute, value in self.values.iteritems():
            if isinstance(value, PersistentCollection):
                companion = item.getAttributeAspect(attribute, 'companion',
                                                    default=None)
                value._setItem(item, companion)

        for refArgs in self.refs:
            refArgs.attach(item, self.repository)

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

        self.cls = repository.item.Item.Item.loadClass(self.data,
                                                       attrs['module'])

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

    def aliasEnd(self, itemHandler, attrs):

        refDict = self.collections[-1]
        if refDict._aliases is None:
            refDict._aliases = {}

        refDict._aliases[attrs['name']] = UUID(self.data)

    def dbEnd(self, itemHandler, attrs):
            
        if not self.collections:
            raise ValueError, self.tagAttrs[-1]['name']

        refDict = self.collections[-1]
        refDict._prepareKey(self.uuid, UUID(self.data))

    def valueStart(self, itemHandler, attrs):

        typeName = attrs.get('type')
        if typeName == 'dict':
            self.collections.append(PersistentDict(None, None))
        elif typeName == 'list':
            self.collections.append(PersistentList(None, None))
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
                cardinality = attribute.getAspect('cardinality',
                                                  default='single')

        return cardinality

    def getTypeName(self, attribute, attrs):

        attrType = attrs.get('type')

        if attrType is None and attribute is not None:
            attrType = attribute.getAspect('type', default=None)
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
            otherName = attribute.getAspect('otherName')

        if otherName is None:
            raise TypeError, 'Undefined other endpoint for %s' %(name)

        return otherName

    def getAttribute(self, name):

        if self.withSchema is False and self.kind is not None:
            return self.kind.getAttribute(name)
        else:
            return None

    def setupTypeDelegate(self, attrs):

        if attrs.has_key('typeid'):
            attrType = self.repository.find(UUID(attrs['typeid']))
            if attrType is None:
                raise TypeError, "Alias used before being defined"
            self.delegates.append(attrType)
        
        elif self.attributes[-1]:
            attrType = self.attributes[-1].getAspect('type')
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

        try:
            return ItemHandler.typeDispatch[typeName](data)
        except KeyError:
            raise ValueError, "Unknown type: %s" %(typeName)

    def typeName(cls, value):

        typeHandler = cls.typeHandlers.get(type(value))

        if typeHandler is not None:
            return typeHandler.handlerName()
        elif isinstance(value, UUID):
            return 'uuid'
        elif isinstance(value, Path):
            return 'path'
        elif isinstance(value, SingleRef):
            return 'ref'
        elif isinstance(value, PersistentList):
            return 'list'
        elif isinstance(value, PersistentDict):
            return 'dict'
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
            if attrType is not None and attrType.isAlias():
                valueType = attrType.type(value)
                if valueType:
                    if withSchema:
                        attrs['type'] = valueType.handlerName()
                    else:
                        attrs['typeid'] = valueType.getUUID().str64()
                else:
                    attrs['type'] = cls.typeName(value)
            elif not isinstance(value, str) and not isinstance(value, unicode):
                if attrType is None:
                    attrs['type'] = cls.typeName(value)
                elif withSchema:
                    attrs['type'] = attrType.handlerName()
        else:
            attrs['cardinality'] = attrCard

        generator.startElement(tag, attrs)

        if withSchema or attrType is None or attrCard != 'single':
            if isinstance(value, dict):
                if isinstance(value, PersistentDict):
                    for key, val in value._iteritems():
                        cls.xmlValue(key, val, 'value', attrType, 'single',
                                     generator, withSchema)
                else:
                    raise TypeError, 'dict is not persistent'
            elif isinstance(value, list):
                if isinstance(value, PersistentList):
                    for val in value._itervalues():
                        cls.xmlValue(None, val, 'value', attrType, 'single',
                                     generator, withSchema)
                else:
                    raise TypeError, 'list is not persistent'
            elif isinstance(value, repository.item.Item.Item):
                raise TypeError, 'Item %s cannot be stored in a collection of literals' %(value.getItemPath())
            elif value is repository.item.Item.Item.Nil:
                raise ValueError, 'Cannot persist Item.Nil'
            else:
                generator.characters(cls.makeString(value))

        else:
            if attrType.recognizes(value):
                attrType.typeXML(value, generator)
            else:
                raise TypeError, 'Value %s of type %s on %s is not recognized by type %s' %(value, type(value), name, attrType.getItemPath())

        generator.endElement(tag)

    typeName = classmethod(typeName)
    makeString = classmethod(makeString)
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
        'class': lambda(data): repository.item.Item.Item.loadClass(str(data)),
        'NoneType': lambda(data): None,
    }


class ItemsHandler(xml.sax.ContentHandler):

    def __init__(self, repository, parent, afterLoadHooks):

        self.repository = repository
        self.parent = parent
        self.afterLoadHooks = afterLoadHooks

    def startDocument(self):

        self.itemHandler = None
        self.items = []
        
    def startElement(self, tag, attrs):

        if tag == 'item':
            self.itemHandler = ItemHandler(self.repository, self.parent,
                                           self.afterLoadHooks)
            self.itemHandler.startDocument()

        if self.itemHandler is not None:
            self.itemHandler.startElement(tag, attrs)

    def characters(self, data):

        if self.itemHandler is not None:
            self.itemHandler.characters(data)

    def endElement(self, tag):

        if self.itemHandler is not None:
            self.itemHandler.endElement(tag)
            
        if tag == 'item':
            self.items.append(self.itemHandler.item)
            self.itemHandler.endDocument()
            self.itemHandler = None
