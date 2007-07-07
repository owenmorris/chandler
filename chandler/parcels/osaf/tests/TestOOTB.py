import application.schema as schema
import osaf.pim as pim
import util.testcase as testcase
from i18n import ChandlerSafeTranslationMessageFactory as translate
from datetime import *

class OOTBTestCase(testcase.SingleRepositoryTestCase):
    """
    Tests that the out-of-the box events and collections are
    created correctly.
    """
    
    def setUp(self):
        super(OOTBTestCase, self).setUp()
        # Make sure the osaf.app parcel is loaded
        schema.parcel_for_module("osaf.app", self.view)
    
    def checkStampness(self, item, *stampClasses):
        for cls in stampClasses:
            self.failUnless(pim.has_stamp(item, cls),
                            "Item %s doesn't have stamp %s" % (item, cls))
            self.failUnless(item in cls.getCollection(self.view),
                            "Item %s is not in collection for stamp %s" %
                                (item, cls))
                                
        self.failUnlessEqual(
            set(pim.Stamp(item).stamp_types),
            set(stampClasses),
            "Unexpected extra classes in stamps %s for item %s" %
                (set(pim.Stamp(item).stamp_types), item)
        )

        
    def getCollection(self, name):
        sidebar = schema.ns("osaf.app", self.view).sidebarCollection
        name = translate(name) # search for the localized name
        for coll in sidebar:
            if coll.displayName == name:
                return coll
        
        self.fail("Couldn't find collection %s in sidebar" % (name,))

    def getItem(self, name):
        all = schema.ns("osaf.pim", self.view).allCollection
        name = translate(name) # search for the localized name
        for item in all:
            if item.displayName == name:
                return item
        
        self.fail("Couldn't find item %s in all collection" % (name,))

    def testSidebar(self):
        sidebarCollection = schema.ns("osaf.app", self.view).sidebarCollection
        pim_ns = schema.ns("osaf.pim", self.view)
        
        i = iter(sidebarCollection)
        
        self.failUnless(i.next() is pim_ns.allCollection)
        self.failUnless(i.next() is pim_ns.inCollection)
        self.failUnless(i.next() is pim_ns.outCollection)
        self.failUnless(i.next() is pim_ns.trashCollection)
                        
        self.failUnless(i.next() is self.getCollection(u"Work"))
        self.failUnless(i.next() is self.getCollection(u"Home"))
        self.failUnless(i.next() is self.getCollection(u"Fun"))
        
        self.failUnlessRaises(StopIteration, i.next)

    def testWelcomeEvent(self):
        
        # Look up the welcome event ...
        welcome = schema.ns("osaf.app", self.view).WelcomeEvent
        
        # Check its event-ness ...
        self.checkStampness(welcome, pim.EventStamp, pim.TaskStamp)

        # Check it's in the all collection
        self.failUnless(
            welcome in schema.ns("osaf.pim", self.view).allCollection)
        # ... and two other collections
        self.failUnless(len(list(welcome.appearsIn)), 3)
        
    def testHomeTaskList(self):
        item = self.getItem(u"Try sharing a Home task list")
        self.checkStampness(item, pim.TaskStamp)
        self.failUnlessEqual(item.triageStatus, pim.TriageEnum.later)
        self.failIf(item.userReminderTime is None)
        self.failUnlessEqual(item.userReminderTime.time(), 
                             time(8, 0))
        self.failUnless(item in self.getCollection(u"Home"))
        self.failUnless(item in schema.ns("osaf.pim", self.view).allCollection)
        self.failUnlessEqual(len(list(item.appearsIn)), 2)
        
    def testDeleteSampleItemsNote(self):
        item = self.getItem(u"Delete sample items and collections")
        self.failUnlessEqual(item.triageStatus, pim.TriageEnum.later)
               
        self.failUnless(item in self.getCollection(u"Work"))
        self.failUnless(item in schema.ns("osaf.pim", self.view).allCollection)
        self.failUnlessEqual(len(list(item.appearsIn)), 2)

    def testPlayWithCalendar(self):
        item = self.getItem(u"Play around with the Calendar")
        self.checkStampness(item, pim.EventStamp)
        self.failUnlessEqual(item.triageStatus, pim.TriageEnum.now)
        
        self.failUnlessEqual(pim.EventStamp(item).duration, timedelta(hours=1))
        self.failUnlessEqual(pim.EventStamp(item).startTime.time(), 
                             time(hour=15))
        
        self.failUnless(item in self.getCollection(u"Home"))
        self.failUnless(item in schema.ns("osaf.pim", self.view).allCollection)
        self.failUnlessEqual(len(list(item.appearsIn)), 2)

    def testDownloadChandler(self):
        item = self.getItem(u"Download Chandler")
        self.checkStampness(item, pim.EventStamp, pim.TaskStamp)
        self.failUnlessEqual(item.triageStatus, pim.TriageEnum.done)
        self.failUnlessEqual(pim.EventStamp(item).startTime.time(), 
                             time(hour=11))        
        self.failUnlessEqual(pim.EventStamp(item).duration, 
                             timedelta(minutes=30))
                             
        self.failUnless(item in self.getCollection(u"Work"))
        self.failUnless(item in schema.ns("osaf.pim", self.view).allCollection)
        self.failUnlessEqual(len(list(item.appearsIn)), 2)
        
    def testSetupAccounts(self):
        item = self.getItem(u"Set up your accounts")
        self.checkStampness(item, pim.EventStamp, pim.TaskStamp,
                            pim.mail.MailStamp)
        self.failUnlessEqual(item.triageStatus, pim.TriageEnum.later)

        self.failUnlessEqual(pim.EventStamp(item).startTime.time(), 
                             time(hour=16))        
        self.failUnlessEqual(pim.EventStamp(item).duration,
                             timedelta(minutes=30))

        self.failUnless(item in self.getCollection(u"Fun"))
        self.failUnless(item in schema.ns("osaf.pim", self.view).allCollection)
        self.failUnlessEqual(len(list(item.appearsIn)), 3)

if __name__ == "__main__":
    import unittest
    unittest.main()
        
