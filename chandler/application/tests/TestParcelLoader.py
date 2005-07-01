"""
Simple tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class SimpleParcelLoaderTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testLoadParcels(self):

        """ Load all parcels beneath testparcels directory and then check to
            make sure the repository contains what we expect.
        """

        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcel("http://testparcels.org/simple/data")

        self.rep.commit()

        # Ensure the simple Parcel was created with the right Kind and attrs
        simpleParcel = self.rep.findPath("//parcels/application/tests/testparcels/simple")
        self.assertEqual(simpleParcel.itsKind,
         self.rep.findPath('//Schema/Core/Parcel'))
        self.assertEqual(simpleParcel.displayName, "Simple Parcel")
        self.assertEqual(simpleParcel.description, 
         "Simple Parcel Loader Test Schema")
        self.assertEqual(simpleParcel.version, "0.1")
        self.assertEqual(simpleParcel.author, 
         "Open Source Applications Foundation")

        # Ensure testAttribute was created with the right Kind and attrs
        testAttribute = self.rep.findPath("//parcels/application/tests/testparcels/simple/TestAttribute")
        self.assertEqual(testAttribute.itsKind,
         self.rep.findPath('//Schema/Core/Attribute'))
        self.assertEqual(testAttribute.type, 
         self.rep.findPath('//Schema/Core/String'))
        self.assertEqual(testAttribute.displayName, "Test Attribute")
        self.assertEqual(testAttribute.cardinality, "single")

        # Ensure testKind was created with the right Kind and attrs
        testKind = self.rep.findPath("//parcels/application/tests/testparcels/simple/TestKind")
        self.assertEqual(testKind.itsKind,
         self.rep.findPath('//Schema/Core/Kind'))
        self.assertEqual(testKind.displayName, "Test Kind")
        self.assertEqual(testKind.displayAttribute, "TestAttribute")

        # Ensure testAttribute is an attribute of testKind (and vice-versa)
        self.assert_(testKind.attributes.has_key(testAttribute.itsUUID))
        self.assert_(testAttribute.kinds.has_key(testKind.itsUUID))

        # Ensure subKind was created with the right Kind and attrs
        subKind = self.rep.findPath("//parcels/application/tests/testparcels/simple/SubKind")
        self.assertEqual(subKind.itsKind,
         self.rep.findPath('//Schema/Core/Kind'))
        self.assertEqual(subKind.displayName, "Subclass Test Kind")

        # Ensure testKind and subKind have the correct inheritence links
        self.assert_(subKind.superKinds.has_key(testKind.itsUUID))
        self.assert_(testKind.subKinds.has_key(subKind.itsUUID))

        # Ensure that an empty defaultValue for a list attribute gets
        # sets properly
        # item1 = self.rep.findPath("//parcels/application/tests/testparcels/simple/data/item1")

        # Ensure that initialValue for a list/dict attributes are
        # set properly
        item3 = self.rep.findPath("//parcels/application/tests/testparcels/simple/data/item3")
        self.assertEqual(type(item3.ListAttribute).__name__, "PersistentList")
        self.assertEqual(type(item3.DictAttribute).__name__, "PersistentDict")
        # make sure this attribute isn't readonly:
        item3.ListAttribute.append("foo")
        # make sure an initialValue was set correctly:
        self.assert_(item3.TestAttribute == "XYZZY")


if __name__ == "__main__":
    unittest.main()
