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


    def testDuplicateNamespace(self):
        """
        Test to ensure we raise a ParcelException when parsing a
        two parcels that have the same <namespace>.
        """

        # Point the parcel manager at badnamespaceparcels/duplicate.
        #
        # Note: Because the parcel.xml namespace scheme allows any
        # parcel.xml file could be associated with any namespace
        # URI, the parcel manager has to know all namespace info for
        # every parcel.xml file in its path before it can update the
        # repository for the namespaces requested in loadParcels(). As
        # a result, if any parcel in the manager's path has a namespace-related
        # error, this will be raised regardless of what namespaces were
        # requested.
        #
        # The upshot of all this for the parcel load unit tests is that
        # the namespace error parcels need to live in a different directory
        # tree from all other test parcels. And when testing namespace errors,
        # we need to have the loader's path point at exactly the tree
        # containing the error we want to test.
        #
        self.manager.path.append(
            os.path.join(
                os.path.dirname(ParcelLoaderTestCase.__file__),
                'badnamespaceparcels',
                'duplicate'
                )
            )

        # We could actually pass in any namespace to loadParcels here (see
        # note above).
        self.assertRaises(application.Parcel.ParcelException, self.loadParcels, ["http://testparcels.org/dupnamespace"])
        
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
