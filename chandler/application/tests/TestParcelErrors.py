"""
Error handling tests for the Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
from application.Parcel import ParcelException as ParcelException
import application

ITSNAME = "parcel:application.tests.testparcels.errors.itsname"
DUPITEMS = "parcel:application.tests.testparcels.errors.dupitems"

class ParcelErrorTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def setUp(self):
    
        super(ParcelErrorTestCase, self).setUp()

        self.manager.path.append(
            os.path.join(
                os.path.dirname(ParcelLoaderTestCase.__file__),
                'testparcels',
                'errors'
            ))

    def testItsnameParcel(self):
        """
        Test to ensure we raise a ParcelException when parsing a parcel
        whose itsName doesn't match the last component of its repository
        path.
        """

        self.assertRaises(ParcelException, self.loadParcels, [ITSNAME])
        
    def testDuplicateItems(self):
        """
        Test to ensure we raise a ParcelException when parsing a parcel
        that attempts to define the same Item twice.
        """

        self.assertRaises(ParcelException, self.loadParcels, [DUPITEMS])

if __name__ == "__main__":
    unittest.main()
