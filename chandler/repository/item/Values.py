
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.PersistentCollections import PersistentCollection


class Values(dict):

    def __init__(self, item):

        super(Values, self).__init__()
        self._setItem(item)

    def _getItem(self):

        return self._item

    def _setItem(self, item):

        self._item = item

    def _copy(self, item):

        values = type(self)(item)
        for name, value in self.iteritems():
            if isinstance(value, PersistentCollection):
                value = value._copy(item, name, value._companion)
            elif isinstance(value, ItemValue):
                value = value._copy(item, name)

            values[name] = value

        return values

    def __setitem__(self, key, value):

        if self._getFlags(key) & Values.READONLY:
            raise AttributeError, 'Value for %s on %s is read-only' %(key, self._item.itsPath)

        if self._item is not None:
            self._item.setDirty(attribute=key)

        return super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._getFlags(key) & Values.READONLY:
            raise AttributeError, 'Value for %s on %s is read-only' %(key, self._item.itsPath)

        if self._item is not None:
            self._item.setDirty(attribute=key)

        return super(Values, self).__delitem__(key)

    def _unload(self):

        self.clear()

    def _setFlag(self, key, flag):

        if '_flags' in self.__dict__:
            self._flags[key] = self._flags.get(key, 0) | flag
        else:
            self._flags = { key: flag }

    def _clearFlag(self, key, flag):

        if '_flags' in self.__dict__:
            if key in self._flags:
                self._flags[key] &= ~flag

    def _setFlags(self, key, flags):

        if '_flags' in self.__dict__:
            self._flags[key] = flags
        else:
            self._flags = { key: flags }

    def _getFlags(self, key, default=0):

        if '_flags' in self.__dict__:
            return self._flags.get(key, default)

        return default

    def _xmlValues(self, generator, withSchema, version, mode):

        from repository.item.ItemHandler import ItemHandler
        
        item = self._item
        kind = item._kind
        repository = item.itsView

        for key, value in self.iteritems():
            if kind is not None:
                attribute = kind.getAttribute(key)
            else:
                attribute = None
                
            if attribute is not None:
                persist = attribute.getAspect('persist', default=True)
            else:
                persist = True

            if persist:
                if attribute is not None:
                    attrType = attribute.getAspect('type')
                    attrCard = attribute.getAspect('cardinality',
                                                   default='single')
                    attrId = attribute.itsUUID
                else:
                    attrType = None
                    attrCard = 'single'
                    attrId = None

                try:
                    ItemHandler.xmlValue(repository, key, value, 'attribute',
                                         attrType, attrCard, attrId,
                                         self._getFlags(key), generator,
                                         withSchema)
                except Exception, e:
                    e.args = ("while saving attribute '%s' of item %s, %s" %(key, item.itsPath, e.args[0]),)
                    raise
            

    READONLY = 0x0001          # value is read-only
        

class References(Values):

    def _setItem(self, item):

        for value in self.itervalues():
            value._setItem(item)

        self._item = item

    def _copy(self, item):

        references = type(self)(item)
        for name, value in self.iteritems():
            copyPolicy = item.getAttributeAspect(name, 'copyPolicy')
            if copyPolicy == 'copy':
                references[name] = value._copy(item, name)
                
        return references

    def __setitem__(self, key, value, *args):

        super(References, self).__setitem__(key, value)

    def _unload(self):

        for value in self.itervalues():
            value._unload(self._item)

    def _xmlValues(self, generator, withSchema, version, mode):

        item = self._item

        for key, value in self.iteritems():
            if item.getAttributeAspect(key, 'persist', default=True):
                value._xmlValue(key, item, generator, withSchema, version,
                                self._getFlags(key), mode)


class ItemValue(object):
    'A superclass for values that are owned by an item.'
    
    def __init__(self):

        self._item = None
        self._attribute = None
        self._dirty = False
        self._readOnly = False

    def _setItem(self, item, attribute):

        if self._item is not None and self._item is not item:
            raise ValueError, 'item attribute value %s is already owned by another item %s' %(self, self._item)
        
        self._item = item
        if self._dirty:
            item.setDirty()

        self._attribute = attribute

    def _setReadOnly(self, readOnly=True):

        self._readOnly = readOnly
        
    def _getItem(self):

        return self._item

    def _getAttribute(self):

        return self._attribute

    def _isReadOnly(self):

        return self._readOnly and self._item is not None

    def _setDirty(self):

        if self._isReadOnly():
            raise AttributeError, 'Value for %s on %s is read-only' %(self._attribute, self._item.itsPath)

        if not self._dirty:
            self._dirty = True
            item = self._item
            if item is not None:
                item.setDirty(attribute=self._attribute, dirty=item.VDIRTY)

    def _copy(self, item, attribute):

        raise NotImplementedError, 'ItemValue._copy is abstract'
