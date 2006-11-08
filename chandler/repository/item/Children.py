#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from chandlerdb.item.c import CItem, isitem
from chandlerdb.util.c import CLink, Nil
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

        pass

    def _append(self, child):

        self[child.itsUUID] = CLink(self, child, None, None,
                                    child.itsName, None)
    
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
