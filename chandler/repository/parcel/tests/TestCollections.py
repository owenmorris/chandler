"""
Collection tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

from repository.parcel.Util import PrintItem
from repository.parcel.LoadParcels import LoadParcel
from repository.item.Item import Item

class CollectionsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCollections(self):

        parcelDir = os.path.join(self.testdir, 'testparcels', 'collections', 'data')
        parcelRoot = os.path.join(self.testdir, 'testparcels' )
        LoadParcel(parcelDir, '//parcels/collections/data', parcelRoot, self.rep)
        self.rep.commit()
        parcel = self.rep.findPath("//parcels/collections")
        parent = parcel.findPath("data/parent")
        child1 = parcel.findPath("data/child1")
        child2 = parcel.findPath("data/child2")

        # Make sure that parentBlock gets set to a default of None
        self.assertEqual(parent.parentBlock, None)

        child1.parentBlock = parent
        child2.parentBlock = parent

        if False:   # Set this to true to see an exception
            for child in parent.childrenBlocks:
                print child, child.parentBlock

if __name__ == "__main__":
    unittest.main()
