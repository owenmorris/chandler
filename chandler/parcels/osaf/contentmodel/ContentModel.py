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
    "Can't stamp Item with the requested Kind Aspect"

class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getContentItemKind()
        super (ContentItem, self).__init__(name, parent, kind)

    def StampKind(self, operation, aspectKind):
        """
          Stamp ourself into the new kind defined by the
        Aspect passed in newKind.
        * Take the current kind, the operation and the Aspect,
        and compute the future Kind.
        * Prepare to become the future Kind, which may mean creating
        one or more Aspects, or saving off Aspects.
        * Stamp ourself to the new Kind.
        * Move the attributes from the Aspects.
        """
        futureKind = self.NewStampedKind(operation, aspectKind)
        addedAspects, removedAspects = self.StampPreProcess(futureKind)
        self.itsKind = futureKind
        self.StampPostProcess(futureKind, addedAspects, removedAspects)

    def NewStampedKind(self, operation, aspectKind):
        """
           Return the new Kind that results from self being
        stamped with the Aspect specified.
        @param self: an Item that will be stamped
        @type self: C{Item}
        @param operation: 'add' to add the aspect, 'remove' to remove
        @type operation: C{String}
        @param aspectKind: the Aspect to be added or removed
        @type aspectKind: C{Kind} of the Aspect
        @return: a C{Kind}
        """
        myKind = self.itsKind
        currentAspects = myKind.getAttributeValue('superKinds', default = [])
        # work with a copy of the superKinds list
        soughtAspects = []
        for aspect in currentAspects:
            soughtAspects.append(aspect)
        if operation == 'add':
            soughtAspects.append(aspectKind)
        else:
            assert operation == 'remove', "invalid Stamp operation in ContentItem.NewStampedKind: "+operation
            soughtAspects.remove(aspectKind)
        qualified = []
        kindKind = Globals.repository.findPath('//Schema/Core/Kind')
        for candidate in Query.KindQuery().run([kindKind]):
            superKinds = candidate.getAttributeValue('superKinds', default = [])
            extras = abs(len(soughtAspects) - len(superKinds))
            if extras > 1:
                continue
            for aKind in soughtAspects:
                if not aKind in superKinds:
                    # aKind not found, continue with the next candidate
                    break
            else:
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
        # couldn't find a match
        if len(qualified) > 1:
            raise StampError, "Multiple Stamp candidates found for object %s of Kind %s with Aspect %s" % \
                              (self.itsName, self.itsKind.itsName, aspectKind.itsName)        
        raise StampError, "Can't Stamp object %s of Kind %s with Aspect %s" % \
                          (self.itsName, self.itsKind.itsName, aspectKind.itsName)        

    def AddedRemovedKinds(self, futureKind):
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
            aspects = removedKinds
        for aKind in longList:
            if not aKind in shortList:
                kinds.append(aKind)
        return (addedKinds, removedKinds)
        
    def StampPreProcess(self, futureKind):
        addedKinds, removedKinds = self.AddedRemovedKinds(futureKind)
        addedAspects = []
        removedAspects = []
        # DLDTBD - flesh out
        return (addedAspects, removedAspects)
        
    def StampPostProcess(self, futureKind, addedAspects, removedAspects):
        # DLDTBD - flesh out
        pass

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
    

