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


""" Classes used for pim parcel and kinds.
"""

__parcel__ = "osaf.pim"

from datetime import datetime

from application.Parcel import Parcel
from application import schema
from repository.util.Path import Path
from repository.util.Lob import Lob
from repository.item.RefCollections import RefList
from repository.schema.Kind import Kind
import repository.item.Item as Item
import logging
from i18n import OSAFMessageFactory as _
from osaf import messages
from PyICU import ICUtzinfo

logger = logging.getLogger(__name__)

class ContentKind(Kind):
    """
    This kind is a metakind for creating other kinds.  Kinds which are
    an instance of ContentKind will have an attribute 'detailView' of type
    Block.  We could also make this attribute a bidiref.
    """

    __metaclass__ = schema.ItemClass

    detailView = schema.One()   # Block


class ImportanceEnum(schema.Enumeration):
    """
    Importance Enum
    """
    values = "important", "normal", "fyi"

class TriageEnum(schema.Enumeration):
    values = "now", "later", "done"

class Calculated(property):
    """ 
    A property with type information, in the style of our schema.* objects. 
    - This could become a schema class when it grows up :-)
    - I'm open to a different name: I think it oughta be schema.Property, but pje
    thought Calculated was better...
    """
    def __new__(cls, schema_type, displayName, basedOn, fget, fset=None, fdel=None, 
                doc=None):
        return property.__new__(cls, fget, fset, fdel, doc)
    
    def __init__(self, schema_type, displayName, basedOn, fget, fset=None, fdel=None, 
                 doc=None):
        property.__init__(self, fget, fset, fdel, doc)
        self.type = schema_type
        self.displayName = displayName
        self.basedOn = basedOn


class ContentItem(schema.Item):
    """
    Content Item

    Content Item is the abstract super-kind for things like Contacts, Calendar
    Events, Tasks, Mail Messages, and Notes.  Content Items are user-level
    items, which a user might file, categorize, share, and delete.

    Examples:
     - a Calendar Event -- 'Lunch with Tug'
     - a Contact -- 'Terry Smith'
     - a Task -- 'mail 1040 to IRS'
    """
    displayName = schema.One(schema.Text, indexed=True)
    body = schema.One(
        schema.Text,
        displayName=_(u"Body"),
        indexed = True,
        defaultValue = _(u""),
        doc="All Content Items may have a body to contain notes.  It's "
            "not decided yet whether this body would instead contain the "
            "payload for resource items such as presentations or "
            "spreadsheets -- resource items haven't been nailed down "
            "yet -- but the payload may be different from the notes because "
            "payload needs to know MIME type, etc."
    )

    creator = schema.One(
        # Contact
        displayName=_(u"creator"),
        doc="Link to the contact who created the item."
    )

    modifiedOn = schema.One(
        schema.DateTimeTZ,
        displayName=_(u"Last Modified"),
        doc="DateTime this item was last modified"
    )

    lastModifiedBy = schema.One(
        # Contact
        displayName=_(u"Last Modified By"),
        doc="Link to the contact who last modified the item.",
    )

    importance = schema.One(ImportanceEnum,
        displayName=u"Importance",
        doc="Most items are of normal importance (no value need be show), "
            "however some things may be flagged either highly important or "
            "merely 'fyi'. This attribute is also used in the mail schema, so "
            "we shouldn't make any changes here that would break e-mail "
            "interoperability features.",
        initialValue="normal",
    )

    lastModified = schema.One(schema.Text)

    mine = schema.One(schema.Boolean, initialValue=True)

    private = schema.One(schema.Boolean, initialValue=False)

    read = schema.One(
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
        schema.DateTimeTZ,
        displayName=_(u"Created"),
        doc="DateTime this item was created"
    )

    contentsOwner = schema.Sequence(
        "osaf.framework.blocks.Block.Block", inverse="contents"
    )

    tags = schema.Sequence(
        'Tag',
        displayName=u'Tags',
        description='All the Tags associated with this ContentItem',
        inverse='items',
        initialValue=[]
    )

    notifications = schema.Sequence('UserNotification',
        displayName=u'User Notifications',
        description='All notifications for this ContentItem',
        initialValue=[]
    )

    triageStatus = schema.One(TriageEnum, indexed=True,
                              displayName=_(u"Triage Status"),
                              initialValue="now")

    # We haven't ported the "other end" of these links, so we have to use
    # 'otherName' settings to ensure that they get hooked up correctly.
    # The 'otherName' settings should be removed once the other side of these
    # links exist in the Python schema.

    shares = schema.Sequence(initialValue=[], otherName="contents") # share
    sharedIn = schema.Sequence(initialValue=[], otherName="items") # share
    viewContainer = schema.Sequence(otherName="views")  # ViewContainer
    branchPointDetailItemOwner = schema.Sequence(otherName="detailItem") # Block
    branchPointSelectedItemOwner = schema.Sequence(otherName="selectedItem") # Block

    # ContentItem instances can be put into ListCollections and AppCollections
    collections = schema.Sequence(otherName='inclusions', notify=True)

    # ContentItem instances can be put into SmartCollections (which define
    # the other end of this biref)
    appearsIn = schema.Sequence()

    schema.addClouds(
        sharing = schema.Cloud("displayName", body, createdOn, 'tags',
                               "description", lastModifiedBy),
        copying = schema.Cloud()
    )

    def __init__(self, *args, **kw):
        super(ContentItem, self).__init__(*args, **kw)
        if not hasattr(self, 'createdOn'):
            self.createdOn = datetime.now(ICUtzinfo.default)

    def __str__ (self):
        if self.isStale():
            return super(ContentItem, self).__str__()
            # Stale items can't access their attributes

        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        if self.isStale():
            return super(ContentItem, self).__unicode__()

        return self.getItemDisplayName()

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(ContentItem, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        # default the displayName
        self.displayName = messages.UNTITLED

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        try:
            super(ContentItem, self).ExportItemData (clipboardHandler)
        except AttributeError:
            pass

        # Let the clipboard handler know we've got a ContentItem to export
        clipboardHandler.ExportItemFormat(self, 'ContentItem')

    def addToCollection(self, collection):
        """Add self to the given collection.
        
        For most items, just call collection.add(self), but for recurring
        events, this method is intercepted by a proxy and buffered while the
        user selects from various possible meanings for adding a recurring event
        to a collection.
        
        """
        collection.add(self)
        
    def removeFromCollection(self, collection, cutting = False):
        """Remove self from the given collection.
        
        For most items, just call collection.remove(self), but for recurring
        events, this method is intercepted by a proxy and buffered while the
        user selects from various possible meanings for removing a recurring
        event from a collection.
        
        Cutting is typically equivalent to remove, but recurrence has different
        behavior for cutting operations than delete.
        
        """
        collection.remove(self)

    def getMembershipItem(self):
        """ Get the item that should be used to test for membership
        tests i.e. if item in collection: should be if
        item.getMembershipItem() in collection

        For most items, this is just itself, but for recurring
        events, this method is intercepted by a proxy.
        """
        return self

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
        
        all = schema.ns("osaf.pim", self.itsView).allCollection
        inAllBeforeStamp = self in all
        
        if newKind is not None:
            self.itsKind = newKind
        else:
            self.mixinKinds ((operation, mixinKind)) # create a class on-the-fly
            
        # [Bug:6151] If you unstamp a received email, it stops being in the "In"
        # collection, and is therefore no longer "mine", and disappears
        # completely. So, for now explicitly add self back to the all collection
        # in this case.
        if inAllBeforeStamp and not self in all:
            all.add(self)

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
        contentItemKind = ContentItem.getKind(self.itsView)
        contentItemKinds = set((contentItemKind,))
        def collectSubKinds(aKind):
            subKinds = getattr(aKind, 'subKinds', None)
            if subKinds is not None:
                contentItemKinds.update(subKinds)
                map(collectSubKinds, subKinds)
        collectSubKinds(contentItemKind)
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
            stampAdditions = []
            for stampSuperKind in stampSignature:
                if not stampSuperKind in soughtSignature:
                    stampAdditions.append(stampSuperKind)
            if len(stampAdditions) == 0:
                logger.warning("Trying to stamp with a Kind Signature already present.")
                logger.warning("%s has signature %s which overlaps with %s whose signature is %s)" % \
                                (stampKind.itsName, stampSignature, \
                                 myKind.itsName, soughtSignature))
                raise StampAlreadyPresentError # no new class was added
            soughtSignature.extend(stampAdditions)
            extrasAllowed = 1
        else:
            assert operation == 'remove', "invalid Stamp operation in ContentItem.NewStampedKind: "+operation
            if not stampSignature.properSubsetOf(soughtSignature):
                logger.warning("Trying to unstamp with a Kind Signature not already present.")
                logger.warning("%s has signature %s which is not present in %s: %s" % \
                                    (stampKind.itsName, stampSignature, \
                                     myKind.itsName, soughtSignature))
                raise StampNotPresentError # Can't remove a stamp that's not there
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
        @param stampKind: the Mixin Kind to be added or removed
        @type stampKind: C{Kind} of the Mixin
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
        logger.debug ("Couldn't find suitable candidates for stamping %s with %s." \
                        % (self.itsKind.itsName, stampKind.itsName))
        logger.debug ("Exact matches: %s" % exactMatches)
        logger.debug ("Close matches: %s" % closeMatches)
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
        from osaf.pim.contacts import ContactName
        """
        return unicode(item.who)
        @@@DLD - XMLRefDicts that have EmailAddress items should 
                 know how to convert themselves to string
        """
        try:
            whoContacts = self.who # get redirected who list
        except AttributeError:
            return u''
        try:
            numContacts = len(whoContacts)
        except TypeError:
            numContacts = -1
        if numContacts == 0:
            return ''
        if numContacts > 0:
            whoNames = []
            for whom in whoContacts.values():
                whoNames.append (unicode (whom))
            whoString = u', '.join(whoNames)
        else:
            whoString = unicode (whoContacts)
            if isinstance(whoContacts, ContactName):
                names = []
                if len (whoContacts.firstName):
                    names.append (whoContacts.firstName)
                if len (whoContacts.lastName):
                    names.append (whoContacts.lastName)
                whoString = u' '.join(names)
        return whoString

    def ItemWhoFromString (self):
        try:
            whoFrom = self.whoFrom # get redirected whoFrom list
        except AttributeError:
            return u''
        return unicode (whoFrom)

    def ItemAboutString (self):
        """
        return unicode(item.about)
        """
        try:
            about = self.about
        except AttributeError:
            about = u''
        return about

    def getEmailAddress (self, nameOrAddressString):
        """
          Lookup or create an EmailAddress based
        on the supplied string.
        This method is here for convenient access, so users
        don't need to import Mail.
        """
        from mail import EmailAddress
        return EmailAddress.getEmailAddress (self.itsView, nameOrAddressString)

    def getCurrentMeEmailAddress (self):
        """
          Lookup or create a current "me" EmailAddress.
        The "me" EmailAddress is whichever one has the current IMAP default address.
        This method is here for convenient access, so users
        don't need to import Mail.
        """
        from mail import EmailAddress
        return EmailAddress.getCurrentMeEmailAddress (self.itsView)


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
        if hasattr(self, 'sharedIn'):
            for share in self.sharedIn:
                state = ContentItem.READONLY
                if share.mode in ('put', 'both'):
                    return ContentItem.READWRITE

        return state

    sharedState = property(getSharedState)

    def getBasedAttributes(self, attribute):
        """ Determine the schema attributes that affect this attribute
        (which might be a redirectTo or a Calculated attribute) """
        # Recurse to handle redirection if necessary
        attr = self.itsKind.getAttribute(attribute, True)
        if attr is not None:
            redirect = attr.getAspect('redirectTo')
            if redirect is not None:
                item = self
                names = redirect.split('.')
                for name in names[:-1]:
                    item = getattr(item, name)
                return item.getBasedAttributes(names[-1])
        
        # Not redirected. If it's Calculated, see what it's based on; 
        # otherwise, just return a list containing its own name.
        descriptor = getattr(self.__class__, attribute, None)
        return getattr(descriptor, 'basedOn', (attribute,))
    
    def isAttributeModifiable(self, attribute):
        # fast path -- item is unshared; have at it!
        if not self.sharedIn:
            return True

        # slow path -- item is shared; we need to look at all the *inbound*
        # shares this item participates in -- if *any* of those inbound shares
        # are writable, the attribute is modifiable; otherwise, if *all* of
        # those inbound shares are read-only, but none of those shares
        # actually *share* that attribute (i.e., it's being filtered either
        # by sharing cloud or explicit filter), then it's modifiable.
        me = schema.ns("osaf.pim", self.itsView).currentContact.item
        basedAttributeNames = None # we'll look these up if necessary
        isSharedInAnyReadOnlyShares = False
        for share in self.sharedIn:
            if getattr(share, 'sharer', None) is not me:   # inbound share
                if share.mode in ('put', 'both'):   # writable share
                    return True
                else:                               # read-only share
                    # We found a read-only share; this attribute isn't
                    # modifiable if it's one of the attributes shared for
                    # this item in this share. (First, map this attribute to 
                    # the 'real' attributes it depends on, if we haven't yet.)
                    if basedAttributeNames is None:
                        basedAttributeNames = self.getBasedAttributes(attribute)
                    for attr in basedAttributeNames:
                        if attr in share.getSharedAttributes(self):
                            isSharedInAnyReadOnlyShares = True

        return not isSharedInAnyReadOnlyShares


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
      1. it bypasses all the branching, allowing (A, (B,C)) to match 
         ((A, B), C)
      2. it uses the most specialized form when there is no branching,
         thus if D has superKind B, and D has no other superKinds,
         D is more specialized, so we want to use it over B.
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


class Tag(ContentItem):

    schema.kindInfo(
        description =
            "A generic tag object that can be associated with any ContentItem"
    )

    items = schema.Sequence(
        'ContentItem',
        displayName=u'Item',
        description='All the ContentItems associated with this Tag',
        inverse='tags',
        initialValue=[]
    )

    supertags = schema.Sequence(
        'Tag',
        displayName=u'SuperTags',
        description='Allows a tag hierarchy',
        inverse='subtags',
        initialValue=[]
    )

    subtags = schema.Sequence(
        'Tag',
        displayName=u'SubTags',
        description='Allows a tag hierarchy',
        inverse='supertags',
        initialValue=[]
    )


class Project(ContentItem):

    schema.kindInfo(
        description =
            "Users can create projects to help organize their work. Users can "
            "take content items (like tasks and mail messages) and assign "
            "them to different projects.\n\n"
            "Examples:\n"
            '   my "Housewarming Party" project\n'
            "   my department's \"Move to new building\" project\n"
            "   my company's \"Open Seattle Store\" project\n"
    )

    parentProject = schema.One(
        'Project',
        displayName = u'Parent Project',
        doc = 'Projects can be organized into hierarchies. Each project can have one parent.',
        inverse = 'subProjects',
    )
    subProjects = schema.Sequence(
        'Project',
        displayName = u'Sub Projects',
        doc = 'Projects can be organized into hierarchies. Each project can have many sub-projects.',
        inverse = 'parentProject',
    )


class Group(ContentItem):

    schema.kindInfo(
        description =
            "See http://wiki.osafoundation.org/twiki/bin/view/Jungle/CollectionProject\n\n"
            "Issues:\n"
            '   We still need to work out some issues about how '
                '"playlists"/"item collections" are modeled.\n'
            '   We need to find a name for these things.\n'
    )

class UserNotification(ContentItem):

    schema.kindInfo(
        description = "Notifications meant for the user to see"
    )

    items = schema.Sequence(ContentItem, inverse='notifications')

    timestamp = schema.One(schema.DateTimeTZ,
        displayName=_(u"timestamp"),
        doc="DateTime this notification ocurred"
    )

    who = schema.One(schema.Text, initialValue = u"", indexed=True)

    # redirections
    about = schema.One(redirectTo = "displayName")

    date = schema.One(redirectTo = "timestamp")

    def __init__(self, *args, **kw):
        super(UserNotification, self).__init__(*args, **kw)
        if not hasattr(self, 'timestamp'):
            self.timestamp = datetime.now(ICUtzinfo.default)


class Principal(ContentItem):
    # @@@MOR These should be moved out so that authentication can be made
    # more general, but they're here for convenience for now.
    login = schema.One(schema.Text)
    password = schema.One(schema.Text)


    members = schema.Sequence('Principal', initialValue=[], inverse='memberOf')
    memberOf = schema.Sequence('Principal', initialValue=[])

    def isMemberOf(self, pid):

        if self.itsUUID == pid:
            return True

        for member in getattr(self.itsView.findUUID(pid), 'members', []):
            if self.isMemberOf(member.itsUUID):
                return True

        return False
