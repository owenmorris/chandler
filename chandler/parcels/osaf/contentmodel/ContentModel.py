""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.Parcel import Parcel
import repository.item.Item as Item
import repository.item.Query as Query
import repository.persistence.XMLRepositoryView as XMLRepositoryView
from mx import DateTime
import logging

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

class SuperKindSignature(list):
    """
    A list of unique superkinds, used as a signature to identify 
    the structure of a Kind for stamping.
    The signature is the list of twig node superkinds of the Kind.
    Using a tree analogy, a twig is the part farthest from the leaf
    that has no braching.
    Specifically, a twig node in the SuperKind hierarchy is a node 
    that has at most one superkind, and whose superkind has at
    most one superkind, all they way up.
    The twig superkinds list makes the best signature for two reasons:
       1) it bypasses all the branching, allowing (A, (B,C)) to match 
            ((A, B), C)
       2) it uses the most specialized form when there is no branching,
            thus if D has superKind B, and B has no superKinds,
            D is more specialized, so we want to use it.
    """
    def __init__(self, aKind, *args, **kwds):
        """
        construct with a single Kind
        """
        super(SuperKindSignature, self).__init__(*args, **kwds)
        onTwig = self.appendTwigSuperkinds(aKind)
        if onTwig:
            assert len(self) == 0, "Error building superKind Signature"
            self.append(aKind)

    def appendTwigSuperkinds(self, aKind):
        """
        called with a kind, appends all the twig superkinds
        and returns True iff there's been no branching within
        this twig
        """
        supers = aKind.getAttributeValue('superKinds', default = [])
        numSupers = len(supers)
        onTwig = True
        for kind in supers:
            onTwig = self.appendTwigSuperkinds(kind)
            if onTwig and numSupers > 1:
                self.appendUnique(kind)
        return numSupers < 2 and onTwig

    def appendUnique(self, item):
        if not item in self:
            self.append(item)

    def extend(self, sequence):
        for item in sequence:
            self.appendUnique(item)
    
    def properSubsetOf(self, sequence):
        """
        return True if self is a proper subset of sequence
        meaning all items in self are in sequence
        """
        for item in self:
            if not item in sequence:
                return False
        return True

    def __str__(self):
        readable = []
        for item in self:
            readable.append(item.itsName)
        theList = ', '.join(readable)
        return '['+theList+']'
            
class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getContentItemKind()
        super (ContentItem, self).__init__(name, parent, kind)

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(ContentItem, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.importance = 'normal'
        self.createdOn = DateTime.now()


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

    def CandidateStampedKinds(self):
        """
        return the list of candidate kinds for stamping
        right now, we consider only ContentItems.
        """
        kindKind = Globals.repository.findPath('//Schema/Core/Kind')
        allKinds = Query.KindQuery().run([kindKind])
        contentItemKinds = []
        contentItemKind = ContentModel.getContentItemKind ()
        for aKind in allKinds:
            if aKind.isKindOf (contentItemKind):
                contentItemKinds.append (aKind)
        return contentItemKinds

    def ComputeTargetKindSignature(self, operation, stampKind):
        """
        Compute the Kind Signature for stamping.
        Takes the operation, the kind of self, the stampKind,
        and computes a target kind signature, which is a list
        of superKinds.
        returns a tuple with the signature, and the allowed
        extra kinds
        @return: a C{Tuple} (kindSignature, allowedExtra)
           where kindSignature is a list of kinds, and
           allowedExtra is an integer telling how many
           extra kinds are allowed beyond what's in the target.
        """
        myKind = self.itsKind
        soughtSignature = SuperKindSignature(myKind)
        stampSignature = SuperKindSignature(stampKind)
        if operation == 'add':
            for stampSuperKind in stampSignature:
                if stampSuperKind in soughtSignature:
                    logging.warning("Trying to stamp with a Kind Signature already present.")
                    logging.warning("%s has signature %s which overlaps with %s whose signature is %s)" % \
                                    (stampKind.itsName, stampSignature, \
                                     myKind.itsName, soughtSignature))
                    return None # in case this method is overloaded
            soughtSignature.extend(stampSignature)
            extrasAllowed = 1
        else:
            assert operation == 'remove', "invalid Stamp operation in ContentItem.NewStampedKind: "+operation
            if not stampSignature.properSubsetOf(soughtSignature):
                logging.warning("Trying to unstamp with a Kind Signature not already present.")
                logging.warning("%s has signature %s which is not present in %s: %s" % \
                                    (stampKind.itsName, stampSignature, \
                                     myKind.itsName, soughtSignature))
                return None # in case this method is overloaded
            for stampSuperKind in stampSignature:
                soughtSignature.remove(stampSuperKind)
            extrasAllowed = -1
        return (soughtSignature, extrasAllowed)

    def FindStampedKind(self, operation, stampKind):
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
        signature = self.ComputeTargetKindSignature(operation, stampKind)
        if signature is None:
            return None
        soughtSignature, extrasAllowed = signature
        exactMatches = []
        closeMatches = []
        candidates = self.CandidateStampedKinds()
        for candidate in candidates:
            candidateSignature = SuperKindSignature(candidate)
            extras = len(candidateSignature) - len(soughtSignature)
            if extras != 0 and (extras - extrasAllowed) != 0:
                continue
            shortList = soughtSignature
            longList = candidateSignature
            if extras < 0:
                shortList = candidateSignature
                longList = soughtSignature
            if shortList.properSubsetOf(longList):
                # found a potential match
                if extras == 0:
                    # exact match
                    exactMatches.append(candidate)
                else:
                    # close match - keep searching for a better match
                    closeMatches.append(candidate)

        # finished search.  Better have only one exact match or else the match is ambiguous.
        if len(exactMatches) == 1:
            return exactMatches[0]
        elif len(exactMatches) == 0:
            if len(closeMatches) == 1:
                # zero exact matches is OK when "mixin synergy" is involved.
                return closeMatches[0]

        # Couldn't find a single exact match or a single close match.
        logging.warning ("Couldn't find suitable candidates for stamping %s with %s." \
                        % (self.itsKind.itsName, stampKind.itsName))
        logging.warning ("Exact matches: %s" % exactMatches)
        logging.warning ("Close matches: %s" % closeMatches)
        # ReKind with the Mixin Kind on-the-fly
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
                    value = self.getAttributeValue(name)
                    # collections need to deep copy their attribute value
                    # otherwise there will be two references to the collection,
                    #  which will go away when the first reference goes away.
                    value = self.CloneCollectionValue(name, value)
                    oldRedirect = self.getAttributeAspect(name, 'redirectTo')
                    carryOver[name] = (value, oldRedirect)
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
                value, redirect = value
                # if the redirect has changed, set the value to the new attribute
                if self.hasAttributeAspect(key, 'redirectTo'):
                    newRedirect = self.getAttributeAspect(key, 'redirectTo')
                    if redirect != newRedirect:
                        try:
                            self.setAttributeValue(key, value)
                        except AttributeError:
                            pass
    
    def CloneCollectionValue(self, key, value):
        """
        If the value is some kind of collection, we need to make a shallow copy
        so the collection isn't destroyed when the reference in the other attribute
        is destroyed.
        
        @param key: the name of the indirect attribute.
        @type name: a string.
        @param value: the value, already set, in the attribute
        @type value: anything compatible with the attribute's type
        
        I made this a separate method for easy overloading.
        """
        # don't need to clone single items
        if self.getAttributeAspect(key, 'cardinality') == 'single':
            return value

        # check the first item to see if it has an alias
        try:
            alias = value.getAlias(value[0])
            hasAlias = alias is not None
        except:
            hasAlias = False

        # create the clone
        if hasAlias:
            clone = {}
        else:
            clone = []

        # copy each item, using alias if available
        for item in value:
            if hasAlias:
                alias = value.getAlias(item)
                clone[alias] = item
            else:
                clone.append(item)
        
        return clone

    def ItemWhoString (self):
        import osaf.contentmodel.contacts.Contacts as Contacts
        """
        return str(item.who)
        DLDTBD - XMLRefDicts that have EmailAddress items should know how to do this
        """
        try:
            whoContacts = self.who # get redirected who list
        except AttributeError:
            return ''
        try:
            numContacts = len(whoContacts)
        except TypeError:
            numContacts = 0            
        if numContacts > 0:
            whoNames = []
            for whom in whoContacts.values():
                whoNames.append(whom.getItemDisplayName())
            whoString = ', '.join(whoNames)
        else:
            whoString = ''
            if isinstance(whoContacts, Contacts.ContactName):
                whoString = whoContacts.firstName + ' ' + whoContacts.lastName
        return whoString

    def ItemBodyString (self):
        """
        return str(item.body) converts from text to string 
        """
        try:
            noteBody = self.body
        except AttributeError:
            noteBody = ''
        else:
            if isinstance(noteBody, XMLRepositoryView.XMLText):
                # Read the unicode stream from the XML
                noteBody = noteBody.getInputStream().read()
        return noteBody

    def ItemAboutString (self):
        """
        return str(item.about)
        """
        try:
            about = self.about
        except AttributeError:
            about = ''
        return about

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
    

