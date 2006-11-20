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

""" Classes used for Contacts parcel kinds
"""

__all__ = ['ContactName', 'Contact']

from osaf.pim import items
from application import schema
from i18n import ChandlerMessageFactory as _


class ContactName(items.ContentItem):
    "A very simple (and incomplete) representation of a person's name"

    firstName = schema.One(schema.Text, initialValue=u"", indexed=True)
    lastName  = schema.One(schema.Text, initialValue=u"", indexed=True)
    contact = schema.One()

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [firstName, lastName]
        )
    )


class Contact(items.ContentItem):
    """
    An entry in an address book.

    Typically represents either a person or a company.

    Issues: We might want to keep track of lots of sharing information like
    'Permissions I've given them', 'Items of mine they've subscribed to',
    'Items of theirs I've subscribed to', etc.
    """
    itemsCreated = schema.Sequence(
        doc = "List of content items created by this user.",
        inverse=items.ContentItem.creator,
    )

    contactName = schema.One(
        inverse=ContactName.contact, initialValue=None
    )

    emailAddress = schema.One(schema.Text,
        initialValue = u"",
        indexed = True,
    )

    itemsLastModified = schema.Sequence(
        items.ContentItem,
        doc="List of content items last modified by this user.",
        inverse=items.ContentItem.lastModifiedBy
    )

    requestedTasks = schema.Sequence(
        doc="List of tasks requested by this user.",
    ) # inverse of tasks.TaskStamp.requestor

    taskRequests= schema.Sequence(
        doc="List of tasks requested for this user.",
    ) # inverse of tasks.TaskStamp.requestee

    organizedEvents= schema.Sequence(
        doc="List of events this user has organized.",
    ) # inverse of EventStamp.organizer

    participatingEvents= schema.Sequence(
        doc="List of events this user is a participant.",
    ) # inverse of EventStamp.participants

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [emailAddress],
            byCloud = [contactName]
        )
    )

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

    def getContactForEmailAddress(cls, view, address):
        """ Given an email address string, find (or create) a matching contact.

        @param view: The repository view object
        @type view: L{repository.persistence.RepositoryView}
        @param address: An email address to use for looking up a contact
        @type address: string
        @return: A Contact
        """

        for item in cls.iterItems(view):
            if item.emailAddress == address:
                return item # Just return the first match

        # Need to create a new Contact
        contact = Contact(itsView=view)
        contact.emailAddress = address
        contact.contactName = None
        return contact

    getContactForEmailAddress = classmethod(getContactForEmailAddress)
