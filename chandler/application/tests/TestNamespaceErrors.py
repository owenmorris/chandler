"""
Error handling tests for the Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
from application.Parcel import *
import application

class NamespaceErrorTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):
        
    def testUndefinedNamespace(self):
        """
        Test to ensure we raise a NamespaceException when parsing a
        two parcels that have the same <namespace>.
        """

        # Make sure the parcel manager loads the contents of testparcels.
        self.manager.path.append(
            os.path.join(
                os.path.dirname(ParcelLoaderTestCase.__file__),
                'testparcels'
                )
            )

        # Now, try ask for a namespace that isn't present in any
        # of the parcel.xml files.
        self.assertRaises(application.Parcel.NamespaceUndefinedException, self.loadParcels, ["http://nosuchparcel.example.com"])

if __name__ == "__main__":
    unittest.main()
