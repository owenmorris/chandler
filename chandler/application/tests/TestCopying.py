"""
Item copying tests
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
from application.Parcel import PrintItem

class CopyingTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCopying(self):

        COPYING = "http://testparcels.org/copying"
        DATA = "%s/data" % COPYING
        sys.path.append(os.path.join(self.testdir, 'testparcels'))
        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcels([COPYING, DATA])

        # PrintItem("//parcels/copying/data", self.rep, recursive=True)

        data = self.manager.lookup(DATA)
        parent = data.lookup("realParent")
        self.assert_(parent is not None)
        self.assert_(len(parent.myChildren) == 1)
        child = parent.myChildren.first()
        self.assertEquals(parent, child.myParent.first())
        grandChild = child.myChildren.first()
        self.assertEquals(child, grandChild.myParent.first())

if __name__ == "__main__":
    unittest.main()
