__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

import osaf.framework.blocks.ControlBlocks as ControlBlocks

import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.contacts.Contacts as Contacts

import repository.item.Query as Query

class ContentItemDetail(ControlBlocks.ItemDetail):
    # @@@ This class is mostly scaffolding
    # (+) We won't use HTML in the long run, but will use blocks
    # (+) Need a data driven way to alternate the type of item detail

    def getHTMLText(self, item):

        HTMLText = "<html><body>"
        
        kind = item.itsKind
        if kind is Globals.repository.findPath("//parcels/osaf/contentmodel/calendar/CalendarEvent"):
            HTMLText += "<b>Headline: </b> %s<br>" % item.about
            HTMLText += "<b>Attendees: </b> %s<br>" % item.who
            HTMLText += "<b>Date: </b> %s<br>" % item.date
            HTMLText += "<b>Duration: </b> %s<br>" % item.duration
        elif kind is Globals.repository.findPath("//parcels/osaf/contentmodel/Note"):
            HTMLText += "<b>Title: </b> %s<br>" % item.about
        elif kind is Globals.repository.findPath("//parcels/osaf/contentmodel/contacts/Contact"):
            HTMLText += "<b>First name: </b> %s<br>" % item.contactName.firstName
            HTMLText += "<b>Last name: </b> %s<br>" % item.contactName.lastName
            for phone in item.homeSection.phoneNumbers:
                HTMLText += "<b>Home phone: </b> %s<br>" % phone.phoneNumber
            for phone in item.workSection.phoneNumbers:
                HTMLText += "<b>Work phone: </b> %s<br>" % phone.phoneNumber
            for email in item.homeSection.emailAddresses:
                HTMLText += "<b>Home email: </b> %s<br>" % email.emailAddress
            for email in item.workSection.emailAddresses:
                HTMLText += "<b>Work email: </b> %s<br>" % email.emailAddress
        else:
            HTMLText += "BOGUS ITEM"
                
        HTMLText += "</body></html>"
        Contacts
        return HTMLText
