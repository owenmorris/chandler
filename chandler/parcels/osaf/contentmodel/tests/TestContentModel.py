"""
Basic Unit tests for contentmodel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import repository.parcel.LoadParcels as LoadParcels
import repository.tests.RepositoryTestCase as RepositoryTestCase
import osaf.contentmodel.ContentModel as ContentModel
import application.Globals as Globals

class ContentModelTestCase(RepositoryTestCase.RepositoryTestCase):
    def setUp(self):
        RepositoryTestCase.RepositoryTestCase.setUp(self)

        Globals.repository = self.rep
        self.parceldir = os.path.join(self.rootdir, 'chandler', 'parcels')

    def loadParcel(self, relPath):
        """
        load only the parcel we need (and it's dependencies)
        """
        uri = "//parcels/%s" % relPath
        uri = uri.replace(os.path.sep, "/")
        parcelDir = os.path.join(self.rootdir, 'chandler', 'parcels', relPath)
        LoadParcels.LoadParcel(parcelDir, uri, self.parceldir, self.rep)
        self.assert_(self.rep.find(uri))

class ContentItemTest(ContentModelTestCase):

    def testContentItem(self):

        self.loadParcel("osaf/contentmodel")

        # Check that the globals got created by the parcel
        self.assert_(ContentModel.ContentModel.getContentItemParent())
        self.assert_(ContentModel.ContentModel.getContentItemKind())
        self.assert_(ContentModel.ContentModel.getProjectKind())
        self.assert_(ContentModel.ContentModel.getGroupKind())

        # Construct a sample item
        genericContentItem = ContentModel.ContentItem("genericContentItem")
        genericProject = ContentModel.Project("genericProject")
        genericGroup = ContentModel.Group("genericGroup")

        # Check that each item was created
        self.assert_(genericContentItem)
        self.assert_(genericProject)
        self.assert_(genericGroup)

        # Check each item's parent, make sure it has a path
        contentItemParent = ContentModel.ContentModel.getContentItemParent()
        self.assertEqual(genericContentItem.itsParent, contentItemParent)
        self.assertEqual(genericProject.itsParent, contentItemParent)
        self.assertEqual(genericGroup.itsParent, contentItemParent)
        
        self.assertEqual(repr(genericContentItem.itsPath),
                         '//userdata/contentitems/genericContentItem')
        self.assertEqual(repr(genericProject.itsPath),
                         '//userdata/contentitems/genericProject')
        self.assertEqual(repr(genericGroup.itsPath),
                         '//userdata/contentitems/genericGroup')

        self.assertEqual(genericContentItem.whoAttribute, 'creator')
        self.assertEqual(genericContentItem.dateAttribute, 'createdOn')
        self.assertEqual(genericContentItem.aboutAttribute, 'displayName')

        # Set and test simple attributes
        genericContentItem.displayName = "Test Content Item"
        genericContentItem.context = "work"
        
        self.assertEqual(genericContentItem.displayName, "Test Content Item")
        self.assertEqual(genericContentItem.context, "work")
        self.assertEqual(genericContentItem.getAbout(), "Test Content Item")
        self.assertEqual(genericContentItem.getWho(), ' ')
        self.assertEqual(genericContentItem.getDate(), ' ')
        # Hmm.. someday we should make sure Who and Date always have values.
        
        genericProject.name = "Test Project"
        genericGroup.name = "Test Group"


        self.assertEqual(genericProject.name, "Test Project")
        self.assertEqual(genericGroup.name, "Test Group")


        # Groups and projects aren't currently linked to Content Items
        # One of these days we'll have to figure out how to hook them
        # up or clean them out.  --Lisa

if __name__ == "__main__":
    unittest.main()
