"""
Basic Unit tests for contentmodel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import repository.tests.RepositoryTestCase as RepositoryTestCase
import osaf.contentmodel.ContentModel as ContentModel

class ContentModelTestCase(RepositoryTestCase.RepositoryTestCase):
    def setUp(self):
        super(ContentModelTestCase,self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'parcels', \
         'osaf', 'contentmodel', 'tests')

        super(ContentModelTestCase,self)._openRepository(self)


    def isOnline(self):
        import socket
        try:
            a = socket.gethostbyname('www.osafoundation.org')
            return True
        except:
            return False

class ContentItemTest(ContentModelTestCase):

    def testContentItem(self):

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel")
        view = self.rep.view
        
        # Check that the globals got created by the parcel
        self.assert_(ContentModel.ContentItem.getDefaultParent(view))
        self.assert_(ContentModel.ContentItem.getKind(view))
        self.assert_(ContentModel.Project.getKind(view))
        self.assert_(ContentModel.Group.getKind(view))

        # Construct a sample item
        view = self.rep.view
        genericContentItem = ContentModel.ContentItem("genericContentItem",
                                                      view=view)
        genericProject = ContentModel.Project("genericProject", view=view)
        genericGroup = ContentModel.Group("genericGroup", view=view)

        # Check that each item was created
        self.assert_(genericContentItem)
        self.assert_(genericProject)
        self.assert_(genericGroup)

        # Check each item's parent, make sure it has a path
        contentItemParent = ContentModel.ContentItem.getDefaultParent(view)
        self.assertEqual(genericContentItem.itsParent, contentItemParent)
        self.assertEqual(genericProject.itsParent, contentItemParent)
        self.assertEqual(genericGroup.itsParent, contentItemParent)
        
        self.assertEqual(repr(genericContentItem.itsPath),
                         '//userdata/genericContentItem')
        self.assertEqual(repr(genericProject.itsPath),
                         '//userdata/genericProject')
        self.assertEqual(repr(genericGroup.itsPath),
                         '//userdata/genericGroup')

        # Set and test simple attributes
        genericContentItem.displayName = "Test Content Item"
        genericContentItem.context = "work"
        genericContentItem.body = "Notes appear in the body"

        self.assertEqual(genericContentItem.displayName, "Test Content Item")
        self.assertEqual(genericContentItem.context, "work")
        self.assertEqual(genericContentItem.body, "Notes appear in the body")
        self.assertEqual(genericContentItem.getItemDisplayName(), "Test Content Item")

        genericProject.name = "Test Project"
        genericGroup.name = "Test Group"


        self.assertEqual(genericProject.name, "Test Project")
        self.assertEqual(genericGroup.name, "Test Group")


        # Groups and projects aren't currently linked to Content Items
        # One of these days we'll have to figure out how to hook them
        # up or clean them out.  --Lisa

if __name__ == "__main__":
    unittest.main()
