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
        


if __name__ == "__main__":
    unittest.main()
