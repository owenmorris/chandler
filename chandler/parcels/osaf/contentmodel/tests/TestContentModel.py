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

        def checkGroupItemLink(group, contentItem):
            self.assertEqual(len(contentItem.groups), 1)
            for item in contentItem.groups:
                self.assertEqual(item, group)
                
            self.assertEqual(len(group.itemsInGroup), 1)
            for item in group.itemsInGroup:
                self.assertEqual(item, contentItem)

        def checkProjectItemLink(project, contentItem):
            self.assertEqual(len(project.itemsInProject), 1)
            for item in project.itemsInProject:
                self.assertEqual(item, contentItem)
                
            self.assertEqual(len(contentItem.projects), 1)
            for item in contentItem.projects:
                self.assertEqual(item, project)

        
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

        # These attributes should be empty, but should not be missing
        self.assert_(not genericContentItem.projects)
        self.assert_(not genericContentItem.groups)
        self.assert_(not genericProject.name)
        self.assert_(not genericProject.itemsInProject)
        self.assert_(not genericGroup.name)
        self.assert_(not genericGroup.itemsInGroup)

        # Set and test simple attributes
        genericContentItem.displayName = "Test Content Item"
        genericProject.name = "Test Project"
        genericGroup.name = "Test Group"

        self.assertEqual(genericProject.name, "Test Project")
        self.assertEqual(genericGroup.name, "Test Group")
        self.assertEqual(genericContentItem.displayName, "Test Content Item")

        # Link the contentItem to the project
        genericContentItem.projects.append(genericProject)
        checkProjectItemLink(genericProject, genericContentItem)
        
        # Link the group to the contentItem
        genericGroup.itemsInGroup.append(genericContentItem)
        checkGroupItemLink(genericGroup, genericContentItem)

        self._reopenRepository()

        # Look to see that projects and groups links still work
        
        project = self.rep.find("//userdata/contentitems/genericProject")
        group = self.rep.find("//userdata/contentitems/genericGroup")
        contentItem = self.rep.find("//userdata/contentitems/genericContentItem")

        checkProjectItemLink(project, contentItem)
        checkGroupItemLink(group, contentItem)

if __name__ == "__main__":
    unittest.main()
