""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.Parcel import Parcel
from repository.util.Path import Path
from repository.util.Lob import Lob
from repository.item.RefCollections import RefList
import repository.item.Item as Item
import repository.item.Query as Query
import mx.DateTime as DateTime
import logging
import tools.timing

import application.Globals as Globals

class ContentModel(Parcel):

    contentitemsPath = Path('//userdata/contentitems')

    # Cached UUID of //userdata/contentitems
    contentItemParentID = None

    def getContentItemParent(cls):
        """ Return //userdata/contentitems or create if non-existent """

        def makeContainer(parent, name, child):
            if child is None:
                return itemKind.newItem(name, parent)
            else:
                return child

        if cls.contentItemParentID is not None:
            parent = Globals.repository.findUUID(cls.contentItemParentID)
            if parent is not None:
                return parent
            # Our cached UUID is invalid
            cls.contentItemParentID is None

        parent = Globals.repository.find(cls.contentitemsPath)
        if parent is None:
            itemKind = Globals.repository.findPath('//Schema/Core/Item')
            parent = Globals.repository.walk(cls.contentitemsPath,
             makeContainer)
        cls.contentItemParentID = parent.itsUUID
        return parent

    getContentItemParent = classmethod(getContentItemParent)


class ChandlerItem(Item.Item):
    """ Subclasses of ChandlerItem get the following behavior for free:
        1. parent will automatically be set to //userdata/contentitems
        2. kind will be determined from the particular subclass's myKindPath

        All subclasses should have myKindID initialized to None, and set
        myKindPath to a string describing their kind's repository path.

        @@@ Better name suggestion welcomed!
    """

    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/ChandlerItem"

    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = self.getKind()
        super (ChandlerItem, self).__init__(name, parent, kind)


    def getKind(cls):
        """ Look up a class's kind, based on its myKindPath attribute """

        """ The UUID of the kind is cached in the class's myKindID 
            attribute """

        if cls.myKindID is not None:
            myKind = Globals.repository.findUUID(cls.myKindID)
            if myKind is not None:
                return myKind
            # Our cached UUID is invalid
            cls.myKindID = None

        myKind = Globals.repository.findPath(cls.myKindPath)
        assert myKind, "%s not yet loaded" % cls.myKindPath
        cls.myKindID = myKind.itsUUID
        return myKind

    getKind = classmethod(getKind)


class ContentItem(ChandlerItem):
    myKindPath = "//parcels/osaf/contentmodel/ContentItem"
    myKindID = None

    def __init__(self, name=None, parent=None, kind=None):
        super (ContentItem, self).__init__(name, parent, kind)

        self.createdOn = DateTime.now()
        self.creator = self.getCurrentMeContact()


    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(ContentItem, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.importance = 'normal'

        # default the displayName to 'untitled'
        self.displayName = _('untitled')

    """
    STAMPING SUPPORT

    Allow changing an Item's class and kind to dynamically
    add or remove capabilities.
    """

    SUPPORT_RESTAMPING = False # True means unstamping should save attributes for restamping

    def StampKind (self, operation, mixinKind):
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
        newKind = self._findStampedKind (operation, mixinKind)
        addedKinds, removedKinds = self._addedOrRemovedKinds (newKind, operation, mixinKind)
        self._stampPreProcess (removedKinds) # save away kinds being removed
        if newKind is not None:
            self.itsKind = newKind
        else:
            self.mixinKinds ((operation, mixinKind)) # create a class on-the-fly
        self._stampPostProcess (addedKinds) # initialize attributes of added kinds
        
        # make sure the respository knows about the item's new Kind
        # @@@BJS: I'm pretty sure this isn't necessary, so I'm commenting it out to speed things up.
        # Globals.repository.commit ()

    def _stampPreProcess (self, removedKinds):
        """
          Pre-process an Item for Stamping.  If we are unstamping an item,
        then we save away a mixin containing a copy of the attributes
        for the portion(s) being unstamped.
        """
        if self.SUPPORT_RESTAMPING:
            # values associated with removed kinds are saved for later restamping
            for removedKind in removedKinds:
                # Create a mixin to capture the attributes
                removedMixinClass = removedKind.getItemClass()
                try:
                    removedMixin = removedMixinClass()
                except:
                    pass
                else:
                    self._copyAttributeValues (sourceItem = self, 
                                               destItem = removedMixin, 
                                               template=removedMixin)
                    try:
                        previousStamps = self.previousStamps
                    except AttributeError:
                        previousStamps = []
                        self.previousStamps = previousStamps
                    # Save the mixin in the Item's previousStamps attribute
                    self.previousStamps.append (removedMixin)

    def _stampPostProcess (self, addedKinds):
        """
          Post-process an Item for Stamping.  If we are stamping an item,
        we want to initialize the new attributes appropriately.  If this
        item was previously stamped, we saved away the attribute values
        in an instance of the mixin.  Otherwise we initialize 
        the mixin attributes explicitly in the newly stamped item.
        """
        # check if we're restamping and get or create the mixin
        for addedKind in addedKinds:
            previousMixin = self._previousStamp (addedKind)
            if previousMixin is None:
                # ask the mixin to init its attributes.
                mixinClass = addedKind.getItemClass ()
                try:
                    mixinInitMethod = getattr (mixinClass, '_initMixin')
                except AttributeError:
                    pass
                else:
                    # call the unbound method with our expanded self to init those attributes
                    mixinInitMethod (self)
            else:
                # copy the attributes into our expanded item
                self._copyAttributeValues (sourceItem = previousMixin,
                                           destItem = self,
                                           template=previousMixin)

    def _previousStamp (self, stampedKind):
        """
          Return a mixin used for stamping previously on this item.
        Matches stampedKind with the previous stamp's kind.
        """
        try:
            previousMixins = self.previousStamps
        except AttributeError:
            return None
        else:
            for aMixin in previousMixins:
                if aMixin.itsKind is stampedKind:
                    previousMixins.remove (aMixin)
                    return aMixin
        return None

    def _copyAttributeValues (self, sourceItem, destItem, template):
        """
          Copy the attributes from the sourceItem to the destItem.  The attributes
        to be copied are determined by the template - all attributes of the template
        are copied.
        """
        attrIter = template.itsKind.iterAttributes()
        while True:
            try:
                name, value, k = attrIter.next()
            except StopIteration:
                break
            if not template.hasAttributeAspect (name, 'redirectTo'):
                try:
                    value = sourceItem.getAttributeValue (name)
                except AttributeError:
                    pass
                else:
                    destItem.setAttributeValue (name, value)

    """
      STAMPING TARGET-KIND DETERMINATION

    This section of code is responsible for selecting an appropriate futureKind
    to use when stamping.  If no futureKind can be determined, the stamping
    can still take place building the python class on-the-fly.  But selecting
    a preexisting Kind solves a few esoteric problems for us:
        1) Unifies class ordering.  We'd like a task item stamped as mail to be
            the same as a mail item stamped as a task.  The class order is
            important because we have multiple definitions of the redirectTo 
            attributes.
        2) Implements our "synergy mixin" requirement.  When an item is both
            a task and an event it gains an additional set of attributes
            due to synergy between the two kinds.  This represents an
            additional mixin that needs to be added (or removed).
    """

    def _candidateStampedKinds (self):
        """
        return the list of candidate kinds for stamping
        right now, we consider only ContentItems.
        """
        global cachedContentItemKinds
        try:
            contentItemKinds = cachedContentItemKinds
        except NameError:
            kindKind = Globals.repository.findPath('//Schema/Core/Kind')
            allKinds = Query.KindQuery().run([kindKind])
            contentItemKind = ContentItem.getKind ()
            contentItemKinds = [ aKind for aKind in allKinds if aKind.isKindOf (contentItemKind) ]
            cachedContentItemKinds = contentItemKinds
        return contentItemKinds

    def _computeTargetKindSignature (self, operation, stampKind):
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
        soughtSignature = _SuperKindSignature (myKind)
        stampSignature = _SuperKindSignature (stampKind)
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

    def _findStampedKind (self, operation, stampKind):
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
        signature = self._computeTargetKindSignature(operation, stampKind)
        if signature is None:
            return None
        soughtSignature, extrasAllowed = signature
        exactMatches = []
        closeMatches = []
        candidates = self._candidateStampedKinds()
        for candidate in candidates:
            candidateSignature = _SuperKindSignature(candidate)
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

    def _addedOrRemovedKinds (self, newKind, operation, mixinKind):
        """
        Return the list of kinds added or removed by the stamping.
        @param newKind: the kind to be used when stamped, or None if unknown
        @type newKind: C{Kind}
        @param operation: wheather adding or removing the kind
        @type operation: C{String}
        @param mixinKind: the kind being added or removed
        @type mixinKind: C{Kind}
        @return: a C{Tuple} containing ([addedKinds], [removedKinds])
        """
        if newKind is None:
            if operation == 'add':
                return ([mixinKind], [])
            else:
                assert operation == 'remove', "invalid Stamp operation in ContentItem._addedOrRemovedKinds: "+operation
                return ([], [mixinKind])
        newSignature = _SuperKindSignature (newKind)
        oldKind = self.itsKind
        oldSignature = _SuperKindSignature (self.itsKind)
        addedKinds = []
        removedKinds = []
        if len (oldSignature) < len (newSignature):
            # put an alias to the longer list into longList
            longList = newSignature
            shortList = oldSignature
            kinds = addedKinds
        else:
            assert len (oldSignature) > len (newSignature)
            longList = oldSignature
            shortList = newSignature
            kinds = removedKinds
        for aKind in longList:
            if not aKind in shortList:
                kinds.append (aKind)
        return (addedKinds, removedKinds)

    """
    ACCESSORS

    Accessors for Content Item attributes
    """
    def ItemWhoString (self):
        import osaf.contentmodel.contacts.Contacts as Contacts
        """
        return str(item.who)
        @@@DLD - XMLRefDicts that have EmailAddress items should 
                 know how to convert themselves to string
        """
        try:
            whoContacts = self.who # get redirected who list
        except AttributeError:
            return ''
        try:
            numContacts = len(whoContacts)
        except TypeError:
            numContacts = -1
        if numContacts == 0:
            return ''
        if numContacts > 0:
            whoNames = []
            for whom in whoContacts.values():
                whoNames.append (str (whom))
            whoString = ', '.join(whoNames)
        else:
            whoString = str (whoContacts)
            if isinstance(whoContacts, Contacts.ContactName):
                names = []
                if len (whoContacts.firstName):
                    names.append (whoContacts.firstName)
                if len (whoContacts.lastName):
                    names.append (whoContacts.lastName)
                whoString = ' '.join(names)
        return whoString

    def ItemWhoFromString (self):
        try:
            whoFrom = self.whoFrom # get redirected whoFrom list
        except AttributeError:
            return ''
        return str (whoFrom)

    def ItemBodyString (self):
        """
        return str(item.body) converts from text to string 
        """
        try:
            noteBody = self.body
        except AttributeError:
            noteBody = ''
        else:
            if isinstance(noteBody, Lob):
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

    def getEmailAddress (self, nameOrAddressString):
        """
          Lookup or create an EmailAddress based
        on the supplied string.
        This method is here for convenient access, so users
        don't need to import Mail.
        """
        import mail.Mail as Mail
        return Mail.EmailAddress.getEmailAddress (nameOrAddressString)

    def getCurrentMeEmailAddress (self):
        """
          Lookup or create a current "me" EmailAddress.
        The "me" EmailAddress is whichever one has the current IMAP default address.
        This method is here for convenient access, so users
        don't need to import Mail.
        """
        import mail.Mail as Mail
        return Mail.EmailAddress.getCurrentMeEmailAddress ()

    def getCurrentMeContact(self):
        """
          Lookup the current "me" Contact.
        """
        import contacts.Contacts
        return contacts.Contacts.Contact.getCurrentMeContact()

    def setStatusMessage (cls, message, *args):
        Globals.mainView.setStatusMessage (message, *args)
    setStatusMessage = classmethod (setStatusMessage)

"""
STAMPING SUPPORT CLASSES
"""
class _SuperKindSignature(list):
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
        super(_SuperKindSignature, self).__init__(*args, **kwds)
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

class Project(ChandlerItem):
    myKindPath = "//parcels/osaf/contentmodel/Project"
    myKindID = None

    def __init__(self, name=None, parent=None, kind=None):
        super (Project, self).__init__(name, parent, kind)

class Group(ChandlerItem):
    myKindPath = "//parcels/osaf/contentmodel/Group"
    myKindID = None

    def __init__(self, name=None, parent=None, kind=None):
        super (Group, self).__init__(name, parent, kind)
