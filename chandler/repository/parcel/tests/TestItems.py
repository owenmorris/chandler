"""
Item tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

from repository.parcel.LoadParcels import LoadParcels
from repository.item.Item import Item

class ItemsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testItems(self):

        """ Ensure we can create items within a parcel file
        """

        parcelDir = os.path.join(self.testdir, 'itemparcels')
        LoadParcels(parcelDir, self.rep)
        self.rep.commit()

        path = "items"

        # Ensure the Parcel was created
        parcel = self.rep.find("//parcels/%s" % path)
        self.assertEqual(parcel.kind,
         self.rep.find("//Schema/Core/Parcel"))

        # Ensure testInstances were created
        testInstance1 = self.rep.find("//parcels/%s/TestInstance1" % path)
        self.assertEqual(testInstance1.kind,
         self.rep.find("//parcels/%s/TestKind" % path))

        testInstance2 = self.rep.find("//parcels/%s/TestInstance2" % path)
        self.assertEqual(testInstance2.kind,
         self.rep.find("//parcels/%s/TestKind" % path))

        # print testInstance1.toXML()
        # print testInstance2.toXML()

        self.assertEqual(testInstance1.RefAttribute, testInstance2)
        self.assertEqual(testInstance1.StringAttribute, "XYZZY")
        self.assertEqual(testInstance1.EnumAttribute, "B")

if __name__ == "__main__":
    unittest.main()
