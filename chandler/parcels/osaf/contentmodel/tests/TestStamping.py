"""
Unit tests for notes parcel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import mx.DateTime as DateTime

from repository.util.Path import Path


class StampingTest(TestContentModel.ContentModelTestCase):
    """ Test Stamping in the Content Model """

    def testStamping(self):
        """ Simple test for creating instances of notes and stamping to related kinds """

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel")

        # Construct sample items
        noteItem1 = Notes.Note("noteItem1")
        noteItem2 = Notes.Note("noteItem2")
        noteItem3 = Notes.Note("noteItem3")

        # Double check kinds
        self.assertEqual(noteItem1.itsKind, ContentModel.ContentModel.getNoteKind())
        self.assertEqual(noteItem2.itsKind, ContentModel.ContentModel.getNoteKind())
        self.assertEqual(noteItem3.itsKind, ContentModel.ContentModel.getNoteKind())

        # Add some attributes
        note1About = 'note1About'
        noteItem1.about = note1About
        note2About = 'note2About'
        noteItem2.about = note2About
        note3About = 'note3About'
        noteItem3.about = note3About
        note1Date = DateTime.now()
        noteItem1.date = note1Date
        note2Date = DateTime.now()
        noteItem2.date = note2Date
        note3Date = DateTime.now()
        noteItem3.date = note3Date
        
        # Get the stamp kinds
        mailMixin = Mail.MailParcel.getMailMessageMixinKind()
        taskMixin = Task.TaskParcel.getTaskMixinKind()
        eventMixin = Calendar.CalendarParcel.getCalendarEventMixinKind()

        # Stamp to Mail, Task, Event
        addOperation = 'add'
        noteItem1.StampKind(addOperation, mailMixin)
        noteItem2.StampKind(addOperation, taskMixin)
        noteItem3.StampKind(addOperation, eventMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)

        # Stamp additional Task, Event, Mail
        noteItem1.StampKind(addOperation, taskMixin)
        noteItem2.StampKind(addOperation, eventMixin)
        noteItem3.StampKind(addOperation, mailMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)

        # Stamp additional, so they have all three
        noteItem1.StampKind(addOperation, eventMixin)
        noteItem2.StampKind(addOperation, mailMixin)
        noteItem3.StampKind(addOperation, taskMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)

        # unstamp in different orders - mail
        removeOperation = 'remove'
        noteItem1.StampKind(removeOperation, mailMixin)
        noteItem2.StampKind(removeOperation, mailMixin)
        noteItem3.StampKind(removeOperation, mailMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)

        # unstamp in different orders - event
        noteItem1.StampKind(removeOperation, eventMixin)
        noteItem2.StampKind(removeOperation, eventMixin)
        noteItem3.StampKind(removeOperation, eventMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)

        # unstamp in different orders - task
        noteItem1.StampKind(removeOperation, taskMixin)
        noteItem2.StampKind(removeOperation, taskMixin)
        noteItem3.StampKind(removeOperation, taskMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)
        
        # should all be back to Note again
        self.assertEqual(noteItem1.itsKind, ContentModel.ContentModel.getNoteKind())
        self.assertEqual(noteItem2.itsKind, ContentModel.ContentModel.getNoteKind())
        self.assertEqual(noteItem3.itsKind, ContentModel.ContentModel.getNoteKind())

        # now mixin some arbitrary Kind
        anotherKind = ContentModel.ContentModel.getConversationKind()

        # stamp an event, mail, task with another kind
        noteItem1.StampKind(addOperation, eventMixin)
        noteItem2.StampKind(addOperation, mailMixin)
        noteItem3.StampKind(addOperation, taskMixin)

        noteItem1.StampKind(addOperation, anotherKind)
        noteItem2.StampKind(addOperation, anotherKind)
        noteItem3.StampKind(addOperation, anotherKind)

        noteItem1.StampKind(removeOperation, anotherKind)
        noteItem2.StampKind(removeOperation, anotherKind)
        noteItem3.StampKind(removeOperation, anotherKind)

        noteItem1.StampKind(removeOperation, eventMixin)
        noteItem2.StampKind(removeOperation, mailMixin)
        noteItem3.StampKind(removeOperation, taskMixin)

        # see that they still have their attributes
        self.assertEqual(noteItem1.about, note1About)
        self.assertEqual(noteItem1.date, note1Date)
        self.assertEqual(noteItem2.about, note2About)
        self.assertEqual(noteItem2.date, note2Date)
        self.assertEqual(noteItem3.about, note3About)
        self.assertEqual(noteItem3.date, note3Date)
        
        # should all be back to Note again
        self.assertEqual(noteItem1.itsKind, ContentModel.ContentModel.getNoteKind())
        self.assertEqual(noteItem2.itsKind, ContentModel.ContentModel.getNoteKind())
        self.assertEqual(noteItem3.itsKind, ContentModel.ContentModel.getNoteKind())

if __name__ == "__main__":
    unittest.main()
