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

    def getHTMLText(self, item):
        return "<html><body><h5>%s</h5></body></html>" % item.getAbout()

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
        if element is self.GetRootKind():
            return True
        else:
            return False

    def NeedsUpdate(self, notification):
        # @@@ Need observable queries!
        pass

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


    

        

