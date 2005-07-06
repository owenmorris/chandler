"""
Collection tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

import application

class CollectionsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testCollections(self):

        self.manager.path.append(os.path.join(self.testdir, 'testparcels'))
        self.loadParcels( ["parcel:application.tests.testparcels.collections.data"] )
        self.rep.commit()
        parcel = self.rep.findPath("//parcels/application/tests/testparcels/collections")
        parent = parcel.findPath("data/parent")
        child1 = parcel.findPath("data/child1")
        child2 = parcel.findPath("data/child2")

        # Make sure that parentBlock gets set to a default of None
        self.assertEqual(parent.parentBlock, None)

        child1.parentBlock = parent
        child2.parentBlock = parent

        for child in parent.childrenBlocks:
            self.assertEqual(child.parentBlock, parent)

        self.assertEqual(child1, parent.getValue('foo', alias='one'))
        self.assertEqual(child2, parent.getValue('foo', alias='two'))


if __name__ == "__main__":
    unittest.main()
