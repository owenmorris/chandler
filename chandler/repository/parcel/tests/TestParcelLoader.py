"""
Simple tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import repository.parcel.LoadParcels as LoadParcels

class SimpleParcelLoaderTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testLoadParcels(self):

        """ Load all parcels beneath testparcels directory and then check to
            make sure the repository contains what we expect.
        """

        parcelDir = os.path.join(self.testdir, 'testparcels')
        sys.path.insert(1, parcelDir)
        LoadParcels.LoadParcels(parcelDir, self.rep)
        self.rep.commit()

        simpleParcel = self.rep.find("//parcels/simple")
        self.assertEqual(simpleParcel.kind,
         self.rep.find('//Schema/Core/Parcel'))

        testAttribute = self.rep.find("//parcels/simple/TestAttribute")
        self.assertEqual(testAttribute.kind,
         self.rep.find('//Schema/Core/Attribute'))

        testKind = self.rep.find("//parcels/simple/TestKind")
        self.assertEqual(testKind.kind,
         self.rep.find('//Schema/Core/Kind'))


if __name__ == "__main__":
    unittest.main()
