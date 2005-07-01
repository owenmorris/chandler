"""
Test of a parcel file defining a kind and item of that kind, with
the item setting some attribute (Bug:1144)
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class KindAndItemTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testKindAndItemParcel(self):

        """ Test to see if you can declare a Kind bound to a Python class, as
        well as an item of that kind, inside a single parcel.xml file. See
        <http://bugzilla.osafoundation.org/show_bug.cgi?id=1144">.
        """

        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcel("http://testparcels.org/kindanditem")
        self.rep.commit()
        
        item = self.rep.findPath("//parcels/application/tests/testparcels/kindanditem/FirstOfItsKind")
        self.assert_(item)
        self.assert_(item.__dict__.has_key('initCalled'))


if __name__ == "__main__":
    unittest.main()
    
