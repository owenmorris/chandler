""" Classes used for Contacts parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import application.Globals as Globals
import mx.DateTime as DateTime

class ContactsParcel(application.Parcel.Parcel):
    def onItemLoad(self):
        super(ContactsParcel, self).onItemLoad()
        self._setUUIDs()

    def startupParcel(self):
        super(ContactsParcel, self).startupParcel()
        self._setUUIDs()

    def _setUUIDs(self):
        contactKind = self['Contact']
        ContactsParcel.contactKindID = contactKind.itsUUID

        contactNameKind = self['ContactName']
        ContactsParcel.contactNameKindID = contactNameKind.itsUUID

    def getContactKind(cls):
        assert cls.contactKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.contactKindID]

    getContactKind = classmethod(getContactKind)

    def getContactNameKind(cls):
        assert cls.contactNameKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.contactNameKindID]

    getContactNameKind = classmethod(getContactNameKind)

    contactKindID = None
    contactNameKindID = None

class Contact(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = ContactsParcel.getContactKind()
        super (Contact, self).__init__(name, parent, kind)

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

    def getCurrentMeContact(cls):
        """ Lookup the current "me" Contact """

        # For now, just hardcode a contact to use:
        return \
         Globals.repository.findPath("//parcels/osaf/views/main/MeContact")

    getCurrentMeContact = classmethod(getCurrentMeContact)

    def __str__(self):
        """ User readable string version of this address. """

        if self.isStale():
            return super(Contact, self).__str__()
            # Stale items shouldn't go through the code below

        try:
            if self.contactName is not None:
                value = self.contactName.firstName + ' ' + \
                 self.contactName.lastName
        except:
            value = self.getItemDisplayName()

        return value

class ContactName(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getContactNameKind()
        super (ContactName, self).__init__(name, parent, kind)
