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

        # Ensure the simple Parcel was created with the right Kind and attrs
        simpleParcel = self.rep.find("//parcels/simple")
        self.assertEqual(simpleParcel.kind,
         self.rep.find('//Schema/Core/Parcel'))
        self.assertEqual(simpleParcel.displayName, "Simple")
        self.assertEqual(simpleParcel.description, 
         "Simple Parcel Loader Test Schema")
        self.assertEqual(simpleParcel.version, "0.1")
        self.assertEqual(simpleParcel.author, 
         "Open Source Applications Foundation")

        # Ensure testAttribute was created with the right Kind and attrs
        testAttribute = self.rep.find("//parcels/simple/TestAttribute")
        self.assertEqual(testAttribute.kind,
         self.rep.find('//Schema/Core/Attribute'))
        self.assertEqual(testAttribute.type, 
         self.rep.find('//Schema/Core/String'))
        self.assertEqual(testAttribute.displayName, "Test Attribute")
        self.assertEqual(testAttribute.cardinality, "single")

        # Ensure testKind was created with the right Kind and attrs
        testKind = self.rep.find("//parcels/simple/TestKind")
        self.assertEqual(testKind.kind,
         self.rep.find('//Schema/Core/Kind'))
        self.assertEqual(testKind.displayName, "Test Kind")
        self.assertEqual(testKind.displayAttribute, "TestAttribute")

        # Ensure testAttribute is an attribute of testKind (and vice-versa)
        self.assert_(testKind.attributes.has_key(testAttribute.getUUID()))
        self.assert_(testAttribute.kinds.has_key(testKind.getUUID()))

        # Ensure subKind was created with the right Kind and attrs
        subKind = self.rep.find("//parcels/simple/SubKind")
        self.assertEqual(subKind.kind,
         self.rep.find('//Schema/Core/Kind'))
        self.assertEqual(subKind.displayName, "Subclass Test Kind")

        # Ensure testKind and subKind have the correct inheritence links
        self.assert_(subKind.superKinds.has_key(testKind.getUUID()))
        self.assert_(testKind.subKinds.has_key(subKind.getUUID()))

        # for i in subKind.iterAttributes():
        # for i in subKind.inheritedAttributes.keys():
        #     print i

if __name__ == "__main__":
    unittest.main()
