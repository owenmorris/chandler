"""
Loads all parcels
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

from repository.parcel.Util import PrintItem
from repository.parcel.LoadParcels import LoadParcels
from repository.item.Item import Item

class AllParcelsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testAllParcels(self):

        """
        Test to ensure all parcels load
        """
        parcelDir = os.path.join(self.rootdir, 'chandler', 'parcels')
        LoadParcels(parcelDir, self.rep)
        PrintItem("//Schema", self.rep)
        PrintItem("//parcels", self.rep)

if __name__ == "__main__":
    unittest.main()
