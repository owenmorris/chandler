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


from chandlerdb.item.c import isitem

#
# __doc__ strings need to be explicitely set in order not to be removed by -OO
#


class ItemError(Exception):

    def getItem(self):
        return self.args[0]

    def str(self, arg):
        if isitem(arg):
            return arg._repr_()
        else:
            return str(arg)


class StaleItemError(ValueError, ItemError):
    __doc__ = "Item is stale"

    def __str__(self):
        return self.getItem()._repr_()


class DirtyItemError(ValueError, ItemError):
    __doc__ = "Item is dirty, cannot be unloaded"

    def __str__(self):
        return self.getItem()._repr_()

    
class InvalidChildError(ValueError, ItemError):
    __doc__ = '%s not a child of %s'

    def __str__(self):
        return self.__doc__ %(self.args[1].itsPath, self.getItem().itsPath)


class ChildNameError(ValueError, ItemError):
    __doc__ = "%s already has a child named '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath, self.args[1])


class AnonymousRootError(ValueError, ItemError):
    __doc__ = 'repository root %s may not be anonymous'
    
    def __str__(self):
        return self.__doc__ %(self.getItem()._repr_())


class OwnedValueError(ValueError, ItemError):
    __doc__ = "Value %s is already owned by item %s on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.args[2],
                              self.getItem()._repr_(),
                              self.args[1])


class RecursiveDeleteError(ValueError, ItemError):
    __doc__ = 'Item %s has children, delete must be recursive'

    def __str__(self):
        return self.__doc__ %(self.getItem()._repr_())


class NoSuchItemInCollectionError(ValueError, ItemError):
    __doc__ = "Item %s: no item %s in collection on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.str(self.args[2]),
                              self.getAttribute())


class NoSuchAttributeError(AttributeError, ItemError):
    __doc__ = "Kind %s has no definition for attribute '%s'"
    
    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath, self.args[1])


class IndirectAttributeError(AttributeError, ItemError):
    __doc__ = "Indirect values on item %s, attribute '%s' via '%s' are not supported"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.args[1],
                              self.args[2])


class NoValueForAttributeError(AttributeError, ItemError):
    __doc__ = "%s (Kind: %s) has no value for '%s'"

    def getAttribute(self):
        return self.args[1]
    
    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getItem()._kind,
                              self.getAttribute())


class NoLocalValueForAttributeError(NoValueForAttributeError):
    __doc__ = "%s (Kind: %s) has no local value for '%s'"
    
    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getItem()._kind,
                              self.getAttribute())


class ReadOnlyAttributeError(AttributeError, ItemError):
    __doc__ = 'Item %s: value for %s is read-only'

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath, self.args[1])


class StaleItemAttributeError(AttributeError, ItemError):
    __doc__ = "Stale Item '%s' has no attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem()._repr_(), self.args[1])


class KindlessItemError(TypeError, ItemError):
    __doc__ = "Item is kindless"

    def __str__(self):
        return self.getItem()._repr_()


class CardinalityError(TypeError, ItemError):
    __doc__ = "Item %s (kind: %s), attribute '%s' is not %s"

    def __str__(self):
        return self.__doc__ %(self.args[1],
                              self.getItem().itsPath,
                              self.getItem()._kind,
                              self.args[2])


class BadRefError(ValueError, ItemError):
    __doc__ = "Item %s, attribute '%s': ref is: %s, but should be: %s"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.args[1],
                              self.str(self.args[2]),
                              self.str(self.args[3]))


class DanglingRefError(BadRefError):
    __doc__ = "Item %s, attribute '%s': referred item %s not found"

    def __str__(self):
        return self.__doc__ %(self.getItem()._repr_(),
                              self.args[1],
                              self.str(self.args[2]))


class ViewMismatchError(BadRefError):
    __doc__ = "Error establishing bidirectional ref, item views don't match: %s is in %s but %s is in %s"

    def __str__(self):
        return self.__doc__ %(self.args[0]._repr_(), self.args[0].itsView,
                              self.args[1]._repr_(), self.args[1].itsView)


class IndexError(ItemError):

    def getCollection(self):
        return self.args[1]

    def getIndexName(self):
        return self.args[2]
    

class NoSuchIndexError(KeyError, IndexError):
    __doc__ = "Item %s: no index named '%s' on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getIndexName(),
                              self.getCollection())


class IndexAlreadyExists(KeyError, IndexError):
    __doc__ = "Item %s: an index named '%s' already exists on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getIndexName(),
                              self.getCollection())


class SchemaError(TypeError, ItemError):

    def __str__(self):
        return self.args[0] % self.args[1:]
