
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.PersistentCollections import PersistentCollection
from repository.util.SingleRef import SingleRef


class Values(dict):

    def __init__(self, item):

        super(Values, self).__init__()
        self._setItem(item)

    def _getItem(self):

        return self._item

    def _setItem(self, item):

        self._item = item

    def _copy(self, orig, copyPolicy, copyFn):

        item = self._item
        for name, value in orig.iteritems():
            if isinstance(value, PersistentCollection):
                self[name] = value._copy(item, name, value._companion,
                                         copyPolicy, copyFn)

            elif isinstance(value, ItemValue):
                value = value._copy(item, name)
                value._setItem(item, name)
                self[name] = value

            elif isinstance(value, SingleRef):
                policy = (copyPolicy or
                          item.getAttributeAspect(name, 'copyPolicy',
                                                  default='copy'))
                other = item.find(value.itsUUID)
                copyOther = copyFn(item, other, policy)

                if copyOther is not None:
                    self[name] = SingleRef(copyOther.itsUUID)
            else:
                self[name] = value

    def __setitem__(self, key, value):

        if self._getFlags(key) & Values.READONLY:
            raise AttributeError, 'Value for %s on %s is read-only' %(key, self._item.itsPath)

        return super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._getFlags(key) & Values.READONLY:
            raise AttributeError, 'Value for %s on %s is read-only' %(key, self._item.itsPath)

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

    def _isReadOnly(self, key):

        return self._getFlags(key) & Values.READONLY != 0

    def _isTransient(self, key):

        return self._getFlags(key) & Values.TRANSIENT != 0

    def _clearTransient(self, key):

        self._flags[key] &= ~Values.TRANSIENT

    def _addMonitor(self, key, count=1):

        if '_monitors' in self.__dict__:
            self._monitors[key] += count
        else:
            self._monitors = { key: count }

    def _hasMonitors(self, key):

        return '_monitors' in self.__dict__ and key in self._monitors
        #return True

    def _removeMonitor(self, key):

        monitors = self._getMonitors(key)

        if monitors:
            self._monitors[key] = monitors - 1
        else:
            raise AttributeError, 'no monitors on attribute %s' %(key)

    def _getMonitors(self, key):

        try:
            return self._monitors[key]
        except AttributeError:
            return 0
        except KeyError:
            return 0

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
                flags = self._getFlags(key)
                persist = flags & self.TRANSIENT == 0

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

                monitors = self._getMonitors(key)
                attrs = {}
                if flags:
                    attrs['flags'] = str(flags)
                if monitors:
                    attrs['monitors'] = str(monitors)

                try:
                    ItemHandler.xmlValue(repository, key, value, 'attribute',
                                         attrType, attrCard, attrId, attrs,
                                         generator, withSchema)
                except Exception, e:
                    e.args = ("while saving attribute '%s' of item %s, %s" %(key, item.itsPath, e.args[0]),)
                    raise


    READONLY = 0x0001          # value is read-only
    TRANSIENT = 0x0002         # value is transient
    

class References(Values):

    def clear(self):

        item = self._item
        for name in self.keys():
            item.removeAttributeValue(name, _attrDict=item._references)

    def _setItem(self, item):

        for value in self.itervalues():
            value._setItem(item)

        self._item = item

    def _copy(self, orig, copyPolicy, copyFn):

        item = self._item
        for name, value in orig.iteritems():
            policy = copyPolicy or item.getAttributeAspect(name, 'copyPolicy')
            value._copy(self, orig._item, item, name, policy, copyFn)

    def _unload(self):

        for value in self.itervalues():
            value._unload(self._item)

    def _xmlValues(self, generator, withSchema, version, mode):

        item = self._item

        for key, value in self.iteritems():
            if item.getAttributeAspect(key, 'persist', default=True):
                flags = self._getFlags(key)
                monitors = self._getMonitors(key)
                attrs = {}
                if flags:
                    attrs['flags'] = str(flags)
                if monitors:
                    attrs['monitors'] = str(monitors)
                value._xmlValue(key, item, generator, withSchema, version,
                                attrs, mode)

    def _isRefDict(self):

        return False


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

        self._dirty = True
        item = self._item
        if item is not None:
            item.setDirty(item.VDIRTY, self._attribute, item._values)

    def _copy(self, item, attribute):

        raise NotImplementedError, '%s._copy' %(type(self))
