#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


from chandlerdb.util.c import Nil


class ItemValue(object):
    'A superclass for values that are owned by an item.'
    
    def __init__(self, item=None, attribute=None):

        if item is None:
            self._owner = Nil
        else:
            self._owner = item.itsRef

        self._attribute = attribute
        self._dirty = False
        self._readOnly = False

    def _setReadOnly(self, readOnly=True):

        self._readOnly = readOnly
        
    def _setOwner(self, item, attribute):

        if item is not None:
            if self._owner is not Nil and self._owner is not item.itsRef:
                raise ValueError, (self._owner(), self._attribute, self)
        
        oldItem = self._owner()
        oldAttribute = self._attribute

        if item is None:
            self._owner = Nil
        else:
            self._owner = item.itsRef

        self._attribute = attribute

        return oldItem, oldAttribute

    def _getOwner(self):

        return self._owner(), self._attribute

    def _getItem(self):

        return self._owner()

    def _getAttribute(self):

        return self._attribute

    def _isReadOnly(self):

        return self._readOnly and self._owner is not Nil

    def _setDirty(self, noMonitors=False):

        if self._readOnly:
            raise ReadOnlyAttributeError, self._attribute

        self._dirty = True
        item = self._owner()
        if item is not None:
            item.setDirty(item.VDIRTY, self._attribute,
                          item._values, noMonitors)

    def _copy(self, item, attribute, copyPolicy, copyFn=None):

        raise NotImplementedError, '%s._copy' %(type(self))

    def _clone(self, item, attribute):

        raise NotImplementedError, '%s._clone' %(type(self))

    def _check(self, logger, item, attribute, repair):

        owner = self._owner(True)

        if not (item is owner and attribute == self._attribute):
            logger.error('Value %s of type %s in attribute %s on %s is owned by  attribute %s on %s', self, type(self), attribute, item._repr_(), self._attribute, owner)
            return False

        return True


class Indexable(object):
    'A superclass for values that implement their full text indexing.'    

    def isIndexed(self):
        raise NotImplementedError, '%s.isIndexed' %(type(self))

    def indexValue(self, view, uItem, uAttribute, uValue, version):
        raise NotImplementedError, '%s.indexValue' %(type(self))
