"""
Basic Unit tests for contentmodel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
import repository.persistence.XMLRepository as XMLRepository
import repository.parcel.LoadParcels as LoadParcels
import OSAF.contentmodel.ContentModel as ContentModel
import application.Globals as Globals

class ContentItemTest(unittest.TestCase):

    def setUp(self):
        self.rootdir = os.environ['CHANDLERHOME']
        self.testdir = os.path.join(self.rootdir, 'Chandler', 'repository',
                                    'tests')

        # Create an empty repository
        self.rep = XMLRepository.XMLRepository(os.path.join(self.testdir,
                                                            '__repository__'))
        self.rep.create()

        # Load the schema of schemas
        schemaPack = os.path.join(self.rootdir, 'Chandler', 'repository',
                                  'packs', 'schema.pack')
        self.rep.loadPack(schemaPack)
        self.rep.commit()

        # Load the parcels
        Globals.repository = self.rep
        self.parceldir = os.path.join(self.rootdir, 'Chandler', 'parcels')
        LoadParcels.LoadParcels(self.parceldir, self.rep)

    def testContentItem(self):
        self.assert_(ContentModel.ContentItemParent)
        self.assert_(ContentModel.ContentItemKind)
        self.assert_(ContentModel.ProjectKind)
        self.assert_(ContentModel.GroupKind)

        genericContentItem = ContentModel.ContentItem()
        genericProject = ContentModel.Project()
        genericGroup = ContentModel.Group()

        self.assert_(genericContentItem)
        self.assert_(genericProject)
        self.assert_(genericGroup)

        self.assertEqual(genericContentItem.getItemParent(),
                         ContentModel.ContentItemParent)
        self.assertEqual(genericProject.getItemParent(),
                         ContentModel.ContentItemParent)
        self.assertEqual(genericGroup.getItemParent(),
                         ContentModel.ContentItemParent)
        
        self.assert_(genericContentItem.getItemPath())
        self.assert_(genericProject.getItemPath())
        self.assert_(genericGroup.getItemPath())

        genericContentItem.displayName = "Test Content Item"
        genericProject.name = "Test Project"
        genericGroup.name = "Test Group"

        self.assertEqual(genericProject.name, "Test Project")
        self.assertEqual(genericGroup.name, "Test Group")
        self.assertEqual(genericContentItem.displayName, "Test Content Item")

        genericContentItem.addValue('projects', genericProject)
        genericGroup.addValue('itemsInGroup', genericContentItem)

        self.assertEqual(len(genericProject.itemsInProject), 1)
        for item in genericProject.itemsInProject:
            self.assertEqual(item, genericContentItem)

        self.assertEqual(len(genericContentItem.projects), 1)
        for item in genericContentItem.projects:
            self.assertEqual(item, genericProject)

        self.assertEqual(len(genericContentItem.groups), 1)
        for item in genericContentItem.groups:
            self.assertEqual(item, genericGroup)

        self.assertEqual(len(genericGroup.itemsInGroup), 1)
        for item in genericGroup.itemsInGroup:
            self.assertEqual(item, genericContentItem)

        self.rep.commit()

    def tearDown(self):
        self.rep.close()
        self.rep.delete()

    def _reopenRepository(self):
        self.rep.commit()
        self.rep.close()
        self.rep.open()

if __name__ == "__main__":
    unittest.main()
