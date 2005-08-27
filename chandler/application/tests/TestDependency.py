"""
Dependency tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application
from application.Parcel import Parcel

class DependencyTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testDependency(self):

        """ Test to see if dependent parcels are correctly loaded
        """

        self.manager.path.append(os.path.join(self.testdir,'dependencyparcels'))
        self.loadParcel("http://testparcels.org/parcels/depA")

        view = self.rep.view
        view.commit()

        # Ensure depA Parcel was created with the right Kind and attrs
        depA = view.findPath("//parcels/application/tests/dependencyparcels/depA")
        self.assertEqual(depA.itsKind, Parcel.getKind(view))

        # Ensure testKind was created with the right Kind
        testKind = view.findPath("//parcels/application/tests/dependencyparcels/depA/TestKind")
        self.assertEqual(testKind.itsKind,
         view.findPath('//Schema/Core/Kind'))

        # Ensure depB Parcel was created with the right Kind and attrs
        depB = view.findPath("//parcels/application/tests/dependencyparcels/depB")
        self.assertEqual(depB.itsKind, Parcel.getKind(view))

        # Ensure depC Parcel was created with the right Kind and attrs
        depC = view.findPath("//parcels/application/tests/dependencyparcels/depB/depC")
        self.assertEqual(depC.itsKind, Parcel.getKind(view))

        # Ensure testAttribute was created with the right Kind
        testAttribute = view.findPath("//parcels/application/tests/dependencyparcels/depB/depC/TestAttribute")
        self.assertEqual(testAttribute.itsKind,
         view.findPath('//Schema/Core/Attribute'))

        # Ensure testAttribute is an attribute of testKind (and vice-versa)
        self.assert_(testKind.attributes.has_key(testAttribute.itsUUID))
        self.assert_(testAttribute.kinds.has_key(testKind.itsUUID))

if __name__ == "__main__":
    unittest.main()
