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

import time
from datetime import datetime

from application import schema
from repository.schema.Kind import Kind
import repository.item.Item as Item
from chandlerdb.item.ItemError import NoLocalValueForAttributeError
import logging
from i18n import ChandlerMessageFactory as _
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
    values = { "now": 0 , "later": 5000, "done": 10000 }

triageStatusNames = { TriageEnum.now: _(u"Now"), 
                      TriageEnum.later: _(u"Later"), 
                      TriageEnum.done: _(u"Done") 
                    }
def getTriageStatusName(value):
    return triageStatusNames[value]

# Bug 6525: the clicking sequence isn't the sort order
triageStatusClickSequence = { TriageEnum.now: TriageEnum.done, 
                              TriageEnum.done: TriageEnum.later, 
                              TriageEnum.later: TriageEnum.now }
def getNextTriageStatus(value):
    return triageStatusClickSequence[value]
    
# For use in indexing time-related attributes. We only use this for 
# reminderFireTime here, but CalendarEventMixin uses this a lot more...
def cmpTimeAttribute(item, other, attr, useTZ=True):
    """Compare item and self.attr, ignore timezones if useTZ is False."""
    otherTime = getattr(other, attr, None)
    itemTime = getattr(item, attr, None)

    if otherTime is None:
        if itemTime is None:
            # both attributes are None, so item and other compare as equal
            return 0
        else:
            return -1
    elif not useTZ:
        otherTime = otherTime.replace(tzinfo = None)

    if itemTime is None:
        return 1
    elif not useTZ:
        itemTime = itemTime.replace(tzinfo = None)

    return cmp(itemTime, otherTime)


    
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
        indexed = True,
        defaultValue = u"",
        doc="All Content Items may have a body to contain notes.  It's "
            "not decided yet whether this body would instead contain the "
            "payload for resource items such as presentations or "
            "spreadsheets -- resource items haven't been nailed down "
            "yet -- but the payload may be different from the notes because "
            "payload needs to know MIME type, etc."
    )

    creator = schema.One(
        # Contact
        doc="Link to the contact who created the item."
    )

    modifiedOn = schema.One(
        schema.DateTimeTZ,
        doc="DateTime this item was last modified"
    )

    lastModifiedBy = schema.One(
        # Contact
        doc="Link to the contact who last modified the item.",
    )

    importance = schema.One(ImportanceEnum,
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

    createdOn = schema.One(
        schema.DateTimeTZ,
        doc="DateTime this item was created"
    )

    contentsOwner = schema.Sequence(
        "osaf.framework.blocks.Block.Block", inverse="contents"
    )

    tags = schema.Sequence(
        'Tag',
        description='All the Tags associated with this ContentItem',
        inverse='items',
        initialValue=[]
    )

    notifications = schema.Sequence('UserNotification',
        description='All notifications for this ContentItem',
        initialValue=[]
    )

    triageStatus = schema.One(TriageEnum, indexed=True,
                              defaultValue=TriageEnum.now)
    
    # For sorting by how recently triageStatus changed, we keep this attribute,
    # which is the time (in seconds) of the last change, negated for proper 
    # order. It's updated automatically when triageStatus is changed by 
    # setTriageStatusChanged, below.
    triageStatusChanged = schema.One(schema.Float)
    
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

    # ContentItem instances can be excluded by AppCollections
    excludedBy = schema.Sequence(otherName='collectionExclusions')

    # ContentItem instances can be put into SmartCollections (which define
    # the other end of this biref)
    appearsIn = schema.Sequence()

    # The date used for sorting the Date column
    relevantDate = schema.One(schema.DateTimeTZ)
    relevantDateSource = schema.One(schema.Importable)
    
    schema.addClouds(
        sharing = schema.Cloud("displayName", body, createdOn, 'tags',
                               "description", lastModifiedBy, triageStatus,
                               triageStatusChanged),
        copying = schema.Cloud()
    )

    def __init__(self, *args, **kw):
        super(ContentItem, self).__init__(*args, **kw)
        now = None
        if not hasattr(self, 'createdOn'):
            now = datetime.now(ICUtzinfo.default)
            self.createdOn = now
        if not hasattr(self, 'triageStatusChanged'):
            self.setTriageStatusChanged(when=now)
            
    def __str__ (self):
        if self.isStale():
            return super(ContentItem, self).__str__()
            # Stale items can't access their attributes

        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        if self.isStale():
            return super(ContentItem, self).__unicode__()

        return self.getItemDisplayName()

    def InitOutgoingAttributes(self):
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
            super(ContentItem, self).ExportItemData(clipboardHandler)
        except AttributeError:
            pass

        # Let the clipboard handler know we've got a ContentItem to export
        clipboardHandler.ExportItemFormat(self, 'ContentItem')
        
    def onItemDelete(self, view, deferring):
        # Hook for stamp deletion ...
        from stamping import Stamp
        for stampObject in Stamp(self).stamps:
            onItemDelete = getattr(stampObject, 'onItemDelete', None)
            if onItemDelete is not None:
                onItemDelete(view, deferring)
        
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
    
    def addRelevantDates(self, dates):
        from osaf.pim.reminders import Remindable
        Remindable(self).addRelevantDates(dates)

    def updateRelevantDate(self, op, attr):
        # Update the relevant date. This could be a lot smarter.
        if self.isDeleted():
            return
        logger.debug("Collecting relevant dates for %r %s", self, self)
        dates = []
        self.addRelevantDates(dates)
        dates = filter(lambda x: x[0], dates)
        dateCount = len(dates)
        if dateCount == 0:
            # No relevant dates? Eventually, we'll use lastModified; for now
            # just delete the value.
            if hasattr(self, 'relevantDate'): 
                del self.relevantDate
                self.relevantDateSource = 'None'
            logger.debug("No relevant date for %r %s", self, self)
            return
        elif dateCount == 1:
            # We have exactly one date; it doesn't matter whether it's in
            # the future or the past -- just use it.
            result = dates[0]
        else:
            # More than one: Use the first one after now if we have one, else
            # the last one before now.
            nowTuple = (datetime.now(tz=ICUtzinfo.default), 'now')
            dates.append(nowTuple)
            dates.sort()
            nowIndex = dates.index(nowTuple)
            try:
                result = dates[nowIndex+1]
            except IndexError:
                result = dates[nowIndex-1]
                
        logger.debug("Relevant date for %r %s is %s", self, self, result)
        assert result[0] is not None
        self.relevantDate, self.relevantDateSource = result
        
    @schema.observer(lastModified)
    def onLastModifiedChanged(self, op, attr):
        self.updateRelevantDate(op, attr)

    @schema.observer(triageStatus)
    def setTriageStatusChanged(self, op='set', attribute=None, when=None):
        """
        Update triageStatusChanged, which is the number of seconds since the
        epoch that triageStatus was changed, negated for proper sort order.
        As a schema.observer of triageStatus, it's called automatically, but
        can also be called directly to set a specific time:
           item.setTriageStatusChanged(when=someDateTime)
        """
        when = when or datetime.now(tz=ICUtzinfo.default)
        self.triageStatusChanged = time.mktime(when.utctimetuple())
        logger.debug("%s.triageStatus = %s @ %s", self, getattr(self, 'triageStatus', None), when)

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
        try:
            basedOn = descriptor.basedOn
        except AttributeError:
            return (attribute,)
        else:
            return tuple(desc.name for desc in basedOn)
            


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

class Tag(ContentItem):

    schema.kindInfo(
        description =
            "A generic tag object that can be associated with any ContentItem"
    )

    items = schema.Sequence(
        'ContentItem',
        description='All the ContentItems associated with this Tag',
        inverse='tags',
        initialValue=[]
    )

    supertags = schema.Sequence(
        'Tag',
        description='Allows a tag hierarchy',
        inverse='subtags',
        initialValue=[]
    )

    subtags = schema.Sequence(
        'Tag',
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
        doc = 'Projects can be organized into hierarchies. Each project can have one parent.',
        inverse = 'subProjects',
    )
    subProjects = schema.Sequence(
        'Project',
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
        doc="DateTime this notification ocurred"
    )

    who = schema.One(schema.Text, initialValue = u"", indexed=True)

    # redirections
    about = schema.One(redirectTo = "displayName")

    def __init__(self, *args, **kw):
        super(UserNotification, self).__init__(*args, **kw)
        if not hasattr(self, 'timestamp'):
            self.timestamp = datetime.now(ICUtzinfo.default)

    @schema.observer(timestamp)
    def onTimestampChanged(self, op, attr):
        self.updateRelevantDate(op, attr)

    def addRelevantDates(self, dates):
        super(UserNotification, self).addRelevantDates(dates)
        timestamp = getattr(self, 'timestamp', None)
        if timestamp is not None:
            dates.append((timestamp, 'timestamp'))


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
