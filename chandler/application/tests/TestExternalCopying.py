"""
Item copying tests
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
from application.Parcel import PrintItem

class ExternalCopyingTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCopying(self):

        EXTERNALCOPYING = "http://testparcels.org/externalcopying"
        PARCELONE = "%s/one" % EXTERNALCOPYING
        PARCELTWO = "%s/two" % EXTERNALCOPYING
        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcels([EXTERNALCOPYING, PARCELONE, PARCELTWO])

        PrintItem("//parcels/application/tests/testparcels/externalcopying", self.rep, recursive=True)

        topLevelParcel = self.manager.lookup(EXTERNALCOPYING)
        self.assert_(topLevelParcel is not None)
        
        originalItem = topLevelParcel.findPath("one/kindOneInstance")
        self.assert_(originalItem is not None)
        
        copiedItem = topLevelParcel.findPath("one/kindTwoInstance/copiedInOne")
        self.assert_(copiedItem is not None)
        self.assertEquals(originalItem.displayName, copiedItem.displayName)

        copiedItem = topLevelParcel.findPath("two/otherKindTwoInstance/copiedKindOneInstance")
        self.assert_(copiedItem is not None)
        
        self.assertEquals(originalItem.displayName, copiedItem.displayName)

if __name__ == "__main__":
    unittest.main()
