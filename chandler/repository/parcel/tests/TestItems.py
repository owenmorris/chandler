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
        sys.path.insert(1, parcelDir)
        LoadParcels(parcelDir, self.rep)
        self.rep.commit()

        def _check(path):
            # Ensure the Parcel was created
            parcel = self.rep.find("//parcels/%s" % path)
            self.assertEqual(parcel.kind,
             self.rep.find("//Schema/Core/Parcel"))

            # Ensure testAttribute was created with the right Kind and attrs
            testAttribute = self.rep.find("//parcels/%s/TestAttribute" % path)
            self.assertEqual(testAttribute.kind,
             self.rep.find("//Schema/Core/Attribute"))
            self.assertEqual(testAttribute.type, 
             self.rep.find("//Schema/Core/String"))

            # Ensure testKind was created with the right Kind and attrs
            testKind = self.rep.find("//parcels/%s/TestKind" % path)
            self.assertEqual(testKind.kind,
             self.rep.find("//Schema/Core/Kind"))

            # Ensure testAttribute is an attribute of testKind (and vice-versa)
            self.assert_(testKind.attributes.has_key(testAttribute.getUUID()))
            self.assert_(testAttribute.kinds.has_key(testKind.getUUID()))

            # Ensure testInstance was created
            testInstance = self.rep.find("//parcels/%s/TestInstance" % path)
            self.assertEqual(testInstance.kind,
             self.rep.find("//parcels/%s/TestKind" % path))


        # There are two versions of this test parcel:
        # "//parcels/items" uses //parcels/items as the default namespace
        # "//parcels/core" uses //Schema/Core as the default namespace
        _check("items")
        _check("core")

if __name__ == "__main__":
    unittest.main()
