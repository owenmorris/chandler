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

        if not self.isOnline():
            return

        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/webdav")
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel")

        test404 = 0
        testPutGetItem = 0
        testExportCollection = 0
        testSyncCollection = 0

        if test404:
            noneItem = DAV('http://code-bear.com/dav/this_item_doesnt_exist').get()
            self.assert_(noneItem == None)

        if testPutGetItem:
            # item exporting
            testItem = GenerateItems.GenerateCalendarEvent(100)
            a = DAV('http://code-bear.com/dav/my_test_item')

            a.deleteResource()
            a.put(testItem)

            """ item fetching """
            testItem = a.get()

            print testItem


        if testExportCollection:
            # export item collections
            ic = ItemCollection.NamedCollection()
            for index in range(3):
                ic.add(GenerateItems.GenerateCalendarEvent(100))

            a = DAV('http://code-bear.com/dav/test_item_collection2')
            a.deleteResource()
            a.put(ic)

        if testSyncCollection:
            # try fetching the item collection.  it shouldn't have any changes
            a = DAV('http://code-bear.com/dav/test_item_collection2')
            ic = a.get()
            print '----------' + str(len(ic)) + '----------'

            # add new event to collection, commit, sync
            ic.add(GenerateItems.GenerateCalendarEvent(100))
            self.rep.commit()

            a.sync(ic)

if __name__ == "__main__":
    unittest.main()
