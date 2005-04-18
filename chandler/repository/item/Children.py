
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from chandlerdb.item.item import CItem
from repository.util.LinkedMap import LinkedMap


class Children(LinkedMap):

    def __init__(self, item, new):

        super(Children, self).__init__(new)

        self._item = None
        self._setItem(item)

    def _setItem(self, item):

        if self._item is not None:
            assert item._uuid == self._item._uuid

            for link in self._itervalues():
                link.getValue(self)._parent = item

        if item is not None and item._isItem():
            item._status |= CItem.CONTAINER
            
        self._item = item

    def _refCount(self):

        return super(Children, self).__len__() + 1
        
    def linkChanged(self, link, key):

        self._item.setDirty(CItem.CDIRTY)

    def _unloadChild(self, child):

        raise NotImplementedError, "%s._unloadChild" %(type(self))

    def _append(self, child):

        self.__setitem__(child._uuid, child, None, None, child._name)
    
    def __repr__(self):

        buffer = ['{(currenly loaded) ']

        first = True
        for link in self._itervalues():
            if not first:
                buffer.append(', ')
            else:
                first = False
            buffer.append(link.getValue(self)._repr_())
        buffer.append('}')

        return ''.join(buffer)

    def _saveValues(self, version):
        raise NotImplementedError, "%s._saveValues" %(type(self))
