__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems

from repository.util.URL import URL
from osaf.framework.webdav.Dav import DAV

import application.Parcel

class TestDAV(TestContentModel.ContentModelTestCase):
    """ Test Calendar Content Model """

    def testGeneratedEvents(self):

        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/webdav")
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")

        """ item exporting """
        testItem = GenerateItems.GenerateCalendarEvent(100)
        url = 'http://code-bear.com/dav/' + testItem.itsUUID.str16()
        a = DAV(url)
        a.put(testItem)
        a.put(testItem)
        print url

        """ item fetching """
        # fetch the item we put above
        testItem = DAV(url).get()
        testItem2 = DAV(url).get()
        testItem3 = DAV(url).get()

        print testItem, testItem2, testItem3
        """ export item collections """
        """
        ic = ItemCollection.NamedCollection()
        for index in range(10):
            ic.add(GenerateItems.GenerateCalendarEvent(100))

        a = DAV('http://code-bear.com/dav/' + str(ic.itsUUID)).putCollection(ic)

        newCollection = DAV(a).getCollection(ic)
        """
        self.rep.commit()

if __name__ == "__main__":
    unittest.main()
