import application.Globals as Globals
import OSAF.contentmodel.calendar.Calendar as Calendar
import OSAF.contentmodel.notes.Notes as Notes
import OSAF.contentmodel.contacts.Contacts as Contacts
import OSAF.contentmodel.tests.GenerateItems as GenerateItems
import OSAF.framework.blocks.ContainerBlocks as ContainerBlocks
import repository.item.Query as Query
import repository.parcel.Parcel as Parcel

class ContentTreeList(ContainerBlocks.TreeList):

    def GetTreeDataName(self, item):
        return item.getUUID()

    def GetTreeData(self, node):
        item = node.GetData()

        if item:
            for child in item:
                names = self.GetNames(child)
                node.AddChildNode(child, names, False)
        else:
            node.AddRootNode(self.GetQuery(), ["Items"], True)

class MixedTreeList(ContentTreeList):

    def GetQuery(self):
        calendarEventKind = Calendar.CalendarParcel.getCalendarEventKind()
        noteKind = Notes.NotesParcel.getNoteKind()
        query = Query.KindQuery().run([calendarEventKind, noteKind])
        return query

    def GetNames(self, child):
        names = [child.getWho(), child.getAbout(), child.getDate()]
        return names

    def OnGenerateContentItems(self, notification):
        GenerateItems.GenerateCalendarEvents(10, 10)
        GenerateItems.GenerateNotes(5)
        GenerateItems.GenerateContacts(5)
        Globals.repository.commit()

    def OnSelectionChangedEvent(self, notification):
        wxTreeListWindow = Globals.association[self.getUUID()]
        data = notification.GetData()
        item = data['item']

        whoAttribute = item.getAttributeValue('whoAttribute')
        whoDisplay = item.getAttributeAspect(whoAttribute, 'displayName')
        wxTreeListWindow.SetColumnText(0, "Who (%s)" % whoDisplay)

        aboutAttribute = item.getAttributeValue('aboutAttribute')
        aboutDisplay = item.getAttributeAspect(aboutAttribute, 'displayName')
        wxTreeListWindow.SetColumnText(1, "About (%s)" % aboutDisplay)

        dateAttribute = item.getAttributeValue('dateAttribute')
        dateDisplay = item.getAttributeAspect(dateAttribute, 'displayName')
        wxTreeListWindow.SetColumnText(2, "Date (%s)" % str(dateDisplay))

class CalendarTreeList(ContentTreeList):
    
    def GetQuery(self):
        calendarEventKind = Calendar.CalendarParcel.getCalendarEventKind()
        query = Query.KindQuery().run([calendarEventKind])
        return query

    def GetNames(self, child):
        names = [child.getWho(), child.getAbout(), child.getDate()]
        return names

    def OnGenerateContentItems(self, notification):
        GenerateItems.GenerateCalendarEvents(10, 10)
        Globals.repository.commit()

class NoteTreeList(ContentTreeList):
    
    def GetQuery(self):
        noteKind = Notes.NotesParcel.getNoteKind()
        query = Query.KindQuery().run([noteKind])
        return query

    def GetNames(self, child):
        names = [child.getAbout(), child.getDate()]
        return names

    def OnGenerateContentItems(self, notification):
        GenerateItems.GenerateNotes(10)
        Globals.repository.commit()

class ContactTreeList(ContentTreeList):
    
    def GetQuery(self):
        contactKind = Contacts.ContactsParcel.getContactKind()
        query = Query.KindQuery().run([contactKind])
        return query

    def GetNames(self, child):
        for phone in child.homeSection.phoneNumbers: pass
        for email in child.homeSection.emailAddresses: pass
        names = [child.contactName.firstName,
                 child.contactName.lastName,
                 phone.phoneNumber, email.emailAddress]
        return names

    def OnGenerateContentItems(self, notification):
        GenerateItems.GenerateContacts(5)
        Globals.repository.commit()

