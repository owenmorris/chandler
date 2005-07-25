""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel"

from datetime import datetime

from application.Parcel import Parcel
from application import schema
from repository.util.Path import Path
from repository.util.Lob import Lob
from repository.item.RefCollections import RefList
from repository.schema.Kind import Kind
import repository.item.Item as Item
import repository.item.Query as Query
import logging

import application.Globals as Globals

class ContentKind(Kind):
    """This kind is a metakind for creating other kinds.  Kinds which are
    an instance of ContentKind will have an attribute 'detailView' of type
    Block.  We could also make this attribute a bidiref."""

    __metaclass__ = schema.ItemClass

    schema.kindInfo(displayName="Metakind 'Content Kind'")

    detailView = schema.One()   # Block


class ImportanceEnum(schema.Enumeration):
    """Importance Enum"""
    schema.kindInfo(
        displayName="Importance Enum"
    )
    values = "important", "normal", "fyi"


class Calculated(property):
    """ 
    A property with type information, in the style of our schema.* objects. 
    - This could become a schema class when it grows up :-)
    - I'm open to a different name: I think it oughta be schema.Property, but pje
      thought Calculated was better...
    """
    def __new__(cls, schema_type, displayName, fget, fset=None, fdel=None, doc=None):
        return property.__new__(cls, fget, fset, fdel, doc)
    
    def __init__(self, schema_type, displayName, fget, fset=None, fdel=None, doc=None):
        property.__init__(self, fget, fset, fdel, doc)
        self.type = schema_type
        self.displayName = displayName


class ContentItem(schema.Item):
    """Content Item"""

    schema.kindInfo(
        displayName = "Content Item",
        examples = [
            "an Calendar Event -- 'Lunch with Tug'",
            "a Contact -- 'Terry Smith'",
            "a Task -- 'mail 1040 to IRS'",
        ],
        description =
            "Content Item is the abstract super-kind for things like "
            "Contacts, Calendar Events, Tasks, Mail Messages, and Notes. "
            "Content Items are user-level items, which a user might file, "
            "categorize, share, and delete.",
    )


    body = schema.One(
        schema.Lob,
        displayName="Body",
        doc="All Content Items may have a body to contain notes.  It's "
            "not decided yet whether this body would instead contain the "
            "payload for resource items such as presentations or "
            "spreadsheets -- resource items haven't been nailed down "
            "yet -- but the payload may be different from the notes because "
            "payload needs to know MIME type, etc."
    )

    creator = schema.One(
        # Contact
        displayName="creator",
        doc="Link to the contact who created the item."
    )

    modifiedOn = schema.One(
        schema.DateTime,
        displayName="Last Modified On",
        doc="DateTime this item was last modified"
    )

    lastModifiedBy = schema.One(
        # Contact
        displayName="Last Modified By",
        doc="Link to the contact who last modified the item.",
    )

    importance = schema.One(ImportanceEnum,
        displayName="Importance",
        doc="Most items are of normal importance (no value need be show), "
            "however some things may be flagged either highly important or "
            "merely 'fyi'. This attribute is also used in the mail schema, so "
            "we shouldn't make any changes here that would break e-mail "
            "interoperability features.",
        initialValue="normal",
    )

    lastModified = schema.One(schema.String)

    isPrivate = schema.One(schema.Boolean, initialValue=False)

    isRead = schema.One(
        schema.Boolean,
        initialValue=False,
        doc="A flag indicating whether the this item has "
            "been 'viewed' by the user"
    )

    previousStamps = schema.Sequence(
        schema.Item,
        doc="A list of mixin items that were used as stamps on this "
            "item previously."
    )

    createdOn = schema.One(
        schema.DateTime,
        displayName="created",
        doc="DateTime this item was created"
    )

    contentsOwner = schema.Sequence(
        "osaf.framework.blocks.Block.Block", inverse="contents"
    )

    currentItemOf = schema.One("CurrentPointer", otherName="item")

    # Placeholders for bidirectional references
    
    itemCollectionInclusions = schema.Sequence()    # ItemCollection
    itemCollectionExclusions = schema.Sequence()    # ItemCollection

    # We haven't ported the "other end" of these links, so we have to use
    # 'otherName' settings to ensure that they get hooked up correctly.
    # The 'otherName' settings should be removed once the other side of these
    # links exist in the Python schema.

    shares = schema.Sequence(initialValue=(), otherName="contents") # share
    viewContainer = schema.Sequence(otherName="views")  # ViewContainer
    TPBDetailItemOwner = schema.Sequence(otherName="TPBDetailItem") # Block
    TPBSelectedItemOwner = schema.Sequence(otherName="TPBSelectedItem") # Block

    schema.addClouds(
        sharing = schema.Cloud("displayName", body, "issues", createdOn,
                               "description"),
        copying = schema.Cloud()
    )

    def __init__(self, name=None, parent=None, kind=None, view=None, **kw):
        super(ContentItem, self).__init__(name, parent, kind, view, **kw)
        self.createdOn = datetime.now()
        if view is None:
            view = self.itsView
        self.creator = self.getCurrentMeContact(view)

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(ContentItem, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        # default the displayName to 'untitled'
        self.displayName = _('untitled')

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        try:
            super(ContentItem, self).ExportItemData (clipboardHandler)
        except AttributeError:
            pass

        # Let the clipboard handler know we've got a ContentItem to export
        clipboardHandler.ExportItemFormat(self, 'ContentItem')

    """
    STAMPING SUPPORT

    Allow changing an Item's class and kind to dynamically
    add or remove capabilities.
    """

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
        addedKinds = self._addedKinds (newKind, operation, mixinKind)
        if newKind is not None:
            self.itsKind = newKind
        else:
            self.mixinKinds ((operation, mixinKind)) # create a class on-the-fly
        self._stampPostProcess (addedKinds) # initialize attributes of added kinds
        
        # make sure the respository knows about the item's new Kind
        #  to trigger updates in the UI.
        # @@@BJS: I'm pretty sure this isn't necessary, so I'm commenting it out to speed things up.
        # self.itsView.commit ()

    def _stampPostProcess (self, addedKinds):
        """
          Post-process an Item for Stamping.  If we have added a kind (or kinds),
        we want to initialize the new attributes appropriately, by calling
        the _initMixin method explicitly on the newly stamped item.
        """
        # check if we're restamping and get or create the mixin
        for addedKind in addedKinds:
            # ask the mixin to init its attributes.
            mixinClass = addedKind.getItemClass ()
            try:
                # get the init method associated with the mixin class added
                mixinInitMethod = getattr (mixinClass, '_initMixin')
            except AttributeError:
                pass
            else:
                # call the unbound method with our expanded self to init those attributes
                mixinInitMethod (self)

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
            kindKind = self.findPath('//Schema/Core/Kind')
            allKinds = Query.KindQuery().run([kindKind])
            contentItemKind = ContentItem.getKind (self.itsView)
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

    def _addedKinds (self, newKind, operation, mixinKind):
        """
        Return the list of kinds added by the stamping.
        @param newKind: the kind to be used when stamped, or None if unknown
        @type newKind: C{Kind}
        @param operation: wheather adding or removing the kind
        @type operation: C{String}
        @param mixinKind: the kind being added or removed
        @type mixinKind: C{Kind}
        @return: a C{List} of kinds added
        """
        if newKind is None:
            if operation == 'add':
                return [mixinKind]
            else:
                assert operation == 'remove', "invalid Stamp operation in ContentItem._addedOrRemovedKinds: "+operation
                return []
        newSignature = _SuperKindSignature (newKind)
        oldSignature = _SuperKindSignature (self.itsKind)
        addedKinds = []
        if len (oldSignature) < len (newSignature):
            for aKind in newSignature:
                if not aKind in oldSignature:
                    addedKinds.append (aKind)
        return addedKinds

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
        return str(item.body) converts from text lob to string 
        """
        try:
            noteBody = self.body
        except AttributeError:
            noteBody = ''
        else:
            if isinstance(noteBody, Lob):
                # Read the unicode stream from the XML
                noteBody = noteBody.getPlainTextReader().read()
        return noteBody

    def SetItemBodyString (self, value):
        try:
            lob = self.body
        except AttributeError:
            lobType = self.getAttributeAspect ('body', 'type')
            self.body = lobType.makeValue(value, indexed=True)
        else:
            writer = lob.getWriter()
            try:
                writer.write(value)
            finally:
                writer.close()

    bodyString = Calculated(schema.String, "bodyString", 
                            fget=ItemBodyString, fset=SetItemBodyString,
                            doc="body attribute as a string")
        
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
        return Mail.EmailAddress.getEmailAddress (self.itsView, nameOrAddressString)

    def getCurrentMeEmailAddress (self):
        """
          Lookup or create a current "me" EmailAddress.
        The "me" EmailAddress is whichever one has the current IMAP default address.
        This method is here for convenient access, so users
        don't need to import Mail.
        """
        import mail.Mail as Mail
        return Mail.EmailAddress.getCurrentMeEmailAddress (self.itsView)

    def getCurrentMeContact(self, view):
        """
          Lookup the current "me" Contact.
        """
        import contacts.Contacts
        return contacts.Contacts.Contact.getCurrentMeContact(view)

    def setStatusMessage (cls, message, *args):
        Globals.views[0].setStatusMessage (message, *args)
    setStatusMessage = classmethod (setStatusMessage)



    READWRITE = 'read-write'
    READONLY = 'read-only'
    UNSHARED = 'unshared'

    def getSharedState(self):
        """
        Examine all the shares this item participates in; if any of those
        shares are writable the shared state is READWRITE.  If all the shares
        are read-only the shared state is READONLY.  Otherwise UNSHARED.
        """

        state = ContentItem.UNSHARED
        if hasattr(self, 'queries'):
            for collection in self.queries:
                if hasattr(collection, 'shares'):
                    for share in collection.shares:
                        state = ContentItem.READONLY
                        if share.mode in ('put', 'both'):
                            return ContentItem.READWRITE

        return state

    sharedState = property(getSharedState)

    def isAttributeModifiable(self, attribute):

        if self.sharedState in (ContentItem.READWRITE, ContentItem.UNSHARED):
            return True

        for collection in self.queries:
            for share in collection.shares:
                # We know that share must be read-only.
                # If the attribute is shared as part of this read-only share,
                # then the user can't modify it.
                if attribute in share.getSharedAttributes(self):
                    return False
        return True



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

class Project(ContentItem):

    schema.kindInfo(
        displayName = "Project",
        examples = [
            'my "Housewarming Party" project',
            "my department's \"Move to new building\" project",
            "my company's \"Open Seattle Store\" project",
        ],
        description =
            "Users can create projects to help organize their work. Users can "
            "take content items (like tasks and mail messages) and assign "
            "them to different projects."
    )

    parentProject = schema.One(
        'Project',
        displayName = 'Parent Project',
        doc = 'Projects can be organized into hierarchies. Each project can have one parent.',
        inverse = 'subProjects',
    )
    subProjects = schema.Sequence(
        'Project',
        displayName = 'Sub Projects',
        doc = 'Projects can be organized into hierarchies. Each project can have many sub-projects.',
        inverse = 'parentProject',
    )


class Group(ContentItem):

    schema.kindInfo(
        displayName = '"Playlist"/"Item Collection"',
        description =
            "See http://wiki.osafoundation.org/twiki/bin/view/Jungle/CollectionProject",
        issues = [
            'We still need to work out some issues about how '
            '"playlists"/"item collections" are modeled.',
            'We need to find a name for these things.',
        ]
    )



class CurrentPointer(schema.Item):
    item = schema.One(
        ContentItem,
        initialValue = None,
        inverse = ContentItem.currentItemOf,
    )

