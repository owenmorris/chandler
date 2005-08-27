"""
Item tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application
from application.Parcel import Parcel

class ItemsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testItems(self):

        """ Ensure we can create items within a parcel file
        """

        self.manager.path.append(os.path.join(self.testdir, 'itemparcels'))
        self.loadParcels(["http://testparcels.org/items", "http://testparcels.org/super"])

        view = self.rep.view
        # Ensure the Parcel was created
        parcel = view.findPath("//parcels/application/tests/itemparcels/items")
        self.assertEqual(parcel.itsKind, Parcel.getKind(view))

        # Ensure testInstances were created
        testInstance1 = view.findPath("//parcels/application/tests/itemparcels/items/TestInstance1")
        self.assertEqual(testInstance1.itsKind,
         view.findPath("//parcels/application/tests/itemparcels/items/Kind2"))

        testInstance2 = view.findPath("//parcels/application/tests/itemparcels/items/TestInstance2")
        self.assertEqual(testInstance2.itsKind,
         view.findPath("//parcels/application/tests/itemparcels/items/Kind2"))

        self.assertEqual(testInstance1.RefAttribute, testInstance2)
        self.assertEqual(testInstance1.StringAttribute, "XYZZY")
        self.assertEqual(testInstance1.EnumAttribute, "B")

        kind1 = view.findPath("//parcels/application/tests/itemparcels/super/Kind1")
        self.assert_(kind1)
        kind2 = view.findPath("//parcels/application/tests/itemparcels/items/Kind2")
        self.assert_(kind2)
        self.assert_(kind1 in kind2.superKinds)
        self.assert_(kind2 in kind1.subKinds)

if __name__ == "__main__":
    unittest.main()
