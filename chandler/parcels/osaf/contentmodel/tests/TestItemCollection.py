"""
Unit tests for item collections
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, random

import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems

class TestItemCollection(TestContentModel.ContentModelTestCase):

    def testCollectionEvents(self):

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")

        ic = ItemCollection.NamedCollection()
        for index in range(100):
            item = GenerateItems.GenerateCalendarEvent(100)
            ic.add(item)

            # test __contains__
            self.assert_(item in ic)

        # test __len__
        self.assert_(len(ic) > 0)

        # pick a random item in the item collection
        item = random.choice(ic)

        # test index
        index = ic.index(item)

        # test __getitem__
        self.assert_(item == ic[index])

        del index

        # test exclude
        ic.remove(item)
        self.assert_(item not in ic)
        
    def testRule(self):
        import logging
        log = logging.getLogger("Test")
        log.setLevel(logging.DEBUG)

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel")

        log.debug("Generating calendar events")
        item = GenerateItems.GenerateCalendarEvent(100)
        self.rep.commit()

        import osaf.contentmodel.Query as Query

        kind = self.rep.findPath('//parcels/osaf/contentmodel/calendar/CalendarEvent')
        queryKind = self.rep.findPath('//parcels/osaf/contentmodel/Query')

        log.debug("Creating query item")
        q = Query.Query('TestQuery',self.rep,queryKind)

        # a newly initialized query with no string has a size 0 rsult
        log.debug("Committing query item #1")
        self.assertEqual(0, len([i for i in q]))
        
        # give it a real query string
        log.debug("Setting data attribute")
        q.data = 'for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where True'
        log.debug("Committing query item #2")
        self.rep.commit()
        print "Test/query: %s, %s" % (q.data, q.itsUUID)
        self.assertEqual(1, len([i for i in q]))

        # test notification
        item = GenerateItems.GenerateCalendarEvent(100)
        self.rep.commit()
        self.assertEqual(2, len([i for i in q]))
        
        # see if we can reload stored data
        uuid = q.itsUUID
        q.onItemUnload() # hack?
        q = None
        self._reopenRepository()
        log.debug("reloading query item")
        q1 = self.rep.findUUID(uuid)
        self.assertEqual(2, len([i for i in q1]))

##         log.debug("Creating item collection")
##         ic = ItemCollection.NamedCollection()
##         print "Test/itemcollection", ic.itsUUID
##         ic.rule = q
##         #@@@@ why _ItemCollection__refresh?
##         log.debug("Refreshing query")
##         q._Query__refresh()
##         print type(q.__iter__())
##         log.debug("Refreshing item collection")
##         ic._ItemCollection__refresh()
##         print len(ic)
##         for i in ic:
##             print i


if __name__ == "__main__":
    unittest.main()
