"""
Dependency tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

from repository.parcel.LoadParcels import LoadParcels
from repository.item.Item import Item

class DependencyTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testDependency(self):

        """ Test to see if dependent parcels are correctly loaded
        """

        parcelDir = os.path.join(self.testdir, 'dependencyparcels')
        sys.path.insert(1, parcelDir)
        LoadParcels(parcelDir, self.rep)
        self.rep.commit()

        # Ensure depA Parcel was created with the right Kind and attrs
        depA = self.rep.find("//parcels/depA")
        self.assertEqual(depA.kind,
         self.rep.find('//Schema/Core/Parcel'))

        # Ensure testKind was created with the right Kind
        testKind = self.rep.find("//parcels/depA/TestKind")
        self.assertEqual(testKind.kind,
         self.rep.find('//Schema/Core/Kind'))

        # Ensure depB Parcel was created with the right Kind and attrs
        depB = self.rep.find("//parcels/depB")
        self.assertEqual(depB.kind,
         self.rep.find('//Schema/Core/Parcel'))

        # Ensure depC Parcel was created with the right Kind and attrs
        depC = self.rep.find("//parcels/depB/depC")
        self.assertEqual(depC.kind,
         self.rep.find('//Schema/Core/Parcel'))

        # Ensure testAttribute was created with the right Kind
        testAttribute = self.rep.find("//parcels/depB/depC/TestAttribute")
        self.assertEqual(testAttribute.kind,
         self.rep.find('//Schema/Core/Attribute'))

        # Ensure testAttribute is an attribute of testKind (and vice-versa)
        self.assert_(testKind.attributes.has_key(testAttribute.getUUID()))
        self.assert_(testAttribute.kinds.has_key(testKind.getUUID()))

if __name__ == "__main__":
    unittest.main()
