""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.Parcel import Parcel
import repository.item.Item as Item
import repository.item.Query as Query

import application.Globals as Globals

class ContentModel(Parcel):

    # The parcel knows the UUIDs for the Kinds, once the parcel is loaded
    contentItemKindID = None
    projectKindID = None
    groupKindID = None
    noteKindID = None
    conversationKindID = None

    # The parcel knows the UUID for the parent, once the parcel is loaded
    contentItemParentID = None
    
    def _setUUIDs(self, parent):
        ContentModel.contentItemParentID = parent.itsUUID

        ContentModel.contentItemKindID = self['ContentItem'].itsUUID
        ContentModel.projectKindID = self['Project'].itsUUID
        ContentModel.groupKindID = self['Group'].itsUUID
        ContentModel.noteKindID = self['Note'].itsUUID
        ContentModel.conversationKindID = self['Conversation'].itsUUID

    def onItemLoad(self):
        super(ContentModel, self).onItemLoad()
        repository = self.itsView
        parent = repository.findPath('//userdata/contentitems')
        self._setUUIDs(parent)

    def startupParcel(self):
        super(ContentModel, self).startupParcel()
        repository = self.itsView
        parent = repository.findPath('//userdata/contentitems')
        if not parent:
            itemKind = repository.findPath('//Schema/Core/Item')
            userdata = repository.getRoot('userdata')
            if not userdata:
                userdata = itemKind.newItem('userdata', repository)
            parent = itemKind.newItem('contentitems', userdata)
        self._setUUIDs(parent)

    def getContentItemParent(cls):
        assert cls.contentItemParentID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.contentItemParentID]

    getContentItemParent = classmethod(getContentItemParent)

    def getContentItemKind(cls):
        assert cls.contentItemKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.contentItemKindID]

    getContentItemKind = classmethod(getContentItemKind)

    def getProjectKind(cls):
        assert cls.projectKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.projectKindID]

    getProjectKind = classmethod(getProjectKind)
    
    def getGroupKind(cls):
        assert cls.groupKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.groupKindID]

    getGroupKind = classmethod(getGroupKind)
    
    def getNoteKind(cls):
        assert cls.noteKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.noteKindID]
    
    getNoteKind = classmethod(getNoteKind)
    
    def getConversationKind(cls):
        assert cls.conversationKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.conversationKindID]
    
    getConversationKind = classmethod(getConversationKind)

class StampError(ValueError):
    "Can't stamp Item with the requested Mixin Kind"

class KindList(list):
    def appendUnique(self, item):
        if not item in self:
            self.append(item)

    def properSubsetOf(self, sequence):
        """
        return True if self is a proper subset of sequence
        meaning all items in self are in sequence
        """
        for item in self:
            if not item in sequence:
                return False
        return True

    def allLeafSuperKinds(cls, aKind):
        """
        Return all the leaf node SuperKinds of a Kind in a list.
        """
        def leafNode(kind):
            supers = kind.getAttributeValue('superKinds', default = None)
            return supers is None
        def appendSuperkinds(aKind, supersList):
            supers = aKind.getAttributeValue('superKinds', default = [])
            for kind in supers:
                # all Kinds have Item as their superKind, so the
                # kinds we want are ones just below the leaf. 
                if leafNode(kind):
                    supersList.appendUnique(aKind)
                appendSuperkinds(kind, supersList)
        supersList = KindList()
        appendSuperkinds(aKind, supersList)
        return supersList
    allLeafSuperKinds = classmethod(allLeafSuperKinds)
    
class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getContentItemKind()
        super (ContentItem, self).__init__(name, parent, kind)

    def StampKind(self, operation, mixinKind):
        """
          Stamp ourself into the new kind defined by the
        Mixin Kind passed in mixinKind.
        * Take the current kind, the operation and the Mixin,
        and compute the future Kind.
        * Prepare to become the future Kind, which may mean creating
        one or more Mixins, or saving off Mixins.
        * Stamp ourself to the new Kind.
        * Move the attributes from the Mixin.
        """
        futureKind = self.FindStampedKind(operation, mixinKind)
        dataCarryOver = self.StampPreProcess(futureKind)
        if futureKind is not None:
            self.itsKind = futureKind
        else:
            self.mixinKinds((operation, mixinKind))
        # make sure the respository knows about the item's new Kind
        self.StampPostProcess(futureKind, dataCarryOver)
        Globals.repository.commit()

    def FindStampedKind(self, operation, mixinKind):
        """
           Return the new Kind that results from self being
        stamped with the Mixin Kind specified.
        @param self: an Item that will be stamped
        @type self: C{Item}
        @param operation: 'add' to add the Mixin, 'remove' to remove
        @type operation: C{String}
        @param mixinKind: the Mixin Kind to be added or removed
        @type mixinKind: C{Kind} of the Mixin
        @return: a C{Kind}
        """
        myKind = self.itsKind
        soughtMixins = KindList.allLeafSuperKinds(myKind)
        if operation == 'add':
            assert not mixinKind in soughtMixins, "Trying to stamp with a Mixin Kind already present"
            soughtMixins.append(mixinKind)
            extrasAllowed = 1
        else:
            assert operation == 'remove', "invalid Stamp operation in ContentItem.NewStampedKind: "+operation
            if not mixinKind in soughtMixins:
                return None
            soughtMixins.remove(mixinKind)
            extrasAllowed = -1

        qualified = []
        kindKind = Globals.repository.findPath('//Schema/Core/Kind')
        allKinds = Query.KindQuery().run([kindKind])
        for candidate in allKinds:
            superKinds = KindList.allLeafSuperKinds(candidate)
            extras = len(superKinds) - len(soughtMixins)
            if extras != 0 and (extras - extrasAllowed) != 0:
                continue
            shortList = soughtMixins
            longList = superKinds
            if extras < 0:
                shortList = superKinds
                longList = soughtMixins
            if shortList.properSubsetOf(longList):
                # found a potential match
                if extras == 0:
                    # exact match
                    return candidate
                else:
                    # close match - keep searching for a better match
                    qualified.append(candidate)

        # finished search with no exact matches.  Better have only one candidate.
        if len(qualified) == 1:
            return qualified[0]
        # couldn't find a match, just ReKind with the Mixin Kind
        return None
        

    def AddedRemovedKinds(self, futureKind):
        """
        UNDER CONSTRUCTION
        Return the list of kinds added or removed by the stamping.
        """
        futureKinds = futureKind.getAttributeValue('superKinds', default = [])
        myKind = self.itsKind
        myKinds = myKind.getAttributeValue('superKinds', default = [])
        addedKinds = []
        removedKinds = []
        if len(myKinds) < len(futureKinds):
            longList = futureKinds
            shortList = myKinds
            kinds = addedKinds
        else:
            assert len(myKinds) > len(futureKinds)
            longList = myKinds
            shortList = futureKinds
            kinds = removedKinds
        for aKind in longList:
            if not aKind in shortList:
                kinds.append(aKind)
        return (addedKinds, removedKinds)
        
    def MixinPreProcess(self, futureKind):
        """
        UNDER CONSTRUCTION
        In the future this will save and restore bags of attributes
        during the stamping/unstamping operation.
        """
        addedKinds, removedKinds = self.AddedRemovedKinds(futureKind)
        addedMixins = []
        removedMixins = []
        # DLDTBD - flesh out
        return (addedMixins, removedMixins)

    def ValuePreProcess(self, futureKind):
        # Return a set of data to be carried over to the newly stamped Item
        # under the simple scheme, we just copy the redirected attributes
        carryOver = {}
        attrIter = self.itsKind.iterAttributes()
        while True:
            try:
                name, value = attrIter.next()
            except StopIteration:
                break
            if self.hasAttributeAspect(name, 'redirectTo'):
                try:
                    carryOver[name] = self.getAttributeValue(name)
                except AttributeError:
                    carryOver[name] = None
        return carryOver

    def StampPreProcess(self, futureKind):
        """
          Pre-process an Item for Stamping, and return data needed
        after the stamping takes place.
        In the future we will add a call to MixinPreProcess to 
        save and restore bags of attributes for restamping.
        """
        return self.ValuePreProcess(futureKind)

    def StampPostProcess(self, newKind, carryOver):
        """
          Post-process an Item for Stamping, and process data 
        prepared during StampPreProcess.
        On the future we will add a call to MixinPostProcess to
        finish saving and restoring bags of attributes for restamping.
        """

        """
        simple implementation - copy the redirected attributes,
        so the new notion of 'who' has the same value as the old one.
        """
        for key, value in carryOver.items():
            if value is not None:
                self.setAttributeValue(key, value)
    
class Project(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getProjectKind()
        super (Project, self).__init__(name, parent, kind)

class Group(ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getGroupKind()
        super (Group, self).__init__(name, parent, kind)
    

