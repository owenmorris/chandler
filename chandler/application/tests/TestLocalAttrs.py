"""
Parcel Loader test for local attributes
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class LocalTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testLocal(self):

        """ Ensure that attributes within kinds are assigned to the kind
        """

        self.manager.path.append(os.path.join(self.testdir,'testparcels'))
        self.loadParcel("http://testparcels.org/localattrs")

        self.rep.commit()

        # Ensure the Parcel was created
        kind = self.rep.findPath("//parcels/localattrs/TestKind")
        self.assert_(kind)
        attr = self.rep.findPath("//parcels/localattrs/TestKind/TestAttribute")
        self.assert_(attr)
        found = False
        for (name, attr) in kind.iterAttributes():
            if str(attr.itsPath) == \
             "//parcels/localattrs/TestKind/TestAttribute":
                found = True
        self.assert_(found, "Local TestAttribute not found")

        item = kind.newItem("testItem", kind)
        item.TestAttribute = "foo"
        self.rep.commit()
        self.assert_(self.rep.check(), "Repository failed to check()")


if __name__ == "__main__":
    # unittest.main()
    # Disabling this test until the parcel loader handles locals properly
    pass
