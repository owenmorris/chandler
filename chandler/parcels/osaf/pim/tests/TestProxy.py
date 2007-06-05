import unittest
import doctest
from util.testcase import SingleRepositoryTestCase
from repository.item.Item import Item
import osaf.pim as pim
import datetime
from PyICU import ICUtzinfo

def additional_tests():
    return doctest.DocFileSuite(
        'proxy.txt',
        optionflags=doctest.ELLIPSIS, package='osaf.pim',
    )
    
class ProxyTestCase(SingleRepositoryTestCase):
    sandbox = None
    
    def setUp(self):
        if self.sandbox is None:
            super(ProxyTestCase, self).setUp()
            self.sandbox = Item("sandbox", self.view, None)
            del self.view
            
        self.event = pim.calendar.Calendar.CalendarEvent(
            itsParent=self.sandbox,
            displayName=u"An event",
            startTime=datetime.datetime(2007, 3, 16, 11, 30,
                            tzinfo=ICUtzinfo.getInstance("America/New_York")),
            duration=datetime.timedelta(minutes=15),
            anyTime=False,
            read=False,
        )
        rrule = pim.calendar.Recurrence.RecurrenceRule(itsParent=self.sandbox,
                                                       freq='daily')
        self.rruleset = pim.calendar.Recurrence.RecurrenceRuleSet(
                                itsParent=self.sandbox, rrules=[rrule])

        self.one = pim.SmartCollection(itsParent=self.sandbox,
                                       displayName=u"One")
        self.two = pim.SmartCollection(itsParent=self.sandbox,
                                       displayName=u"Two")

    def tearDown(self):
        for child in self.sandbox.iterChildren():
            child.delete(recursive=True)

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
        
        if __debug__:
            self.failUnlessRaises(AssertionError,
                                  proxiedSecond.itsItem.collections.add, 
                                  self.two)
        else:
            proxiedSecond.itsItem.collections.add(self.two)
            
        self.failIf(second.itsItem in self.two)
        self.failIf(self.event.itsItem in self.two)
        for modItem in self.event.modifications:
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

    def testUnstamp_THISANDFUTURE(self):
        pim.TaskStamp(self.event).add()
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()
        
        pim.TaskStamp(pim.CHANGE_FUTURE(third)).remove()
        
        self.failIfEqual(third.getMaster(), self.event.getMaster())
        self.failIf(pim.has_stamp(third, pim.TaskStamp))
        self.failIf(pim.has_stamp(third.getNextOccurrence(), pim.TaskStamp))
        self.failUnless(pim.has_stamp(self.event, pim.TaskStamp))
        self.failUnless(pim.has_stamp(self.event.getFirstOccurrence(),
                                      pim.TaskStamp))

    def testUnstampEvent_ALL(self):
        self.event.rruleset = self.rruleset
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()

        pim.CHANGE_ALL(third).remove()
        
        self.failUnless(pim.isDead(third.itsItem))
        self.failIf(pim.isDead(self.event.itsItem))
        self.failIf(pim.has_stamp(self.event, pim.EventStamp))
        
if __name__ == "__main__":
    from util.test_finder import ScanningLoader

    unittest.main(testLoader=ScanningLoader())
