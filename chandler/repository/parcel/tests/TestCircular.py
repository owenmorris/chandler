"""
Circular reference tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

from repository.parcel.Util import PrintItem
from repository.parcel.LoadParcels import LoadParcel
from repository.item.Item import Item

class CircularTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCircular(self):

        """
        Test to ensure circular references are handled
        """
        parcelDir = os.path.join(self.testdir, 'testparcels', 'circular', 'calendar')
        LoadParcel(parcelDir, '//parcels/circular/calendar', os.path.join(self.testdir, 'testparcels'), self.rep)
        parcelDir = os.path.join(self.testdir, 'testparcels', 'circular', 'contact')
        LoadParcel(parcelDir, '//parcels/circular/contact', os.path.join(self.testdir, 'testparcels'), self.rep)
        self.rep.commit()
        # PrintItem("//parcels", self.rep)

if __name__ == "__main__":
    unittest.main()
