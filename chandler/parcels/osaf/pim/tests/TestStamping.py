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

"""
Unit test for stamping
"""

import unittest, doctest

import osaf.pim.tests.TestDomainModel as TestDomainModel
from osaf import pim
from application import schema
import osaf.pim.mail as Mail
import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.generate as generate
import logging

from datetime import datetime
from repository.util.Path import Path
from osaf.pim.stamping import has_stamp, StampAlreadyPresentError, StampNotPresentError

def test_stamping_doc():
    return doctest.DocFileSuite(
        'stamping.txt',
        optionflags=doctest.ELLIPSIS, package='osaf.pim',
    )


verbose = False
compareWhos = False
compareDates = False # date shouldn't automatically carry over
testFailureCases = True

class SavedAttrs:
    """
    Saved Attributes stored in one of these
    """
    pass

class StampingTest(TestDomainModel.DomainModelTestCase):

    """ Test Stamping in the Domain Model """
    def setAttributes(self, item, doWho=True):
        try:
            savedItems = self.savedAttrs
        except AttributeError:
            self.savedAttrs = {}
        
        savedAttrs = SavedAttrs()
        self.savedAttrs[item.itsName] = savedAttrs
            
        displayName = 'aTitleOrHeadline'
        item.displayName = displayName
        savedAttrs.displayName = displayName
        
        item.createdOn = self.savedAttrs[item.itsName].createdOn = datetime.now()
    
        if has_stamp(item, pim.TaskStamp):
            task = pim.TaskStamp(item)
            # Add some attributes here...
        
        if has_stamp(item, pim.EventStamp):
            event = pim.EventStamp(item)
            
        if has_stamp(item, Mail.MailStamp):
            mail = Mail.MailStamp(item)

        """
        item.displayName = anAbout
        aDate = datetime.now()
        item.date = aDate
        aWhoList = []
        view = item.itsView
        if doWho:
            aWhoList.append(generate.GenerateCalendarParticipant(view))
            aWhoList.append(generate.GenerateCalendarParticipant(view))
        if compareWhos:
            item.who = aWhoList


        savedAttrs.displayName = anAbout
        savedAttrs.date = aDate
        savedAttrs.who = aWhoList
        """

    def assertAttributes(self, item):
        itemAttrs = self.savedAttrs[item.itsName]
        self.assertEqual(item.displayName, itemAttrs.displayName)
        # compare the dates
        if compareDates:
            self.assertEqual(item.createdOn, itemAttrs.createdOn)
        # compare the whos
        if compareWhos:
            self.assertEqual(len(item.who), len(itemAttrs.who))
            i = 0
            for whom in item.who:
                self.assertEqual(whom, itemAttrs.who[i])
                i += 1

    #def assertKinds(self, item, stampsList):
    #    self.assertAttributes(item)
    #    for stamp in stampsList:
    #        self.failUnless(stamp in Stamp(item).stamps)

    def traverseStampSquence(self, item, sequence):
        for operation, stampClass in sequence:
            if verbose:
                message = "stamping %s: %s %s" % \
                        (item.itsKind.itsName, 
                         operation,
                         stampClass)
                logging.info(message)
            stampItem = stampClass(item)
            getattr(stampItem, operation)() # i.e. stampClass(item).add() or
                                            # stampClass(item).remove()
            self.assertAttributes(item)
            if operation == 'add':
                self.failUnless(has_stamp(item, stampClass))

    def testStamping(self):
        # Make sure the domain model is loaded.
        self.loadParcel("osaf.pim")
        # @@@ Also make sure the default imap account is loaded, in order to
        # have a "me" EmailAddress
        self.loadParcel("osaf.mail")
        view = self.rep.view
        
        # Get the stamp kinds
        mailStamp = Mail.MailStamp
        taskStamp = pim.TaskStamp
        eventStamp = Calendar.EventStamp
        noteKind = pim.Note.getKind(view)

        # start out with a Note
        aNote = pim.Note("noteItem1", itsView=view)
        self.setAttributes(aNote, doWho=False)
        self.assertAttributes(aNote)
        add = 'add'
        remove = 'remove'

        # stamp everything on and off the note
        self.traverseStampSquence(aNote, ((add, mailStamp),
                                          (add, taskStamp),
                                          (add, eventStamp),
                                          (remove, eventStamp),
                                          (remove, taskStamp),
                                          (remove, mailStamp)))

        # stamp everything on again, remove in a different order
        self.traverseStampSquence(aNote, ((add, mailStamp),
                                          (add, taskStamp),
                                          (add, eventStamp),
                                          (remove, mailStamp),
                                          (remove, taskStamp),
                                          (remove, eventStamp)))
        self.assertAttributes(aNote)

        # Create a Task, and do all kinds of stamping on it
        aTask = pim.Task("aTask", itsView=view).itsItem
        self.setAttributes(aTask)

        self.traverseStampSquence(aTask, ((add, eventStamp),
                                          (remove, taskStamp)))
        # now it's an Event

        self.traverseStampSquence(aTask, ((add, mailStamp),
                                          (remove, mailStamp)))

        self.traverseStampSquence(aTask, ((add, mailStamp),
                                          (add, taskStamp),
                                          (remove, mailStamp),
                                          (remove, taskStamp)))

        self.traverseStampSquence(aTask, ((add, taskStamp),
                                          (add, mailStamp),
                                          (remove, mailStamp),
                                          (remove, taskStamp)))

        self.traverseStampSquence(aTask, ((add, mailStamp),
                                          (remove, eventStamp)))
        # now it's a Mail

        self.traverseStampSquence(aTask, ((add, taskStamp),
                                          (remove, mailStamp)))
        # it's a Task again

        self.traverseStampSquence(aTask, ((add, mailStamp),
                                          (remove, taskStamp)))

        self.traverseStampSquence(aTask, ((add, taskStamp),
                                          (remove, mailStamp)))
        # it's a Task again

        self.traverseStampSquence(aTask, ((add, eventStamp),
                                          (remove, taskStamp),
                                          (add, mailStamp),
                                          (remove, eventStamp),
                                          (add, taskStamp),
                                          (remove, mailStamp)))
        self.failUnless(has_stamp(aTask, taskStamp))

        # check stamping on an Event
        anEvent = Calendar.CalendarEvent("anEvent", itsView=view).itsItem
        self.setAttributes(anEvent)

        # round-robin its Kind back to event
        self.traverseStampSquence(anEvent, ((add, mailStamp),
                                            (remove, eventStamp),
                                            (add, taskStamp),
                                            (remove, mailStamp),
                                            (add, eventStamp),
                                            (remove, taskStamp)))
        self.failUnless(has_stamp(anEvent, eventStamp))

        # check stamping on a Mail Message
        aMessage = Mail.MailMessage("aMessage", itsView=view).itsItem
        self.setAttributes(aMessage)
        self.traverseStampSquence(aMessage, ((add, eventStamp),
                                             (add, taskStamp),
                                             (remove, eventStamp),
                                             (remove, taskStamp)))
        self.failUnless(has_stamp(aMessage, mailStamp))

        # now mixin some arbitrary Kind
        #anotherKind = view.findPath('//parcels/osaf/framework/blocks/Block')

        # stamp an event, mail, task with another kind
        #aNote.StampKind(add, anotherKind)
        #aTask.StampKind(add, anotherKind)
        #anEvent.StampKind(add, anotherKind)
        #aMessage.StampKind(add, anotherKind)

        #self.assertKinds(aNote, (noteKind, anotherKind))
        #self.assertKinds(aTask, (taskKind, anotherKind))
        #self.assertKinds(anEvent, (eventKind, anotherKind))
        #self.assertKinds(aMessage, (mailKind, anotherKind))

        # unstamp with another kind
        #aNote.StampKind(remove, anotherKind)
        #aTask.StampKind(remove, anotherKind)
        #anEvent.StampKind(remove, anotherKind)
        #aMessage.StampKind(remove, anotherKind)

        # see that they still have their attributes
        #self.assertKinds(aNote, (noteKind, ))
        #self.assertKinds(aTask, (taskKind, ))
        #self.assertKinds(anEvent, (eventKind, ))
        #self.assertKinds(aMessage, (mailKind, ))

        # Test some failure cases
        # These cases should produce suitable warning messages in Chandler.log
        if testFailureCases:
            anotherEvent = Calendar.CalendarEvent("anotherEvent", itsView=view).itsItem
            self.setAttributes(anotherEvent)
            self.failUnless(has_stamp(anotherEvent, eventStamp))
            # Could use assertRaises here, but it's syntax with respect to parameters is
            #   not clear with my complex arguments, so try/except/else is more readable.
            try:
                # double stamping
                self.traverseStampSquence(anotherEvent, ((add, mailStamp),
                                                         (add, mailStamp)))
            except StampAlreadyPresentError:
                pass
            else:
                self.failUnless(False, "Double stamping should raise an exception!")

            try:
                # unstamping something not present
                self.traverseStampSquence(anotherEvent, ((remove, taskStamp), ))
            except StampNotPresentError:
                pass
            else:
                self.failUnless(False, "Unstamping a stamp not present should raise an exception!")
            # Test for Bug:6151: Make sure items don't disappear
            # from the all collection if they're unstamped
            #
            # Make an email ...
            aMessage = Mail.MailMessage("aNewMessage", itsView=view)
            self.setAttributes(aMessage.itsItem)

            # Make sure it's in "Out"
            aMessage.fromMe = True
            outCollection = schema.ns("osaf.pim", view).outCollection

            self.failUnless(aMessage.itsItem in outCollection)

            # unstamp its emailness
            self.traverseStampSquence(aMessage.itsItem,
                                      (('add', taskStamp),
                                      ('remove', mailStamp)))
            
            allCollection = schema.ns("osaf.pim", view).allCollection
            self.failUnless(aMessage.itsItem in allCollection)
            
    def testStampWelcomeNote(self):
        
        # Look up the welcome note ...
        welcome = schema.ns("osaf.app", self.rep.view).WelcomeEvent
        
        # stamp it as a mail ...
        stampedWelcome = Mail.MailStamp(welcome)
        stampedWelcome.add()
        
        self.failUnlessEqual(list(stampedWelcome.mimeContent.mimeParts), [])
        self.failUnlessEqual(stampedWelcome.mimeContent.mimeType,
                             'message/rfc822')

def additional_tests():
    return unittest.TestSuite(
        [ test_stamping_doc(), ]
    )

if __name__ == "__main__":
    # Just using unittest.main() here isn't good enough, since
    # that wouldn't pick up the tests in additional_tests().
    # For that, the magic ScanningLoader() below is needed.
    from util import test_finder
    unittest.main(testLoader=test_finder.ScanningLoader())
