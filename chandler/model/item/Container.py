
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Item import Item
from model.util.Path import Path
from model.util.UUID import UUID


class Container(Item):
    '''The root class of all item containers.

    A container contains items as children.
    When a container is deleted via Container.delete() all its children
    are deleted first, recursively.
    A Container instance can be used as an iterator over its children.'''

    def __init__(self, name, parent, kind, **kwds):

        super(Container, self).__init__(name, parent, kind, **kwds)

        self._children = {}

    def __iter__(self):

        return self._children.itervalues()
    
    def _addItem(self, item):

        try:
            name = item._name
            current = self._children[name]
        except KeyError:
            pass
        else:
            current.delete()

        self._children[name] = item

        return self._root

    def _removeItem(self, item):

        del self._children[item.getName()]

    def delete(self):
        'Delete this Container and all its children. See also Item.delete().'
        
        for item in self._children.values():
            item.delete()

        super(Container, self).delete()

    def getChild(self, name):
        'Return the child as named or None if not found.'
        
        return self._children.get(name)

    def _setRoot(self, root):

        super(Container, self)._setRoot(root)

        if self.__dict__.has_key('_children'):
            for child in self._children.itervalues():
                child._setRoot(root)

    def find(self, spec, _index=0):
        '''Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the item unless the path is absolute.'''

        if isinstance(spec, Path):
            l = len(spec)

            if _index == l:
                return self

            if _index > l:
                return None

            if _index == 0:
                if spec[0] == '//':
                    return self.getRepository().find(spec)

                elif spec[0] == '/':
                    if self._root is self:
                        return self.find(spec, _index=1)
                    else:
                        return self._root.find(spec, _index=0)

            else:
                child = self._children.get(spec[_index])
                if child is not None:
                    return child.find(spec, _index + 1)

        elif isinstance(spec, UUID):
            return self.getRepository().find(spec)

        elif isinstance(spec, str):
            if spec.find('/') >= 0:
                return self.find(Path(spec))
            elif len(spec) == 36 and spec[8] == '-' or len(spec) == 22:
                return self.find(UUID(spec))

        return None
