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
        if kind is Calendar.CalendarParcel.getCalendarEventKind():
            HTMLText += "<b>Headline: </b> %s<br>" % item.getAbout()
            HTMLText += "<b>Attendees: </b> %s<br>" % item.getWho()
            HTMLText += "<b>Date: </b> %s<br>" % item.getDate()
            HTMLText += "<b>Duration: </b> %s<br>" % item.duration
        elif kind is Notes.NotesParcel.getNoteKind():
            HTMLText += "<b>Title: </b> %s<br>" % item.getAbout()
        elif kind is Contacts.ContactsParcel.getContactKind():
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
        
        return HTMLText

class QueryTreeDelegate:

    def ElementParent(self, element):
        rootKind = self.GetRootKind()
        if element is rootKind:
            return None
        else:
            return rootKind

    def ElementChildren(self, element):
        if element:
            return self.GetQuery()
        else:
            return self.GetRootKind()

    def ElementCellValues(self, element):
        if element is self.GetRootKind():
            return ["//"]
        else:
            return self.GetCellValues(element)

    def ElementHasChildren(self, element):
        return (element is self.GetRootKind())

    def NeedsUpdate(self, notification):
        # @@@ Need observable queries!
        # the current simple strategy is to schedule an update if
        # the item is of the kind we're interested in
        item = Globals.repository.find(notification.data['uuid'])
        if item.kind is self.GetRootKind():
            self.scheduleUpdate = True
            

class MixedTreeDelegate(QueryTreeDelegate):

    def GetRootKind(self):
        return Calendar.CalendarParcel.getCalendarEventKind()
    
    def GetQuery(self):
        calendarEventKind = Calendar.CalendarParcel.getCalendarEventKind()    
        noteKind = Notes.NotesParcel.getNoteKind()
        query = Query.KindQuery().run([calendarEventKind, noteKind])
        return query
    
    def GetCellValues(self, element):
        return [element.getWho(), element.getAbout(), element.getDate()]

    def GetCellLabels(self, element):
        whoAttribute = element.getAttributeValue('whoAttribute')
        whoDisplay = element.getAttributeAspect(whoAttribute, 'displayName')

        aboutAttribute = item.getAttributeValue('aboutAttribute')
        aboutDisplay = item.getAttributeAspect(aboutAttribute, 'displayName')

        dateAttribute = item.getAttributeValue('dateAttribute')
        dateDisplay = item.getAttributeAspect(dateAttribute, 'displayName')

        return ["Who (%s)" % whoDisplay,
                "About (%s)" % aboutDisplay,
                "Date (%s)" % str(dateDisplay)]

    def NeedsUpdate(self, notification):
        item = Globals.repository.find(notification.data['uuid'])
        if (item.kind is Notes.NotesParcel.getNoteKind() or
            item.kind is Calendar.CalendarParcel.getCalendarEventKind()):
            self.scheduleUpdate = True
    
class CalendarTreeDelegate(QueryTreeDelegate):
    
    def GetRootKind(self):
        return Calendar.CalendarParcel.getCalendarEventKind()
    
    def GetQuery(self):
        calendarEventKind = Calendar.CalendarParcel.getCalendarEventKind()    
        query = Query.KindQuery().run([calendarEventKind])
        return query
    
    def GetCellValues(self, element):
        return [element.getWho(), element.getAbout(), element.getDate()]

class ContactTreeDelegate(QueryTreeDelegate):
    
    def GetRootKind(self):
        return Contacts.ContactsParcel.getContactKind()
    
    def GetQuery(self):
        contactKind = Contacts.ContactsParcel.getContactKind()    
        query = Query.KindQuery().run([contactKind])
        return query
    
    def GetCellValues(self, element):
        for phone in element.homeSection.phoneNumbers: pass
        for email in element.homeSection.emailAddresses: pass
        values = [element.contactName.firstName,
                  element.contactName.lastName,
                  phone.phoneNumber, email.emailAddress]
        return values
    
class NoteTreeDelegate(QueryTreeDelegate):
    
    def GetRootKind(self):
        return Notes.NotesParcel.getNoteKind()
    
    def GetQuery(self):
        noteKind = Notes.NotesParcel.getNoteKind()    
        query = Query.KindQuery().run([noteKind])
        return query
    
    def GetCellValues(self, element):
        return [element.getAbout(), element.getDate()]


    

        

