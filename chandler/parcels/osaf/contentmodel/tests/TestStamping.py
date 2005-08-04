"""
Unit tests for notes parcel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
from osaf.contentmodel.tasks import Task, TaskMixin
import osaf.contentmodel.mail as Mail
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import logging

from datetime import datetime
from repository.util.Path import Path

verbose = False
compareWhos = False
compareDates = False # date shouldn't automatically carry over
testFailureCases = True

class SavedAttrs:
    """
    Saved Attributes stored in one of these
    """
    pass

class StampingTest(TestContentModel.ContentModelTestCase):
    """ Test Stamping in the Content Model """
    def setAttributes(self, item, doWho=True):
        anAbout = 'aTitleOrHeadline'
        item.about = anAbout
        aDate = datetime.now()
        item.date = aDate
        aWhoList = []
        view = item.itsView
        if doWho:
            aWhoList.append(GenerateItems.GenerateCalendarParticipant(view))
            aWhoList.append(GenerateItems.GenerateCalendarParticipant(view))
        if compareWhos:
            item.who = aWhoList

        savedAttrs = SavedAttrs()
        try:
            savedItems = self.savedAttrs
        except AttributeError:
            self.savedAttrs = {}
        self.savedAttrs[item.itsName] = savedAttrs

        savedAttrs.about = anAbout
        savedAttrs.date = aDate
        savedAttrs.who = aWhoList

    def assertAttributes(self, item):
        itemAttrs = self.savedAttrs[item.itsName]
        self.assertEqual(item.about, itemAttrs.about)
        # compare the dates
        if compareDates:
            self.assertEqual(item.date, itemAttrs.date)
        # compare the whos
        if compareWhos:
            self.assertEqual(len(item.who), len(itemAttrs.who))
            i = 0
            for whom in item.who:
                self.assertEqual(whom, itemAttrs.who[i])
                i += 1

    def assertKinds(self, item, kindsList):
        self.assertAttributes(item)
        for kind in kindsList:
            self.assert_(item.isItemOf(kind))

    def traverseStampSquence(self, item, sequence):
        for operation, stampKind in sequence:
            if verbose:
                message = "stamping %s: %s %s" % \
                        (item.itsKind.itsName, 
                         operation,
                         stampKind.itsName)
                logging.info(message)
            item.StampKind(operation, stampKind)
            self.assertAttributes(item)
            if operation == 'add':
                self.assert_(item.isItemOf(stampKind))

    def testStamping(self):
        # Make sure the contentModel is loaded.
        self.loadParcel("parcel:osaf.contentmodel")
        # @@@ Also make sure the default imap account is loaded, in order to
        # have a "me" EmailAddress
        self.loadParcel("parcel:osaf.mail")
        view = self.rep.view
        
        # Get the stamp kinds
        mailMixin = Mail.MailMessageMixin.getKind(view)
        taskMixin = TaskMixin.getKind(view)
        eventMixin = Calendar.CalendarEventMixin.getKind(view)
        taskKind = Task.getKind(view)
        mailKind = Mail.MailMessage.getKind(view)
        eventKind = Calendar.CalendarEvent.getKind(view)
        noteKind = Notes.Note.getKind(view)

        # start out with a Note
        aNote = Notes.Note("noteItem1", view=view)
        self.setAttributes(aNote, doWho=False)
        self.assertAttributes(aNote)
        add = 'add'
        remove = 'remove'

        # stamp everything on and off the note
        self.traverseStampSquence(aNote, ((add, mailMixin),
                                          (add, taskMixin),
                                          (add, eventMixin),
                                          (remove, eventMixin),
                                          (remove, taskMixin),
                                          (remove, mailMixin)))

        # stamp everything on again, remove in a different order
        self.traverseStampSquence(aNote, ((add, mailMixin),
                                          (add, taskMixin),
                                          (add, eventMixin),
                                          (remove, mailMixin),
                                          (remove, taskMixin),
                                          (remove, eventMixin)))
        self.assertAttributes(aNote)

        # Create a Task, and do all kinds of stamping on it
        aTask = Task("aTask", view=view)
        self.setAttributes(aTask)

        self.traverseStampSquence(aTask, ((add, eventMixin),
                                          (remove, taskMixin)))
        # now it's an Event

        self.traverseStampSquence(aTask, ((add, mailMixin),
                                          (remove, mailMixin)))

        self.traverseStampSquence(aTask, ((add, mailMixin),
                                          (add, taskMixin),
                                          (remove, mailMixin),
                                          (remove, taskMixin)))

        self.traverseStampSquence(aTask, ((add, taskMixin),
                                          (add, mailMixin),
                                          (remove, mailMixin),
                                          (remove, taskMixin)))

        self.traverseStampSquence(aTask, ((add, mailMixin),
                                          (remove, eventMixin)))
        # now it's a Mail

        self.traverseStampSquence(aTask, ((add, taskMixin),
                                          (remove, mailMixin)))
        # it's a Task again

        self.traverseStampSquence(aTask, ((add, mailMixin),
                                          (remove, taskMixin)))

        self.traverseStampSquence(aTask, ((add, taskMixin),
                                          (remove, mailMixin)))
        # it's a Task again

        self.traverseStampSquence(aTask, ((add, eventMixin),
                                          (remove, taskMixin),
                                          (add, mailMixin),
                                          (remove, eventMixin),
                                          (add, taskMixin),
                                          (remove, mailMixin)))
        self.assert_(aTask.isItemOf(taskKind))

        # check stamping on an Event
        anEvent = Calendar.CalendarEvent("anEvent", view=view)
        self.setAttributes(anEvent)

        # round-robin it's Kind back to event
        self.traverseStampSquence(anEvent, ((add, mailMixin),
                                            (remove, eventMixin),
                                            (add, taskMixin),
                                            (remove, mailMixin),
                                            (add, eventMixin),
                                            (remove, taskMixin)))
        self.assert_(anEvent.isItemOf(eventKind))

        # check stamping on a Mail Message
        aMessage = Mail.MailMessage("aMessage", view=view)
        self.setAttributes(aMessage)
        self.traverseStampSquence(aMessage, ((add, eventMixin),
                                             (add, taskMixin),
                                             (remove, eventMixin),
                                             (remove, taskMixin)))
        self.assert_(aMessage.isItemOf(mailKind))

        # now mixin some arbitrary Kind
        anotherKind = self.rep.findPath('//parcels/osaf/framework/blocks/Block')

        # stamp an event, mail, task with another kind
        aNote.StampKind(add, anotherKind)
        aTask.StampKind(add, anotherKind)
        anEvent.StampKind(add, anotherKind)
        aMessage.StampKind(add, anotherKind)

        self.assertKinds(aNote, (noteKind, anotherKind))
        self.assertKinds(aTask, (taskKind, anotherKind))
        self.assertKinds(anEvent, (eventKind, anotherKind))
        self.assertKinds(aMessage, (mailKind, anotherKind))

        # unstamp with another kind
        aNote.StampKind(remove, anotherKind)
        aTask.StampKind(remove, anotherKind)
        anEvent.StampKind(remove, anotherKind)
        aMessage.StampKind(remove, anotherKind)

        # see that they still have their attributes
        self.assertKinds(aNote, (noteKind, ))
        self.assertKinds(aTask, (taskKind, ))
        self.assertKinds(anEvent, (eventKind, ))
        self.assertKinds(aMessage, (mailKind, ))

        # Test some failure cases
        # These cases should produce suitable warning messages in Chandler.log
        if testFailureCases:
            anotherEvent = Calendar.CalendarEvent("anotherEvent", view=view)
            self.setAttributes(anotherEvent)
            self.assert_(anotherEvent.isItemOf(eventKind))
            try:
                # double stamping
                self.traverseStampSquence(anotherEvent, ((add, mailMixin),
                                                         (add, mailMixin)))
            except:
                pass

            try:
                # unstamping something not present
                self.traverseStampSquence(anotherEvent, ((remove, taskMixin), ))
            except:
                pass


if __name__ == "__main__":
    unittest.main()
