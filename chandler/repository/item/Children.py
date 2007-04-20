#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


from weakref import ref

from chandlerdb.item.c import CItem, isitem
from chandlerdb.util.c import CLink, Nil
from repository.util.LinkedMap import LinkedMap


class Children(LinkedMap):

    def __init__(self, view, item, lmflags):

        super(Children, self).__init__(view, lmflags)

        self._owner = Nil
        self._setItem(item)

    def _setItem(self, item):

        if self._owner is not Nil:
            assert item.itsUUID == self._owner.itsUUID

            for link in self._itervalues():
                link.value._parent = item

        if isitem(item):
            item._status |= CItem.CONTAINER
            self._owner = item.itsRef
            self._view = item.itsView
        elif item is None:
            self._owner = Nil

        self._owner = ref(item)

    def linkChanged(self, link, key, oldAlias=Nil):

        self._owner().setDirty(CItem.CDIRTY)

    def _append(self, child):

        key = child.itsUUID
        link = self._get(key, True, True)
        if link is None:
            self[key] = CLink(self, child.itsRef, None, None,
                              child.itsName, None)
        else:
            link.value = child.itsRef
            if link.alias != child.itsName:
                self.setAlias(key, child.itsName)
    
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
