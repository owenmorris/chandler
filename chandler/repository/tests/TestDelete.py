"""
Test deletion of items
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path


class TestDelete(RepositoryTestCase):
    """ Test item deletion """

    def setUp(self):

        super(TestDelete, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

    def testDeleteItemsInCollection(self):

        self._reopenRepository()
        k = self.rep.findPath('//CineGuide/KHepburn')
        for m in k.movies:
            m.delete()

        self.assert_(len(k.movies) == 0)
        self.assert_(self.rep.check())

        self._reopenRepository()
        self.assert_(self.rep.check())


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
