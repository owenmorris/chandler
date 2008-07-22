#   Copyright (c) 2003-2008 Open Source Applications Foundation
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

from application import schema
from items import ContentItem
from collections import ContentCollection
from chandlerdb.util.c import Empty

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
    """
    The item that's created in the repository for each Stamp subclass
    you declare.
    """
       
    _collection = schema.One()
    stampClass = schema.One(schema.Class)

    # collection is a property because we can't create a StampCollection
    # at schema init time (due to dependency issues), but delaying its
    # creation (via a callback from StampClass._init_schema_item) is too
    # late, because osaf.pim's installParcel() wants to access this collection.
    # So, we make it a property so that it will be loaded on demand, by the
    # schema init callback, or parcel installation calling Stamp.getCollection.

    @property
    def collection(self):
        if not self.hasLocalAttributeValue('_collection'):
            self._collection = StampCollection(itsView=self.itsView, schemaItem=self)
        return self._collection

class StampClass(schema.AnnotationClass):
    """Metaclass for stamp types"""

    def __init__(cls, name, bases, cdict):
        cls.__initialValues__ = iv = []
        for name,ob in cdict.items():
            if isinstance(ob,schema.Descriptor) and hasattr(ob,'initialValue'):
                iv.append((name, ob.initialValue))
                del ob.initialValue

        super(StampClass,cls).__init__(name, bases, cdict)

        cls.__all_ivs__, cls.__setup__ = schema._initializers_for(cls)

    def _create_schema_item(cls, view):
        return StampItem(None, view['Schema'], stampClass=cls)
        
        
    def _init_schema_item(cls,item,view):
        callback = super(StampClass, cls)._init_schema_item(item, view)
        if cls.__use_collection__:
            def newCallback():
                if callback is not None: callback()
                # Make sure we create the collection!
                item.collection
            return newCallback
        return callback

class Stamp(schema.Annotation):

    __metaclass__ = StampClass

     # should be Note? or even Item? Or leave it up to subclasses?
    schema.kindInfo(annotates=ContentItem)
    
    stampCollections = schema.Sequence(defaultValue=Empty)

    __use_collection__ = False
    
    @classmethod
    def getCollection(cls, repoView):
        if cls.__use_collection__:
            return schema.itemFor(cls, repoView).collection
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

    def get_stamp_types(self, allowInherit=True):
        stampCollections = self.stampCollections
        if (allowInherit and
            stampCollections is not Empty and
            stampCollections.isDeferred()):
            try:
                stampCollections = getattr(self.itsItem.inheritFrom,
                                           Stamp.stampCollections.name)
            except AttributeError:
                stampCollections = Empty

        return frozenset(coll.schemaItem.stampClass
                             for coll in stampCollections)

    def set_stamp_types(self, values):
        old = self.get_stamp_types(allowInherit=False)
        
        for cls in old:
            if not cls in values:
                cls(self).remove()

        for cls in values:
            if not cls in old:
                cls(self).add()

    stamp_types = schema.Calculated(schema.Set, basedOn=stampCollections,
                                    fset=set_stamp_types, fget=get_stamp_types)

    @property
    def stamps(self):
        for t in self.stamp_types:
            yield t(self)
            
    def add(self):
        item = self.itsItem
        stampClass = self.__class__
        stampCollection = schema.itemFor(stampClass, item.itsView).collection

        if stampCollection in self.stampCollections:
            raise StampAlreadyPresentError, \
                "Item %r already has stamp %r" % (item, self)
        
        if (not self.itsItem.isProxy and
            not self.itsItem.hasLocalAttributeValue(Stamp.stampCollections.name)):
            self.stampCollections = []
        self.stampCollections.add(stampCollection)
        
        if not item.isProxy:
        
            for attr, callback in stampClass.__all_ivs__:
                if not hasattr(self, attr):
                    setattr(self, attr, callback(self))
            
            for cls in stampClass.__mro__:
                # Initialize values for annotation attributes
                for attr, val in getattr(cls,'__initialValues__',()):
                    if not hasattr(self, attr):
                        setattr(self, attr, val)

    def remove(self):
        item = self.itsItem
        stampClass = self.__class__
        stampCollection = schema.itemFor(stampClass, item.itsView).collection

        if not stampCollection in self.stampCollections:
            raise StampNotPresentError, \
                  "Item %r doesn't have stamp %r" % (item, self)

        addBack = None
        
        if not item.isProxy:
            
            # This is gross, and was in the old stamping code.
            # Some items, like Mail messages, end up in the
            # all collection by virtue of their stamp. So, we
            # explicitly re-add the item to all after unstamping
            # if necessary.
            all = schema.ns("osaf.pim", item.itsView).allCollection
            if item in all:
                addBack = all
    
            if not self.itsItem.hasLocalAttributeValue(Stamp.stampCollections.name):
                self.stampCollections = list(self.stampCollections)

        self.stampCollections.remove(stampCollection)

        if addBack is not None and not item in addBack:
            addBack.add(item)

    def isAttributeModifiable(self, attribute):
        # A default implementation which sub-classes can override if necessary
        # ContentItem's isAttributeModifiable( ) calls this method on all of
        # an item's stamps
        return True


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
        
    @schema.observer(stampCollections)
    def onStampTypesChanged(self, op, attr):
        self.itsItem.updateDisplayDate(op, attr)
        self.itsItem.updateDisplayWho(op, attr)

class StampCollection(ContentCollection):
    """
    A C{ContentCollection} to store the collection of items that have a
    particular C{Stamp}. Used in favor of C{ListCollection} because there
    is code (in recurrence, for example) that manipulates
    C{ContentItem.collections}, the inverse of C{ListCollection.inclusions}
    in a way that breaks stamp collection membership.
    """
    __metaclass__ = schema.CollectionClass
    __collection__ = 'stampedItems'
    
    schemaItem = schema.One(StampItem, inverse=StampItem._collection)
    stampedItems = schema.Sequence(Stamp, inverse=Stamp.stampCollections,
                                   initialValue=[])

    @property
    def stamp_type(self):
        return self.schemaItem.stampClass
    
    def __repr__(self):
        return "<%s(%s): %s>" % (type(self).__name__, self.schemaItem.stampClass,
                                 self.itsUUID.str16())

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

