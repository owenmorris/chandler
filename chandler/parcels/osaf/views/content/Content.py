__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

import OSAF.framework.blocks.ControlBlocks as ControlBlocks

import OSAF.contentmodel.calendar.Calendar as Calendar
import OSAF.contentmodel.notes.Notes as Notes
import OSAF.contentmodel.contacts.Contacts as Contacts

import repository.item.Query as Query

class ContentItemDetail(ControlBlocks.ItemDetail):
    # @@@ This class is mostly scaffolding
    # (+) We won't use HTML in the long run, but will use blocks
    # (+) Need a data driven way to alternate the type of item detail

    def getHTMLText(self, item):

        HTMLText = "<html><body>"
        
        kind = item.kind
        if kind is Globals.repository.find ("//parcels/OSAF/contentmodel/calendar/CalendarEvent"):
            HTMLText += "<b>Headline: </b> %s<br>" % item.getAbout()
            HTMLText += "<b>Attendees: </b> %s<br>" % item.getWho()
            HTMLText += "<b>Date: </b> %s<br>" % item.getDate()
            HTMLText += "<b>Duration: </b> %s<br>" % item.duration
        elif kind is Globals.repository.find ("//parcels/OSAF/contentmodel/notes/Note"):
            HTMLText += "<b>Title: </b> %s<br>" % item.getAbout()
        elif kind is Globals.repository.find ("//parcels/OSAF/contentmodel/contacts/Contact"):
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


class CalendarListDelegate (ControlBlocks.ListDelegate):
    def ElementText (self, index, column):
        counterpart = Globals.repository.find (self.counterpartUUID)
        result = counterpart.contentSpec.indexResult (index) 
        if column == 0:
            return result.getWho()
        elif column == 1:
            return result.getAbout()
        elif column == 2:
            return result.getDate()
        elif __debug__:
            assert False, "Bad column"
        return ""


class ContactListDelegate(ControlBlocks.ListDelegate):
    def valOrEmpty(self, element, attrList):
        if len(attrList)==0:
            return element
        attr=attrList[0]
        if element.hasAttributeValue(attr):
            if element.getAttributeAspect(attr, "cardinality") == "single":
                r=element.getAttributeValue(attr)
            else:
                r=element.getAttributeValue(attr).first()
            return self.valOrEmpty(r, attrList[1:])
        else:
            return ""

    def ElementText (self, index, column): 
        counterpart = Globals.repository.find (self.counterpartUUID)
        result = counterpart.contentSpec.indexResult (index) 
        if column == 0:
            return self.valOrEmpty(result, ("contactName", "firstName"))
        elif column == 1:
            return self.valOrEmpty(result, ("contactName", "lastName"))
        elif column == 2:
            return self.valOrEmpty(result, ("homeSection", "phoneNumbers", "phoneNumber"))
        elif column == 3:
            return self.valOrEmpty(result, ("homeSection", "emailAddresses", "emailAddress"))
        elif __debug__:
            assert False, "Bad column"
        return ""

class MixedListDelegate(ControlBlocks.ListDelegate):
    def ElementText (self, index, column):
        counterpart = Globals.repository.find (self.counterpartUUID)
        result = counterpart.contentSpec.indexResult (index) 
        if column == 0:
            return result.getWho()
        elif column == 1:
            return result.getAbout()
        elif column == 2:
            return result.getDate()
        elif __debug__:
            assert False, "Bad column"
        return ""


class NoteListDelegate(ControlBlocks.ListDelegate):
    def ElementText (self, index, column):
        counterpart = Globals.repository.find (self.counterpartUUID)
        result = counterpart.contentSpec.indexResult (index) 
        if column == 0:
            return result.getAbout()
        elif column == 1:
            return result.getDate()
        elif __debug__:
            assert False, "Bad column"
        return ""
