
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.uuid import _hash, _combine
from chandlerdb.item.ItemError import SchemaError
from repository.item.Item import Item
from repository.schema.Kind import Kind
from repository.schema.TypeHandler import TypeHandler


class Attribute(Item):
    
    def __init__(self, name, parent, kind):

        super(Attribute, self).__init__(name, parent, kind)
        self._status |= Item.SCHEMA | Item.PINNED

    def _fillItem(self, name, parent, kind, **kwds):

        super(Attribute, self)._fillItem(name, parent, kind, **kwds)
        
        refList = self._refList('inheritingKinds', 'inheritedAttributes', False)
        self._references['inheritingKinds'] = refList

        self._status |= Item.SCHEMA | Item.PINNED

    def hasAspect(self, name):

        return self.hasLocalAttributeValue(name)

    def getAspect(self, name, **kwds):

        if name in self._values:
            return self._values[name]
        elif name in self._references:
            return self._references._getRef(name)

        if 'superAttribute' in self._references:
            return self.superAttribute.getAspect(name, **kwds)

        if 'default' in kwds:
            return kwds['default']

        if self._kind is not None:
            aspectAttr = self._kind.getAttribute(name, False, self)
            return aspectAttr.getAttributeValue('defaultValue', default=None)
        
        return None

    def _walk(self, path, callable, **kwds):

        l = len(path)
        
        if path[0] == '//':
            if l == 1:
                return self
            roots = self.getAttributeValue('roots', default=Item.Nil,
                                           _attrDict=self._values)
            if roots is Item.Nil:
                root = None
            else:
                root = roots.get(path[1], None)
            index = 1

        elif path[0] == '/':
            root = self.getAttributeValue('root', default=None,
                                          _attrDict=self._values)
            index = 0

        root = callable(self, path[index], root, **kwds)

        if root is not None:
            index += 1
            if index == l:
                return root
            return root.walk(path, callable, index, **kwds)

        return None

    def _hashItem(self):

        hash = 0
        view = self.itsView

        item = self.getAttributeValue('superAttribute', self._references,
                                      default=None)
        if item is not None:
            hash = _combine(hash, item.hashItem())

        for aspect in Attribute.valueAspects:
            value = self.getAttributeValue(aspect, self._values, 
                                           default=Item.Nil)
                                           
            if value is not Item.Nil:
                hash = _combine(hash, _hash(aspect))
                type = self.getAttributeAspect(aspect, 'type', default=None)
                if type is not None:
                    hash = _combine(hash, type.hashValue(value))
                else:
                    hash = _combine(hash, TypeHandler.hashValue(view, value))

        item = self.getAttributeValue('type', self._references,
                                      default=None)
        if item is not None:
            if isinstance(item, Kind):
                hash = _combine(hash, _hash(str(item.itsPath)))
            else:
                hash = _combine(hash, item.hashItem())

        return hash

    def hashItem(self):

        if 'schemaHash' in self._values:
            return self.schemaHash

        self.schemaHash = hash = self._hashItem()
        return hash

    def onValueChanged(self, name):

        if ('schemaHash' in self._values and
            (name in Attribute.valueAspects or
             name in Attribute.refAspects)):
            del self.schemaHash
            if 'kinds' in self._references:
                for kind in self.kinds:
                    kind.onValueChanged('attributeHash')

    def findMatch(self, view, matches=None):

        if matches is not None:
            match = matches.get(self)
        else:
            match = None
            
        if match is None:
            match = view.find(self._uuid)
            if match is None:
                match = view.find(self.itsPath)
                if not (match is None or matches is None):
                    if not (self is match or
                            self.hashItem() == match.hashItem()):
                        raise SchemaError, ("Attribute matches are incompatible: %s %s", self.itsPath, match.itsPath)
                    matches[self] = match

        return match

    valueAspects = ('required', 'persist', 'cardinality',
                    'defaultValue', 'initialValue',
                    'inheritFrom', 'redirectTo', 'otherName', 'companion',
                    'deletePolicy', 'copyPolicy', 'countPolicy')

    refAspects = ('type', 'superAttribute')
