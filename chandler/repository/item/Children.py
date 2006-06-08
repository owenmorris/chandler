
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from chandlerdb.item.c import CItem, Nil, isitem
from chandlerdb.util.c import CLink
from repository.util.LinkedMap import LinkedMap


class Children(LinkedMap):

    def __init__(self, item, lmflags):

        super(Children, self).__init__(lmflags)

        self._item = None
        self._setItem(item)

    def _setItem(self, item):

        if self._item is not None:
            assert item.itsUUID == self._item.itsUUID

            for link in self._itervalues():
                link.value._parent = item

        if isitem(item):
            item._status |= CItem.CONTAINER
            
        self._item = item

    def _refCount(self):

        return len(self._dict) + 1
        
    def linkChanged(self, link, key, oldAlias=Nil):

        self._item.setDirty(CItem.CDIRTY)

    def _unloadChild(self, child):

        raise NotImplementedError, "%s._unloadChild" %(type(self))

    def _append(self, child):

        self[child.itsUUID] = CLink(self, child, None, None, child.itsName)
    
    def __repr__(self):

        buffer = ['{(currenly loaded) ']

        first = True
        for link in self._itervalues():
            if not first:
                buffer.append(', ')
            else:
                first = False
            buffer.append(link.value._repr_())
        buffer.append('}')

        return ''.join(buffer)

    def _saveValues(self, version):
        raise NotImplementedError, "%s._saveValues" %(type(self))
