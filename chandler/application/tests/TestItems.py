"""
Item tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class ItemsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testItems(self):

        """ Ensure we can create items within a parcel file
        """

        self.manager.path.append(os.path.join(self.testdir, 'itemparcels'))
        self.loadParcels(["http://testparcels.org/items", "http://testparcels.org/super"])

        # Ensure the Parcel was created
        parcel = self.rep.findPath("//parcels/application/tests/itemparcels/items")
        self.assertEqual(parcel.itsKind,
         self.rep.findPath("//Schema/Core/Parcel"))

        # Ensure testInstances were created
        testInstance1 = self.rep.findPath("//parcels/application/tests/itemparcels/items/TestInstance1")
        self.assertEqual(testInstance1.itsKind,
         self.rep.findPath("//parcels/application/tests/itemparcels/items/Kind2"))

        testInstance2 = self.rep.findPath("//parcels/application/tests/itemparcels/items/TestInstance2")
        self.assertEqual(testInstance2.itsKind,
         self.rep.findPath("//parcels/application/tests/itemparcels/items/Kind2"))

        self.assertEqual(testInstance1.RefAttribute, testInstance2)
        self.assertEqual(testInstance1.StringAttribute, "XYZZY")
        self.assertEqual(testInstance1.EnumAttribute, "B")

        kind1 = self.rep.findPath("//parcels/application/tests/itemparcels/super/Kind1")
        self.assert_(kind1)
        kind2 = self.rep.findPath("//parcels/application/tests/itemparcels/items/Kind2")
        self.assert_(kind2)
        self.assert_(kind1 in kind2.superKinds)
        self.assert_(kind2 in kind1.subKinds)

if __name__ == "__main__":
    unittest.main()
