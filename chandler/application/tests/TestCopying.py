"""
Item copying tests
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest
from application.Parcel import PrintItem

class CopyingTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):
    COPYING = "http://testparcels.org/copying"
    DATA = "%s/data" % COPYING

    def setUp(self):
        super(CopyingTestCase, self).setUp()
        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcels([self.COPYING, self.DATA])
        self.dataParcel = self.manager.lookup(self.DATA)

        

    def testCopying(self):

        # PrintItem("//parcels/application/tests/testparcels/copying/data", self.rep, recursive=True)

        parent = self.dataParcel.lookup("realParent")
        self.assert_(parent is not None)
        self.assert_(len(parent.myChildren) == 1)
        child = parent.myChildren.first()
        self.assertEquals(parent, child.myParent.first())
        grandChild = child.myChildren.first()
        self.assertEquals(child, grandChild.myParent.first())
        
        
    def testCopyOrder(self):
        orderTestItem = self.dataParcel.lookup("copyOrderTest")
        self.assert_(orderTestItem != None)
        orderedChildren = orderTestItem.myChildren
        self.assert_(len(orderedChildren) == 2)
        self.assertEquals(orderedChildren.first().itsName, "anotherCopiedChild")
        self.assertEquals(
                orderTestItem.myChildren.last(),
                self.dataParcel.lookup("templateChild0")
        )


if __name__ == "__main__":
    unittest.main()
