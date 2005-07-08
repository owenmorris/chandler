"""
Test of Cloud copy
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class DependencyTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCloudCopy(self):

        """ Test to see if cloud copying works
        """

        self.manager.path.append(os.path.join(self.testdir,'testparcels'))
        self.loadParcel("http://testparcels.org/clouds/data")

        parcel = self.manager.lookup("http://testparcels.org/clouds")

        widgetA = self.manager.lookup("http://testparcels.org/clouds/data",
         "widgetA")

        # This is how you determine which items would get copied if you
        # were doing a cloud copy:
        trace={}
        items = widgetA.getItemCloud('test', trace=trace)

        expectedItems = [
            "//parcels/application/tests/testparcels/clouds/data/widgetA",
            "//parcels/application/tests/testparcels/clouds/data/widgetB",
            "//parcels/application/tests/testparcels/clouds/data/sprocketA",
            "//parcels/application/tests/testparcels/clouds/data/widgetC",
            "//parcels/application/tests/testparcels/clouds/data/sprocketB",
            "//parcels/application/tests/testparcels/clouds/data/sprocketC",
        ]


        for item in items:
            path = str(item.itsPath)
            self.assert_(path in expectedItems)
            expectedItems.remove(path)
        self.assertEquals(len(expectedItems), 0)


        # When you actually do a copy, here is how you can retrieve the set
        # of copies:
        copies = {}
        copy = widgetA.copy(cloudAlias="test", copies=copies)
        expectedItems = [
            "wA",
            "wB",
            "wC",
            "sA",
            "sB",
            "sC",
        ]
        for copy in copies.itervalues():
            self.assert_(copy.xyzzy in expectedItems)
            expectedItems.remove(copy.xyzzy)
        self.assertEquals(len(expectedItems), 0)

if __name__ == "__main__":
    unittest.main()
