"""
Loads all parcels
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application
import tools.timing

class AllParcelsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testAllParcels(self):

        """
        Test to ensure all parcels load
        """
        tools.timing.begin("application.TestAllParcels")

        self.loadParcels()
        
        tools.timing.end("application.TestAllParcels")
        tools.timing.results()

        self.assert_( self.rep.check(), "Repository check failed -- see chandler.log" )

if __name__ == "__main__":
    unittest.main()
