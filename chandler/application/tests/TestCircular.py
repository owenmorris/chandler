"""
Circular reference tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class CircularTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCircular(self):

        """
        Test to ensure circular references are handled
        """
        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcels(
         ["http://testparcels.org/calendar", "http://testparcels.org/contact"]
        )
        self.rep.commit()

if __name__ == "__main__":
    unittest.main()
