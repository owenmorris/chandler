"""
Unit tests for item collections
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, random

import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems

class TestItemCollection(TestContentModel.ContentModelTestCase):

    def testCollectionEvents(self):

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        view = self.rep.view
        ic = ItemCollection.ItemCollection("TestCollectionEvents", view=view)
        for index in range(100):
            item = GenerateItems.GenerateCalendarEvent(view, 100)
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

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        log.debug("Generating calendar events")
        view = self.rep.view
        item = GenerateItems.GenerateCalendarEvent(view, 100)
        view.commit()

        log.debug("Creating ItemCollection")
        ic = ItemCollection.ItemCollection("TestRule",view=view)
        ic.subscribe()

        # a newly initialized query with no string has a size 0 rsult
        self.assertEqual(0, len(ic))
        
        # give it a real query string
        log.debug("Setting rule attribute")
        ic.rule = 'for i inevery "//parcels/osaf/contentmodel/calendar/CalendarEvent" where True'
        log.debug("Committing ItemCollection")
        view.commit()
        print "Rule/ItemCollection: %s, %s" % (ic.rule, ic.itsUUID)
        self.assertEqual(1, len([i for i in ic]))

        # test notification
        item = GenerateItems.GenerateCalendarEvent(view, 100)
        view.commit()
        self.assertEqual(2, len(ic))
        view.commit()

        # see if we can reload stored data
        uuid = ic.itsUUID
        ic = None
        self._reopenRepository()
        view = self.rep.view
        log.debug("reloading ItemCollection")
        ic = view.findUUID(uuid)
        self.assertEqual(2, len([i for i in ic]))

if __name__ == "__main__":
    unittest.main()
