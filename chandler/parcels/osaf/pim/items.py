#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from application import schema
from repository.schema.Kind import Kind
from chandlerdb.util.c import Empty, Nil
from osaf.pim.reminders import isDead
from osaf.pim.triage import Triageable
import logging
from i18n import ChandlerMessageFactory as _
from osaf import messages

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

class Modification(schema.Enumeration):
    """
    Enumeration of the types of modification that are part of
    the edit/update workflows (a.k.a. "Stamping Storyboards")
    """
    values = { "edited":100, "queued":200, "sent":300, "updated":400,
               "created":500 }

class ContentItem(Triageable):
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
    isProxy = False
    
    displayName = schema.One(schema.Text,
        defaultValue = u"",
        indexed=True)
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

    modifiedFlags = schema.Many(
        Modification,
        defaultValue=Empty,
        description='Used to track the modification state of the item'
    )

    lastModified = schema.One(
        schema.DateTimeTZ,
        doc="DateTime (including timezone) this item was last modified",
        defaultValue=None,
    )

    lastModifiedBy = schema.One(
        doc="Link to the EmailAddress who last modified the item.",
        defaultValue=None
    )

    lastModification = schema.One(
        Modification,
        doc="What the last modification was.",
        defaultValue=Modification.created,
    )
    
    BYLINE_FORMATS = {
        Modification.created: (
            _(u"created by %(user)s on %(date)s %(tz)s"),
            _(u"created on %(date)s %(tz)s"),
        ),
        Modification.edited: (
            _(u"edited by %(user)s on %(date)s %(tz)s"),
            _(u"edited on %(date)s %(tz)s"),
        ),
        Modification.updated: (
            _(u"updated by %(user)s on %(date)s %(tz)s"),
            _(u"updated on %(date)s %(tz)s"),
        ),
        Modification.sent: (
            _(u"sent by %(user)s on %(date)s %(tz)s"),
            _(u"sent on %(date)s %(tz)s"),
        ),
        Modification.queued: (
            _(u"queued by %(user)s on %(date)s %(tz)s"),
            _(u"queued on %(date)s %(tz)s"),
        ),
    }

    def getByline(self):
        lastModification = self.lastModification
        assert lastModification in self.BYLINE_FORMATS
        
        fmt, noUserFmt = self.BYLINE_FORMATS[lastModification]

        # fall back to createdOn
        view = self.itsView
        lastModified = (self.lastModified or getattr(self, 'createdOn', None) or
                        datetime.now(view.tzinfo.default))

        shortDateTimeFormat = schema.importString("osaf.pim.shortDateTimeFormat")
        date = shortDateTimeFormat.format(view, lastModified)

        tzPrefs = schema.ns('osaf.pim', view).TimezonePrefs
        if tzPrefs.showUI:
            from calendar.TimeZone import shortTZ            
            tzName = shortTZ(view, lastModified)
        else:
            tzName = u''
            
        user = self.lastModifiedBy
        if user:
            result = fmt % dict(user=user.getLabel(), date=date, tz=tzName)
        else:
            result = noUserFmt % dict(date=date, tz=tzName)
        return result.strip()
        
    error = schema.One(
        schema.Text,
        doc="A user-visible string containing the last error that occurred. "
            "Typically, this should be set by the sharing or email layers when "
            "a conflict or delivery problem occurs.",
        defaultValue=None
    )

    byline = schema.Calculated(
        schema.Text,
        basedOn=(modifiedFlags, lastModified, lastModification, lastModifiedBy),
        fget=getByline
    )
    
    importance = schema.One(ImportanceEnum,
        doc="Most items are of normal importance (no value need be shown), "
            "however some things may be flagged either highly important or "
            "merely 'fyi'. This attribute is also used in the mail schema, so "
            "we shouldn't make any changes here that would break e-mail "
            "interoperability features.",
        defaultValue="normal",
    )

    mine = schema.One(schema.Boolean, defaultValue=True)

    private = schema.One(schema.Boolean, defaultValue=False)

    read = schema.One(
        schema.Boolean,
        defaultValue=False,
        doc="A flag indicating whether the this item has "
            "been 'viewed' by the user"
    )

    needsReply = schema.One(
        schema.Boolean,
        defaultValue=False,
        doc="A flag indicating that the user wants to reply to this item"
    )


    createdOn = schema.One(
        schema.DateTimeTZ,
        doc="DateTime this item was created"
    )

    # ContentItem instances can be put into ListCollections and AppCollections
    collections = schema.Sequence(notify=True) # inverse=collections.inclusions

    # ContentItem instances can be excluded by AppCollections
    excludedBy = schema.Sequence()

    # ContentItem instances can be put into SmartCollections (which define
    # the other end of this biref)
    appearsIn = schema.Sequence()

    # The date used for sorting the Date column
    displayDate = schema.One(schema.DateTimeTZ, indexed=True)
    displayDateSource = schema.One(schema.Importable)

    # The value displayed (and sorted) for the Who column.
    displayWho = schema.One(schema.Text, indexed=True)
    displayWhoSource = schema.One(schema.Importable)

    schema.addClouds(
        sharing = schema.Cloud(
            literal = ["displayName", body, createdOn, "description"],
            byValue = [lastModifiedBy]
        ),
        copying = schema.Cloud()
    )

    schema.initialValues(
        createdOn = lambda self: datetime.now(self.itsView.tzinfo.default)
    )
    
    def __str__ (self):
        if self.isStale():
            return super(ContentItem, self).__str__()
            # Stale items can't access their attributes

        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        if self.isStale():
            return super(ContentItem, self).__unicode__()

        return unicode(getattr(self, 'displayName', self.itsName) or
                       self.itsUUID.str64())

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        
        super(ContentItem, self).InitOutgoingAttributes ()

        # default the displayName
        self.displayName = messages.UNTITLED
        
        if not self.hasLocalAttributeValue('lastModifiedBy'):
            self.lastModifiedBy = self.getMyModifiedByAddress()

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
        super(ContentItem, self).onItemDelete(view, deferring)

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

        The special mine collection behavior that removed items should remain in
        the Dashboard is implemented here.

        """
        self._prepareToRemoveFromCollection(collection)
        collection.remove(self)

    def _prepareToRemoveFromCollection(self, collection):
        """
        If the collection is a mine collection and the item doesn't exist in any
        other 'mine' collections, manually add it to 'all' to keep the item
        'mine'.

        We don't want to do this blindly though, or all's inclusions will get
        unnecessarily full.

        We also don't want to remove collection from mine.sources. That will
        cause a notification storm as items temporarily leave and re-enter
        being 'mine'.
        
        """
        pim_ns = schema.ns('osaf.pim', self.itsView)
        mine = pim_ns.mine
        allCollection = pim_ns.allCollection

        if collection in mine.sources:
            for otherCollection in self.appearsIn:
                if otherCollection is collection:
                    continue
    
                if otherCollection in mine.sources:
                    # we found it in another 'mine'
                    break
            else:
                # we didn't find it in a 'mine' Collection
                self.collections.add(allCollection)

    def getMembershipItem(self):
        """ Get the item that should be used to test for membership
        tests i.e. if item in collection: should be if
        item.getMembershipItem() in collection

        For most items, this is just itself, but for recurring
        events, this method is intercepted by a proxy.
        """
        return self

    def changeEditState(self, modType=Modification.edited, who=None,
                        when=None):
        """
        @param modType: What kind of modification you are making. Used to set
                        the value of C{self.lastModification}.
        @type modType: C{Modification}
        
        @param who: May be C{None}, which is interpreted as an anonymous
                    user (e.g. a "drive-by" sharing user).
                    Used to set the value of {self.lastModifiedBy}.
        @type who: C{EmailAddress}
        
        @param when: The date&time of this change. Used to set the value
                     of C{self.lastModified}. The default, C{None}, sets
                     the 
        @type when: C{datetime}
        """
        
        logger.debug("ContentItem.changeEditState() self=%s view=%s modType=%s who=%s when=%s", self, self.itsView, modType, who, when)
        
        currentModFlags = self.modifiedFlags
        
        if (modType == Modification.edited and
            not self.hasLocalAttributeValue('lastModification', None) and
            not getattr(self, 'inheritFrom', self).hasLocalAttributeValue('lastModification')):
            # skip edits until the item is explicitly marked created

            return

        if modType == Modification.sent:
            if Modification.sent in currentModFlags:
                #raise ValueError, "You can't send an item twice"
                pass
            elif Modification.queued in currentModFlags:
                currentModFlags.remove(Modification.queued)
        elif modType == Modification.updated:
            #XXX Brian K: an update can occur with out a send.
            # Case user a sends a item to user b (state == sent)
            #      user a edits item to user b and adds user c (state == update).
            # For user c the state of sent was never seen.

            #if not Modification.sent in currentModFlags:
            #    raise ValueError, "You can't update an item till it's been sent"

            if Modification.queued in currentModFlags:
                currentModFlags.remove(Modification.queued)

        # Clear the edited flag and error on send/update/queue
        if (modType in (Modification.sent, Modification.updated, 
                        Modification.queued)):
            if Modification.edited in currentModFlags:
                currentModFlags.remove(Modification.edited)
            del self.error

        if not currentModFlags:
            self.modifiedFlags = set([modType])
        else:
            currentModFlags.add(modType)
        self.lastModification = modType
        self.lastModified = when or datetime.now(self.itsView.tzinfo.default)
        self.lastModifiedBy = who # None => me

    """
    ACCESSORS

    Accessors for Content Item attributes
    """
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
        This method is here for convenient access, so users
        don't need to import Mail.
        """
        import mail
        return mail.getCurrentMeEmailAddress (self.itsView)

    def getMyModifiedByAddress(self):
        """
        Get an EmailAddress that represents the local user, for
        storing in lastModifiedBy after a local change.
        """
        me = self.getCurrentMeEmailAddress()
        if not me: # Email not configured...
            # Get the user name associated with the default sharing account
            import osaf.sharing # hmm, this import seems wrong
            sharingAccount = osaf.sharing.getDefaultAccount(self.itsView)
            if sharingAccount is not None:
                import mail
                me = mail.EmailAddress.getEmailAddress(self.itsView,
                    sharingAccount.username)
        return me

    def _updateCommonAttribute(self, attributeName, sourceAttributeName,
                               collectorMethodName, args=()):
        """
        Mechanism for coordinating updates to a common-display field
        (like displayWho and displayDate, but not displayName for now).
        """
        if self.isDeleted():
            return
        logger.debug("Collecting relevant %ss for %r %s",
                     attributeName, self, self)
                     
        collectorMethod = getattr(type(self), collectorMethodName)

        # Collect possible values. The collector method adds tuples to the
        # contenders list; each tuple starts with a value to sort by, and
        # ends with the attribute value to assign and the name of the attribute
        # it came from (which will be used later to pick a displayable string
        # to describe the source of the value).
        #
        # Examples: if we sort by the attribute value, only two values are
        # needed in the tuple: eg, (aDate, 'dateField). If the picking happens
        # based on an additional value (or values), the sort value(s) come
        # before the attribute value: eg (1, 'me@ex.com', 'to'),
        # (2, 'you@ex.com', 'from'). This works because sort sorts by the
        # values in order, and we access the attribute value and name using
        # negative indexes (so contender[-2] is the value, contender[-1] is
        # the name).
        contenders = []
        collectorMethod(self, contenders, *args)

        # Now that we have the contenders, pick one.
        contenderCount = len(contenders)
        if contenderCount == 0:
            # No contenders: delete the value
            if hasattr(self, attributeName):
                delattr(self, attributeName)
            if hasattr(self, sourceAttributeName):
                delattr(self, sourceAttributeName)
            logger.debug("No relevant %s for %r %s", attributeName, self, self)
            return
        
        if contenderCount > 1:
            # We have more than one possibility: sort, then we'll use the first one.
            contenders.sort()        
        result = contenders[0]
        logger.debug("Relevant %s for %r %s is %s", attributeName, self, self, result)
        assert result[-2] is not None
        setattr(self, attributeName, result[-2])
        setattr(self, sourceAttributeName, result[-1])
        
        if getattr(self, 'inheritFrom', None) is None:
            for item in getattr(self, 'inheritTo', []):
                item._updateCommonAttribute(attributeName, sourceAttributeName,
                               collectorMethodName, args)

    def addDisplayWhos(self, whos):
        pass

    def updateDisplayWho(self, op, attr):
        self._updateCommonAttribute('displayWho', 'displayWhoSource',
                                    'addDisplayWhos')

    def addDisplayDates(self, dates, now):
        super(ContentItem, self).addDisplayDates(dates, now)
        # Add our creation and last-mod dates, if they exist.
        for importance, attr in (999, "lastModified"), (1000, "createdOn"):
            v = getattr(self, attr, None)
            if v is not None:
                dates.append((importance, v, attr))
        
    def updateDisplayDate(self, op, attr):
        now = datetime.now(tz=self.itsView.tzinfo.default)
        self._updateCommonAttribute('displayDate', 'displayDateSource',
                                    'addDisplayDates', [now])

    @schema.observer(modifiedFlags, lastModified, createdOn)
    def onCreatedOrLastModifiedChanged(self, op, attr):
        self.updateDisplayDate(op, attr)

    @schema.observer(modifiedFlags, lastModification, lastModifiedBy)
    def onModificationChange(self, op, name):
        # CommunicationStatus might have changed
        self.updateDisplayWho(op, name)

    @schema.observer(error)
    def onErrorChanged(self, op, attr):
        if getattr(self, 'error', None) is not None:
            self.setTriageStatus(None, popToNow=True, force=True)


    def getBasedAttributes(self, attribute):
        """ Determine the schema attributes that affect this attribute
        (which might be a Calculated attribute) """
        # If it's Calculated, see what it's based on;
        # otherwise, just return a list containing its own name.
        descriptor = getattr(self.__class__, attribute, None)
        try:
            basedOn = descriptor.basedOn
        except AttributeError:
            return (attribute,)
        else:
            return tuple(desc.name for desc in basedOn)



    def isAttributeModifiable(self, attribute):
        """ Determine if an item's attribute is modifiable based on the
            shares it's in """
        from osaf.sharing import isReadOnly
        return not isReadOnly(self)

        #from stamping import Stamp
        #for stampObject in Stamp(self).stamps:
            #isAttrMod = getattr(stampObject, 'isAttributeModifiable', None)
            #if isAttrMod is not None:
                #if not isAttrMod(attribute):
                    #return False
        #return True


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
        doc = 'Projects can be organized into hierarchies. Each project can have one parent.',
    )
    subProjects = schema.Sequence(
        doc = 'Projects can be organized into hierarchies. Each project can have many sub-projects.',
        inverse = parentProject,
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

class Principal(ContentItem):
    # @@@MOR These should be moved out so that authentication can be made
    # more general, but they're here for convenience for now.
    login = schema.One(schema.Text)
    password = schema.One(schema.Text)


    members = schema.Sequence(initialValue=[])
    memberOf = schema.Sequence(initialValue=[], inverse=members)

    def isMemberOf(self, pid):

        if self.itsUUID == pid:
            return True

        for member in getattr(self.itsView.findUUID(pid), 'members', []):
            if self.isMemberOf(member.itsUUID):
                return True

        return False
