#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

import unittest
import doctest
from util.testcase import SingleRepositoryTestCase
from repository.item.Item import Item
import osaf.pim as pim
import datetime, time
from osaf.mail.message import messageTextToKind


def additional_tests():
    return doctest.DocFileSuite(
        'proxy.txt',
        optionflags=doctest.ELLIPSIS, package='osaf.pim',
    )

class ProxyTestCase(SingleRepositoryTestCase):
    sandbox = None

    def makeRuleset(self, freq):
        rrule = pim.calendar.Recurrence.RecurrenceRule(itsParent=self.sandbox,
                                                       freq=freq)
        return pim.calendar.Recurrence.RecurrenceRuleSet(
                                itsParent=self.sandbox, rrules=[rrule])


    def setUp(self):
        if self.sandbox is None:
            super(ProxyTestCase, self).setUp()
            type(self).sandbox = Item("sandbox", self.view, None)
            del self.view
        view = self.sandbox.itsView

        self.event = pim.calendar.Calendar.CalendarEvent(
            itsParent=self.sandbox,
            displayName=u"An event",
            startTime=datetime.datetime(2007, 3, 16, 11, 30,
                            tzinfo=view.tzinfo.getInstance("America/New_York")),
            duration=datetime.timedelta(minutes=15),
            anyTime=False,
            read=False,
        )
        self.rruleset = self.makeRuleset('daily')
        self.one = pim.SmartCollection(itsParent=self.sandbox,
                                       displayName=u"One")
        self.two = pim.SmartCollection(itsParent=self.sandbox,
                                       displayName=u"Two")
        return view

    def tearDown(self):
        for child in self.sandbox.iterChildren():
            child.delete(recursive=True)

class ProxyChangeTestCase(ProxyTestCase):

    def testAdd_THIS(self):
        # Adding just a THIS mod to a collection is disabled for now
        # (fails with an assertion).
        self.event.itsItem.collections=[self.one, self.two]
        self.event.rruleset = self.rruleset
        second = self.event.getFirstOccurrence().getNextOccurrence()
        proxiedSecond = pim.CHANGE_THIS(second)

        if __debug__:
            self.failUnlessRaises(AssertionError,
                                  proxiedSecond.itsItem.collections.remove, 
                                  self.two)
        else:
            proxiedSecond.itsItem.collections.remove(self.two)

        self.failUnless(second.itsItem in self.two)
        self.failUnless(self.event.itsItem in self.two)
        for modItem in self.event.modifications:
            self.failUnless(modItem in self.two)


    def testRemove_ALL(self):
        self.event.itsItem.collections=[self.one, self.two]
        self.event.rruleset = self.rruleset

        firstProxy = pim.CHANGE_ALL(self.event.getFirstOccurrence())
        firstProxy.itsItem.collections.remove(self.one)

        self.failIf(self.event.itsItem in self.one)
        self.failUnless(self.event.itsItem in self.two)

    def testRemove_THISANDFUTURE(self):
        self.event.itsItem.collections=[self.one, self.two]
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()
        secondProxy = pim.CHANGE_FUTURE(second)
        secondProxy.itsItem.collections.remove(self.two)

        self.failUnless(self.event.itsItem in self.one)
        self.failUnless(self.event.itsItem in self.two)
        self.failIfEqual(self.event.getMaster(), second.getMaster())
        self.failIf(second.itsItem in self.two)
        self.failUnless(self.event.itsItem in self.two)

    def testAdd_THIS(self):
        # Adding just a THIS mod to a collection is disabled for now
        # (fails with an assertion).
        self.event.itsItem.collections=[self.one]
        self.event.rruleset = self.rruleset
        second = self.event.getFirstOccurrence().getNextOccurrence()
        proxiedSecond = pim.CHANGE_THIS(second)

        proxiedSecond.itsItem.collections.add(self.two)

        self.failUnless(second.itsItem in self.two)
        self.failIf(self.event.itsItem in self.two)
        for modItem in self.event.modifications:
            if modItem is not second.itsItem:
                self.failIf(modItem in self.two)


    def testAdd_ALL(self):
        self.event.itsItem.collections=[self.one]
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()
        pim.CHANGE_THIS(second).summary = u'New'
        secondProxy = pim.CHANGE_ALL(second)
        secondProxy.itsItem.collections.add(self.two)

        self.failUnless(self.event.itsItem in self.two)
        self.failUnless(self.event.modifications, "No auto-generated occurrences?")
        for modItem in self.event.modifications:
            self.failUnless(modItem in self.two)

    def test_THIS(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.CHANGE_THIS(third).allDay = True

        self.failUnless(third.modificationFor is not None)
        self.failUnless(third.allDay)
        self.failIf(self.event.allDay)

    def testStamp_THIS(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.TaskStamp(pim.CHANGE_THIS(third)).add()

        self.failUnless(third.modificationFor is not None)
        self.failUnless(pim.has_stamp(third, pim.TaskStamp))
        self.failIf(pim.has_stamp(self.event, pim.TaskStamp))
        self.failIf(pim.has_stamp(self.event.getFirstOccurrence(),
                                  pim.TaskStamp))

    def testUnstamp_THIS(self):
        pim.TaskStamp(self.event).add()
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.TaskStamp(pim.CHANGE_THIS(third)).remove()

        self.failUnless(third.modificationFor is not None)
        self.failIf(pim.has_stamp(third, pim.TaskStamp))
        self.failUnless(pim.has_stamp(self.event, pim.TaskStamp))
        self.failUnless(pim.has_stamp(self.event.getFirstOccurrence(),
                                      pim.TaskStamp))

    def testStamp_THISANDFUTURE(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.TaskStamp(pim.CHANGE_FUTURE(third)).add()

        self.failIfEqual(third.getMaster(), self.event.getMaster())
        self.failUnless(pim.has_stamp(third, pim.TaskStamp))
        self.failUnless(pim.has_stamp(third.getNextOccurrence(), pim.TaskStamp))
        self.failIf(pim.has_stamp(self.event, pim.TaskStamp))
        self.failIf(pim.has_stamp(self.event.getFirstOccurrence(),
                                  pim.TaskStamp))

    def testStamp_THISANDFUTURE(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.TaskStamp(pim.CHANGE_FUTURE(third)).add()

        self.failIfEqual(third.getMaster(), self.event.getMaster())
        self.failUnless(pim.has_stamp(third, pim.TaskStamp))
        self.failUnless(pim.has_stamp(third.getNextOccurrence(), pim.TaskStamp))
        self.failIf(pim.has_stamp(self.event, pim.TaskStamp))
        self.failIf(pim.has_stamp(self.event.getFirstOccurrence(),
                                  pim.TaskStamp))

    def testStamp_ALL(self):
        self.event.rruleset = self.rruleset
        ruleEnd = self.event.startTime + datetime.timedelta(days=10)
        self.event.rruleset.rrules.first().until = ruleEnd
        
        occurrences = [self.event.getFirstOccurrence()]
        for i in xrange(10):
            occurrences.append(occurrences[-1].getNextOccurrence())

        pim.TaskStamp(pim.CHANGE_ALL(occurrences[0])).add()

        for event in occurrences:
            self.failUnlessEqual(event.getMaster(), self.event)
        for item in self.event.occurrences:
            self.failUnless(pim.has_stamp(item, pim.TaskStamp))
        self.failUnless(pim.has_stamp(self.event, pim.TaskStamp))

    def testUnstampEvent_ALL(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.CHANGE_ALL(third).remove()

        self.failUnless(pim.isDead(third.itsItem))
        self.failIf(pim.isDead(self.event.itsItem))
        self.failIf(pim.has_stamp(self.event, pim.EventStamp))


    def testChangeRecurrence_ALL(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.CHANGE_ALL(third).rruleset = self.makeRuleset('weekly')

        self.failUnless(pim.isDead(third.itsItem))
        self.failIf(pim.isDead(self.event.itsItem))
        self.failUnlessEqual(self.event.rruleset.rrules.first().freq, 'weekly')


    def testChangeRecurrence_FUTURE(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.CHANGE_FUTURE(third).rruleset = self.makeRuleset('weekly')

        self.failIfEqual(third.getMaster(), self.event.getMaster())
        self.failIf(pim.isDead(self.event.itsItem))
        self.failIf(pim.isDead(third.itsItem))
        self.failUnlessEqual(third, third.getMaster().getFirstOccurrence())
        self.failUnlessEqual(self.event.rruleset.rrules.first().freq, 'daily')
        self.failUnlessEqual(third.rruleset.rrules.first().freq, 'weekly')

    def testDeleteRecurrence_ALL(self):
        self.event.rruleset = self.rruleset
        first = self.event.getFirstOccurrence()
        third = first.getNextOccurrence().getNextOccurrence()

        del pim.CHANGE_ALL(third).rruleset

        self.failUnless(pim.isDead(first.itsItem))
        self.failUnless(pim.isDead(third.itsItem))
        self.failIf(pim.isDead(self.event.itsItem))
        self.failUnless(self.event.rruleset is None)

class ProxyEditStateTestCase(ProxyTestCase):
    def setUp(self):
        view = super(ProxyEditStateTestCase, self).setUp()
        self.start = (datetime.datetime.now(view.tzinfo.default) -
                      datetime.timedelta(minutes=10))
        self.event.itsItem.changeEditState(pim.Modification.created,
                                           when=self.start)

    def testNoRecurrence_THIS(self):
        pim.CHANGE_THIS(self.event.itsItem).changeEditState()

        self.failUnlessEqual(self.event.itsItem.lastModification,
                             pim.Modification.edited)
        self.failUnless(self.event.itsItem.lastModified > self.start)


    def testNoRecurrence_FUTURE(self):
        pim.CHANGE_FUTURE(self.event.itsItem).changeEditState()

        self.failUnlessEqual(self.event.itsItem.lastModification,
                             pim.Modification.edited)
        self.failUnless(self.event.itsItem.lastModified > self.start)

    def testNoRecurrence_ALL(self):
        pim.CHANGE_ALL(self.event.itsItem).changeEditState()

        self.failUnlessEqual(self.event.itsItem.lastModification,
                             pim.Modification.edited)
        self.failUnless(self.event.itsItem.lastModified > self.start)

    def testRecurrence(self):
        self.event.rruleset = self.rruleset

        # This assumes that assigning rruleset auto-creates occurrences
        self.failUnless(self.event.occurrences)

        for occurrence in self.event.occurrences:
            self.failIf(occurrence.hasLocalAttributeValue('lastModified'))
            self.failIf(occurrence.hasLocalAttributeValue('lastModification'))

    def testChange_THIS(self):
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()

        pim.CHANGE_THIS(second).summary = u'I am so special'
        self.failUnlessEqual(self.event.itsItem.lastModified, self.start)
        self.failUnless(second.itsItem.lastModified > self.start)

    def testChange_FUTURE(self):
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()

        pim.CHANGE_FUTURE(second).startTime = second.startTime + datetime.timedelta(hours=1)
        self.failUnlessEqual(self.event.itsItem.lastModified, self.start)
        self.failUnless(second.itsItem.lastModified > self.start)
        self.failUnless(second.getNextOccurrence().itsItem.lastModified > self.start)

    def testChange_ALL(self):
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()

        pim.CHANGE_ALL(second).startTime = second.startTime + datetime.timedelta(hours=1)
        self.failUnless(self.event.itsItem.lastModified > self.start)
        self.failUnlessEqual(second.getNextOccurrence().itsItem.lastModified,
                            self.event.itsItem.lastModified)


    def testChangeNonOverlapping_THIS_ALL(self):
        # Make a THIS change to one occurrence, followed by an ALL
        # change of a different attribute to a different occurrence, and make
        # sure the lastModified is updated accordingly.
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()
        third = second.getNextOccurrence()

        # THIS change to summary (a.k.a. displayName) ...
        pim.CHANGE_THIS(third).summary = u'This has been changed'
        # Make sure the lastModified changed for this event (third) ...
        self.failUnless(third.itsItem.lastModified > self.start)
        # ... but not for second, a different event in the series
        self.failUnlessEqual(second.itsItem.lastModified, self.start)

        # Now make an ALL change on duration
        pim.CHANGE_ALL(second).duration = datetime.timedelta(hours=4)

        # self.event (the master) should have a changed lastModified
        self.failIfEqual(self.event.itsItem.lastModified, self.start)
        # ... which is the same as for second
        self.failUnlessEqual(self.event.itsItem.lastModified,
                             second.itsItem.lastModified)
        # third was altered by the last change, so its
        # lastModified should be changed, too.
        self.failUnlessEqual(self.event.itsItem.lastModified,
                             third.itsItem.lastModified)


    def testChangeOverlapping_THIS_ALL(self):
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()
        third = second.getNextOccurrence()

        pim.CHANGE_THIS(third).duration = datetime.timedelta(hours=2)
        self.failUnless(third.itsItem.lastModified > self.start)

        saveLastModified = third.itsItem.lastModified
        time.sleep(0.1) # Make sure some time elapses for lastModified

        pim.CHANGE_ALL(second).duration = datetime.timedelta(hours=4)
        # However, third wasn't altered by the last change, so its
        # lastModified should be unchanged.
        self.failUnlessEqual(saveLastModified, third.itsItem.lastModified)

    def testChangeNonOverlapping_THIS_FUTURE(self):
        # Make a THIS change to one occurrence, followed by an FUTURE
        # change of a different attribute to a different occurrence, and make
        # sure the lastModified is updated accordingly.
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()
        third = second.getNextOccurrence()

        # THIS change to summary (a.k.a. displayName) ...
        pim.CHANGE_THIS(third).summary = u'This has been changed'
        # Make sure the lastModified changed for this event (third) ...
        self.failUnless(third.itsItem.lastModified > self.start)
        # ... but not for second, a different event in the series
        self.failUnlessEqual(second.itsItem.lastModified, self.start)

        # Remember third's lastModified, so we can check that it changed
        # later.
        saveLastModified = third.itsItem.lastModified

        time.sleep(0.1) # Make sure some time elapses for lastModified

        # Now make an FUTURE change on duration
        pim.CHANGE_FUTURE(second).duration = datetime.timedelta(hours=4)

        # self.event (the master) should have an unchanged lastModified
        self.failUnlessEqual(self.event.itsItem.lastModified, self.start)
        # second is now part of a new series, and so should have a new
        # lastModified
        self.failIfEqual(self.event.itsItem.lastModified,
                         second.itsItem.lastModified)
        # third was altered by the last change, so its
        # lastModified should be changed, too.
        self.failIfEqual(saveLastModified, third.itsItem.lastModified)
        self.failUnlessEqual(second.itsItem.lastModified,
                             third.itsItem.lastModified)


    def testChangeOverlapping_THIS_FUTURE(self):
        self.event.rruleset = self.rruleset

        second = self.event.getFirstOccurrence().getNextOccurrence()
        third = second.getNextOccurrence()

        pim.CHANGE_THIS(third).duration = datetime.timedelta(hours=2)
        self.failUnless(third.itsItem.lastModified > self.start)

        saveLastModified = third.itsItem.lastModified

        time.sleep(0.1) # Make sure some time elapses for lastModified        
        pim.CHANGE_FUTURE(second).duration = datetime.timedelta(hours=4)
        # However, third wasn't altered by the last change, so its
        # lastModified should be unchanged.
        self.failUnlessEqual(saveLastModified, third.itsItem.lastModified)

    def testChangeCC(self):

#        email = pim.mail.EmailAddress(itsParent=self.sandbox, fullName=u'Tommy Totoro',
#                             emailAddress=u'totoro@example.com')

        mei = pim.mail.EmailAddress(itsParent=self.sandbox, fullName=u'Mei Kusakabe',
                          emailAddress=u'mei@totoro.example.com')

        catbus = pim.mail.EmailAddress(itsParent=self.sandbox,
                          fullName=u'Nekobasu',
                          emailAddress=u'cat-bus@totoro.example.com')

        mail = messageTextToKind(self.sandbox.itsView,
            "From: Nekobasu <cat-bus@totoro.example.com\r\n"
            "To: Mei Kusakabe <mei@totoro.example.com\r\n"
            "Subject: Do you need a ride home?\r\n"
            "Content-Type: text/plain; charset='US-ASCII'"
            "\r\n"
            "I think it's raining!\r\n"
        )[1]
        mail.itsItem.lastModification = pim.Modification.created

        pim.mail.getCurrentMeEmailAddresses(mei.itsView).add(mei)

        event = pim.EventStamp(mail)
        event.add()
        event.rruleset = self.rruleset

        pim.CHANGE_THIS(mail.itsItem).displayName = u"You bet I do!"

        firstItem = event.getFirstOccurrence().itsItem

        self.failIf(firstItem.hasLocalAttributeValue(
                        pim.mail.MailStamp.ccAddress.name)
        )

        self.failUnless(mei is mail.fromAddress)
        self.failUnless(catbus in mail.ccAddress)

if __name__ == "__main__":
    from util.test_finder import ScanningLoader

    unittest.main(testLoader=ScanningLoader())
