from application import schema
from chandlerdb.item.ItemError import NoLocalValueForAttributeError
from items import ContentItem
from collections import ListCollection


__parcel__ = 'osaf.pim'

"""
STAMPING SUPPORT CLASSES
"""
class StampAlreadyPresentError(ValueError):
    """
    Stamping could not be performed because the stamp is already present,
    and no new class would be added.
    """

class StampNotPresentError(ValueError):
    """
    A Stamp could not be removed because the stamp is not already
    present in the item to be unstamped.
    """

class StampItem(schema.AnnotationItem):
    """The item that's created in the repository for each Stamp subclass
       you declare."""
       
    _stampedItems = schema.One(ListCollection)

    # stampedItems is a property because we can't create a ListCollection
    # at schema init time (due to dependency issues), but delaying its
    # creation (via a callback from StampClass._init_schema_item) is too
    # late, because osaf.pim's installParcel() wants to access this collection.
    # So, we make it a property so that it will be loaded on demand, by the
    # schema init callback, or parcel installation calling Stamp.getCollection.

    @property
    def stampedItems(self):
        if not self.hasLocalAttributeValue('_stampedItems'):
            self._stampedItems = ListCollection(itsView=self.itsView)
        return self._stampedItems

class StampClass(schema.AnnotationClass):
    """Metaclass for stamp types"""
    def _create_schema_item(cls, view):
        return StampItem(None, view['Schema'])
        
        
    def _init_schema_item(cls,item,view):
        callback = super(StampClass, cls)._init_schema_item(item, view)
        if cls.__use_collection__:
            def newCallback():
                if callback is not None: callback()
                # Make sure we create the collection!
                item.stampedItems
            return newCallback
        return callback

class Stamp(schema.Annotation):

    __metaclass__ = StampClass

     # should be Note? or even Item? Or leave it up to subclasses?
    schema.kindInfo(annotates=ContentItem)
    
    stamp_types = schema.Many(schema.Class, defaultValue=None)

    __use_collection__ = False
    
    @classmethod
    def getCollection(cls, repoView):
        if cls.__use_collection__:
            return schema.itemFor(cls, repoView).stampedItems
        else:
            return None

    @classmethod
    def iterItems(cls, repoView):
        collection = cls.getCollection(repoView)
        if collection is not None:
            for item in collection: yield item
        
    @property
    def collection(self): # @@@ [grant] is this used anywhere
        return type(self).getCollection(self.itsItem.itsView)

    @property
    def stamps(self):
        types = self.stamp_types
        try:
            types = iter(types)
        except TypeError:
            pass
        else:
            for t in types:
                yield t(self)
            
    def add(self):
        new_stamp_types = set([self.__class__])
        if self.stamp_types is not None:
            if self.__class__ in self.stamp_types:
                raise StampAlreadyPresentError, \
                    "Item %r already has stamp %r" % (self.itsItem, self)
                    
            new_stamp_types = new_stamp_types.union(self.stamp_types)
        
        stamped = self.collection
        
        if stamped is not None:
            stamped.add(self.itsItem)

        self.stamp_types = new_stamp_types

    def remove(self):
        new_stamp_types = set(self.stamp_types)
        try:
            new_stamp_types.remove(self.__class__)
        except KeyError:
            raise StampNotPresentError, \
                  "Item %r doesn't have stamp %r" % (self.itsItem, self)
        
        stamped = self.collection
        
        # This is gross, and was in the old stamping code.
        # Some items, like Mail messages, end up in the
        # all collection by virtue of their stamp. So, we
        # explicitly re-add the item to all after unstamping
        # if necessary.
        all = schema.ns("osaf.pim", self.itsItem.itsView).allCollection
        inAllBeforeStamp = self.itsItem in all


        if stamped is not None:
            stamped.remove(self.itsItem)

        self.stamp_types = new_stamp_types
        
        if inAllBeforeStamp and not self.itsItem in all:
            all.add(self.itsItem)


    @classmethod
    def addIndex(cls, view_or_collection, name, type, **keywds):
        try:
            addIndex = view_or_collection.addIndex
        except AttributeError:
            collection = cls.getCollection(view_or_collection)
        else:
            collection = view_or_collection
            
        return super(Stamp, cls).addIndex(collection, name, type, **keywds)
    
    @classmethod
    def update(cls, parcel, itsName, **attrs):
        targetType = cls.targetType()
        newAttrs = {}
        
        for key, value in attrs.iteritems():
            if getattr(targetType, key, None) is None:
                key = getattr(cls, key).name
            newAttrs[key] = value
        item = targetType.update(parcel, itsName, **newAttrs)
        cls(item).add()
        return item

    def hasLocalAttributeValue(self, attrName):
        fullName = getattr(type(self), attrName).name
        return self.itsItem.hasLocalAttributeValue(fullName)
        
    def __eq__(self, other):
        return type(other) == type(self) and self.itsItem == other.itsItem

    @schema.observer(stamp_types)
    def onStampTypesChanged(self, op, attr):
        self.itsItem.updateRelevantDate(op, attr)

def has_stamp(item, stampClass):
    try:
        stamps = Stamp(item).stamp_types or []
    except TypeError: # item isn't a ContentItem
        return False
    else:
        return stampClass in stamps


if __name__ == "__main__":
    import doctest
    doctest.testfile("stamping.txt", optionflags=doctest.ELLIPSIS)

