"""
Test of Cloud copy
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
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

        # application.Parcel.PrintItem(parcel.itsPath, self.rep, recursive=True)

        cloud = self.manager.lookup("http://testparcels.org/clouds",
         "Widget/Cloud")
        widgetA = self.manager.lookup("http://testparcels.org/clouds/data",
         "widgetA")

        items = cloud.getItems(widgetA)
        expectedItems = [
            "//parcels/clouds/data/widgetA",
            "//parcels/clouds/data/widgetB",
            "//parcels/clouds/data/sprocketA",
            "//parcels/clouds/data/widgetC",
            "//parcels/clouds/data/sprocketB",
            "//parcels/clouds/data/sprocketC",
        ]

        for item in items:
            self.assert_(str(item.itsPath) in expectedItems)
            expectedItems.remove(str(item.itsPath))
        self.assertEquals(len(expectedItems), 0)

        copies = cloud.copyItems(widgetA)
        expectedItems = [
            "wA",
            "wB",
            "wC",
            "sA",
            "sB",
            "sC",
        ]
        for copy in copies:
            self.assert_(copy.xyzzy in expectedItems)
            expectedItems.remove(copy.xyzzy)
        self.assertEquals(len(expectedItems), 0)

if __name__ == "__main__":
    unittest.main()
