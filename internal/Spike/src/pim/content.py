"""Basic content model for PIM applications

Classes not included from osaf.contentmodel:

Project, Group
    These classes do not appear to be used anywhere but Chandler's tests.

ItemCollection
    This class is deferred, pending further work on Spike's storage and
    interaction layers.


Attributes not included from ContentItem in osaf.contentmodel:

modifiedOn, lastModified, lastModifiedBy
    These do not appear to be used; some parcels have their own definitions
    but the ones in the base model don't appear used anywhere.

previousStamps
    Spike's stamping model uses an ``actionStamps`` attribute instead, with
    the actual ``ActionStamp`` instances that contain the respective stamps'
    data.

itemCollectionInclusions, itemCollectionExclusions, etc.
    These attributes are not currently used directly, so ItemCollection
    uses anonymous inverse roles instead.

contentsOwner, viewContainer, detailItemOwner
    These attributes are not currently used directly, so blocks will use
    anonymous inverse roles instead.

currentItemOf
    Spike models "currentness" using relationships to a singleton
    ``Application`` object, so content items in general don't need this
    attribute (which isn't currently used in Chandler anyway).

"""

from spike import schema
from datetime import datetime

# XXX temporary hacks
Lob = str
DateTime = datetime
String = basestring

__all__ = [
    'Importance', 'Item', 'Contact', 'Application', 'Stamp',
]


class Importance(schema.Enumeration):
    important = schema.enum("Important")
    normal = schema.enum("Normal")
    fyi = schema.enum("FYI")


class Base(schema.Entity):
    """Base for both items and stamps"""

    displayName = schema.One(basestring,
        compute = repr,
        displayName = "Display Name",
        doc = "The text that should be displayed when viewing this item"
    )

    def __str__(self):
        return self.displayName

    __unicode__ = __str__


class Item(Base):
    """Base class for content items

    A content item (such as a contact, note, photo, etc.)  Content objects are
    user-level items that a user might file, categorize, share, and delete.
    """

    body = schema.One(Lob,
        displayName = "Body",
        doc = """\
        All Content Items may have a body to contain notes.  It's not decided
        yet whether this body would instead contain the payload for resource
        items such as presentations or spreadsheets -- resource items haven't
        been nailed down yet -- but the payload may be different from the notes
        because payload needs to know MIME type, etc."""
    )

    importance = schema.One(Importance, default=Importance.normal,
        displayName = "Importance",
        doc = """\
        Most items are of normal importance (no value need be show), however
        some things may be flagged either highly important or merely 'fyi'.
        This attribute is also used in the mail schema, so we shouldn't make
        any changes here that would break e-mail interoperability features."""
    )

    creator = schema.One(
        displayName = "Created By",
        doc = "Link to the contact who created the item."
        # inverse = Contact.itemsCreated
    )

    isPrivate = schema.One(bool, default=False)

    createdOn = schema.One(DateTime,
        compute = lambda self: DateTime.now(),
        displayName = "Created On",
        doc = "Date/time this item was created"
    )

    actionStamps = schema.Many(
        displayName = "Action Stamps",
        doc =
        "All action stamps that this item has ever had, active or inactive."
    )

    @actionStamps.loader
    def _loadStamps(self,linkset):
        linkset.addValidator(self._crippleStamps)

    def _crippleStamps(self,event):
        """Prevent use of more than one stamp of a given type"""

        for stamp in event.added:
            cls = stamp.__class__
            for old in event.sender:
                if old.__class__ is cls and old not in event.added:
                    raise TypeError(
                        "Only one %r stamp allowed per content item" %
                        cls.__name__
                    )


    def get_stamp(self,type):
        """Return stamp of `type` (active or inactive), or ``None``"""
        for stamp in self.actionStamps:
            if stamp.__class__ is type:
                return stamp

    def stamp(self,type):
        """Return activated (and possibly new) stamp of `type`"""

        stamp = self.get_stamp(type)
        if stamp is None:
            stamp = type(contentItem=self)

        stamp.isActive = True
        return stamp

    def unstamp(self,type):
        """Deactivate any existing stamp of `type`"""
        stamp = self.get_stamp(type)
        if stamp is not None:
            stamp.isActive = False


class Stamp(Base):
    """Base class for action stamps like mail, tasks, calendar events, etc."""

    isActive = schema.One(bool,
        default=True,
        displayName = "Active?",
        doc="True if contentItem is currently stamped with this stamp"
    )

    contentItem = schema.One(Item,
        displayName = "Content Item",
        doc = "The content item that this stamp is attached to",
        inverse = Item.actionStamps
    )

    @Base.displayName.loader
    def _loadName(self,linkset):
        try:
            return Base.displayName.of(self.contentItem)
        except AttributeError:
            pass

    @contentItem.loader
    def _loadItem(self,linkset):
        linkset.addValidator(self._noRemove)

    def _noRemove(self,event):
        if event.removed:
            raise TypeError("A stamp's content item cannot be changed")


class Contact(Item):
    """An entry in an address book

    Typically represents either a person or a company.

    Issues: We might want to keep track of lots of sharing information like
    'Permissions I've given them', 'Items of mine they've subscribed to',
    'Items of theirs I've subscribed to', etc.
    """

    @Base.displayName.loader
    def _loadName(self,linkset):
        """Use a contact's email address as its displayName"""
        return Contact.emailAddress.of(self)

    firstName = schema.One(String, default="")
    lastName = schema.One(String, default="")

    #contactName = schema.One(String)
    #@contactName.loader
    #def _loadContactName(self,linkset):
    #   compute contactName from first/last name


    emailAddress = schema.One(String, default="")   # XXX

    itemsCreated = schema.Many(Item,
        displayName = "Items Created",
        doc = "Content items created by this user.",
        inverse = Item.creator
    )


class Application(Base):
    user = schema.One(Contact,
        displayName = "Application User",
        doc = "The Contact that represents the application's user",
    )

