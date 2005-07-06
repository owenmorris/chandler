"""
Test of uuidOf
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class DependencyTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testUuidOf(self):

        """ Test to see if uuidOf works
        """

        self.manager.path.append(os.path.join(self.testdir,'testparcels'))
        self.loadParcel("http://testparcels.org/uuidof")

        myColl = self.manager.lookup("http://testparcels.org/uuidof", "myColl")

        # application.Parcel.PrintItem(myColl.itsPath, self.rep)

        for i in range(3):
            item = self.manager.lookup("http://testparcels.org/uuidof", 
             "item%d" % i)
            self.assert_(item.itsUUID in myColl.inclusions)

if __name__ == "__main__":
    unittest.main()
