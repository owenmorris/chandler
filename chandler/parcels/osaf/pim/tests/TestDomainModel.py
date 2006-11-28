#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Basic Unit tests for pim
"""

import unittest, os

import repository.tests.RepositoryTestCase as RepositoryTestCase
import osaf.pim.items as items
from i18n.tests import uw

class DomainModelTestCase(RepositoryTestCase.RepositoryTestCase):
    def setUp(self):
        super(DomainModelTestCase, self)._setup()

        self.testdir = os.path.join(self.rootdir, 'parcels', \
         'osaf', 'pim', 'tests')

        super(DomainModelTestCase, self)._openRepository()


    def isOnline(self):
        import socket
        try:
            a = socket.gethostbyname('www.osafoundation.org')
            return True
        except:
            return False

class ContentItemTest(DomainModelTestCase):

    def testContentItem(self):

        self.loadParcel("osaf.pim")
        view = self.rep.view

        # Check that the globals got created by the parcel
        self.assert_(items.ContentItem.getDefaultParent(view))
        self.assert_(items.ContentItem.getKind(view))
        self.assert_(items.Project.getKind(view))
        self.assert_(items.Group.getKind(view))

        # Construct a sample item
        view = self.rep.view
        genericContentItem = items.ContentItem("genericContentItem",
                                                      itsView=view)
        genericProject = items.Project("genericProject", itsView=view)
        genericGroup = items.Group("genericGroup", itsView=view)

        # Check that each item was created
        self.assert_(genericContentItem)
        self.assert_(genericProject)
        self.assert_(genericGroup)

        # Check each item's parent, make sure it has a path
        contentItemParent = items.ContentItem.getDefaultParent(view)
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
        genericContentItem.displayName = uw("Test Content Item")
        genericContentItem.context = uw("work")
        genericContentItem.body = uw("Notes appear in the body")

        self.assertEqual(genericContentItem.displayName, uw("Test Content Item"))
        self.assertEqual(genericContentItem.context, uw("work"))
        self.assertEqual(genericContentItem.body, uw("Notes appear in the body"))

        # Test Calculated basedOn
        self.assertEqual(genericContentItem.getBasedAttributes('body'), ('body',))

        genericProject.name = uw("Test Project")
        genericGroup.name = uw("Test Group")


        self.assertEqual(genericProject.name, uw("Test Project"))
        self.assertEqual(genericGroup.name, uw("Test Group"))


        # Groups and projects aren't currently linked to Content Items
        # One of these days we'll have to figure out how to hook them
        # up or clean them out.  --Lisa

if __name__ == "__main__":
    unittest.main()
