
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class ItemError(Exception):

    def getItem(self):
        return self.args[0]

    def str(self, arg):
        from repository.item.Item import Item
        if isinstance(arg, Item):
            return arg._repr_()
        else:
            return str(arg)


class StaleItemError(ValueError, ItemError):
    "Item is stale"

    def __str__(self):
        return self.getItem()._repr_()


class DirtyItemError(ValueError, ItemError):
    "Item %s has changed, cannot be unloaded"

    def __str__(self):
        return self.getItem().itsPath

    
class InvalidChildError(ValueError, ItemError):
    '%s not a child of %s'

    def __str__(self):
        return self.__doc__ %(self.args[1].itsPath, self.getItem().itsPath)


class ChildNameError(ValueError, ItemError):
    "%s already has a child named '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath, self.args[1])


class OwnedValueError(ValueError, ItemError):
    "Value %s is already owned by item %s on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.args[2],
                              self.getItem().itsPath,
                              self.args[1])


class RecursiveDeleteError(ValueError, ItemError):
    'Item %s has children, delete must be recursive'

    def __str__(self):
        return self.__doc__ %(self.getItem()._repr_())


class NoSuchItemInCollectionError(ValueError, ItemError):
    "Item %s: no item %s in collection on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.str(self.args[2]),
                              self.getAttribute())


class NoSuchAttributeError(AttributeError, ItemError):
    "Kind %s has no definition for attribute '%s'"
    
    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath, self.args[1])


class IndirectAttributeError(AttributeError, ItemError):
    "Indirect values on item %s, attribute '%s' via '%s' are not supported"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.args[1],
                              self.args[2])


class NoValueForAttributeError(AttributeError, ItemError):
    "%s (Kind: %s) has no value for '%s'"

    def getAttribute(self):
        return self.args[1]
    
    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getItem()._kind,
                              self.getAttribute())


class NoLocalValueForAttributeError(NoValueForAttributeError):
    "%s (Kind: %s) has no local value for '%s'"
    
    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getItem()._kind,
                              self.getAttribute())


class ReadOnlyAttributeError(AttributeError, ItemError):
    'Item %s: value for %s is read-only'

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath, self.args[1])


class KindlessItemError(TypeError, ItemError):
    "Item is kindless"

    def __str__(self):
        return self.getItem()._repr_()


class CardinalityError(TypeError, ItemError):
    "Item %s (kind: %s), attribute '%s' is not %s"

    def __str__(self):
        return self.__doc__ %(self.args[1],
                              self.getItem().itsPath,
                              self.getItem()._kind,
                              self.args[2])


class BadRefError(ValueError, ItemError):
    "Item %s, attribute '%s': ref is: %s, but should be: %s"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.args[1],
                              self.str(self.args[2]),
                              self.str(self.args[3]))


class DanglingRefError(BadRefError):
    "Item %s, attribute '%s': referred item %s not found"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.args[1],
                              self.str(self.args[2]))


class IndexError(ItemError):

    def getCollection(self):
        return self.args[1]

    def getIndexName(self):
        return self.args[2]
    

class NoSuchIndexError(KeyError, IndexError):
    "Item %s: no index named '%s' on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getIndexName(),
                              self.getCollection())


class IndexAlreadyExists(KeyError, IndexError):
    "Item %s: an index named '%s' already exists on attribute '%s'"

    def __str__(self):
        return self.__doc__ %(self.getItem().itsPath,
                              self.getIndexName(),
                              self.getCollection())


class SchemaError(TypeError, ItemError):

    def __str__(self):
        return self.args[0] % self.args[1:]


class NoSuchDefaultKindError(SchemaError):
    'While creating %s, defaultKind %s specified on class %s.%s was not found'

    def __str__(self):
        cls = self.args[1]
        return self.__doc__ %(self.str(self.getItem()),
                              cls._defaultKind, cls.__module__, cls.__name__)

class NoSuchDefaultParentError(SchemaError):
    'While creating %s, defaultParent %s, specified on kind %s, was not found'

    def __str__(self):
        kind = self.args[1]
        return self.__doc__ %(self.str(self.getItem()), 
                              kind._values['defaultParent'],
                              kind.itsPath)
