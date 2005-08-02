
__revision__  = "$Revision: 6275 $"
__date__      = "$Date: 2005-07-29 08:19:45 -0700 (Fri, 29 Jul 2005) $"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.item.ItemError import OwnedValueError


class ItemValue(object):
    'A superclass for values that are owned by an item.'
    
    def __init__(self, item=None, attribute=None):

        self._item = item
        self._attribute = attribute
        self._dirty = False
        self._readOnly = False

    def _setReadOnly(self, readOnly=True):

        self._readOnly = readOnly
        
    def _setOwner(self, item, attribute):

        if item is not None:
            if self._item is not None and self._item is not item:
                raise ValueError, (self._item, self._attribute, self)
        
        oldItem = self._item
        oldAttribute = self._attribute

        self._item = item
        self._attribute = attribute

        return oldItem, oldAttribute

    def _getOwner(self):

        return (self._item, self._attribute)

    def _getItem(self):

        return self._item

    def _getAttribute(self):

        return self._attribute

    def _refCount(self):

        return 1

    def _isReadOnly(self):

        return self._readOnly and self._item is not None

    def _setDirty(self, noMonitors=False):

        if self._isReadOnly():
            raise ReadOnlyAttributeError, (self._item, self._attribute)

        self._dirty = True
        item = self._item
        if item is not None:
            item.setDirty(item.VDIRTY, self._attribute,
                          item._values, noMonitors)

    def _copy(self, item, attribute, copyPolicy, copyFn=None):

        raise NotImplementedError, '%s._copy' %(type(self))

    def _check(self, logger, item, attribute):

        if not (item is self._item and attribute == self._attribute):
            logger.error('Value %s of type %s in attribute %s on %s is owned by  attribute %s on %s', value, type(value), name, item._repr_(), self._attribute, self._item)
            return False

        return True
