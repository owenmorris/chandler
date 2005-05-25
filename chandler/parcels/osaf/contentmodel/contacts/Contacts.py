""" Classes used for Contacts parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.contentmodel.ContentModel as ContentModel
import repository.query.Query as Query
from repository.item.Query import KindQuery

class Contact(ContentModel.ContentItem):

    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/contacts/Contact"


    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (Contact, self).__init__(name, parent, kind, view)

        # If I didn't get assigned a creator, then I must be the "me" contact
        # and I want to be my own creator:
        if self.creator is None:
            self.creator = self

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(Contact, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.contactName = ContactName()
        self.contactName.firstName = ''
        self.contactName.lastName = ''

    def getCurrentMeContact(cls, view):
        """ Lookup the current "me" Contact """

        # cls.meContactID caches the Contact representing the user.  One will
        # be created if it doesn't yet exist.

        if cls.meContactID is not None:
            me = view.findUUID(cls.meContactID)
            if me is not None:
                return me
            # Our cached UUID is invalid
            cls.meContactID is None

        parent = ContentModel.ContentModel.getContentItemParent(view)
        me = parent.getItemChild("me")
        if me is None:
            me = Contact(name="me", parent=parent)
            me.displayName = "Me"
            me.contactName = ContactName(parent=me)
            me.contactName.firstName = "Chandler"
            me.contactName.lastName = "User"

        cls.meContactID = me.itsUUID

        return me

    getCurrentMeContact = classmethod(getCurrentMeContact)

    # Cache "me" for fast lookup; used by getCurrentMeContact()
    meContactID = None


    def getContactForEmailAddress(cls, view, address):
        """ Given an email address string, find (or create) a matching contact.

        @param view: The repository view object
        @type view: L{repository.persistence.RepositoryView}
        @param address: An email address to use for looking up a contact
        @type address: string
        @return: A Contact
        """

        """ @@@MOR, convert this section to use Query; I tried briefly but
        wasn't successful, and it's just using KindQuery right now:

        query = Query.Query(view, parent=view.findPath("//userdata"), queryString="") # @@@MOR Move this to a singleton

        queryString = "for i in '//parcels/osaf/contentmodel/contacts/Contact' where i.emailAddress == $0"
        query.args = { 0 : address }
        query.execute()
        for item in query:
        """

        for item in KindQuery().run([view.findPath("//parcels/osaf/contentmodel/contacts/Contact")]):
            if item.emailAddress == address:
                return item # Just return the first match

        # Need to create a new Contact
        contact = Contact(view=view)
        contact.emailAddress = address
        contact.contactName = None
        return contact

    getContactForEmailAddress = classmethod(getContactForEmailAddress)

    def __str__(self):
        """ User readable string version of this address. """

        if self.isStale():
            return super(Contact, self).__str__()
            # Stale items shouldn't go through the code below

        value = self.getItemDisplayName()

        return value

class ContactName(ContentModel.ContentItem):

    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/contacts/ContactName"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (ContactName, self).__init__(name, parent, kind, view)
