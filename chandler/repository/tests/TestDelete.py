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
import tools.timing


class TestDelete(RepositoryTestCase):
    """ Test item deletion """

    def setUp(self):

        super(TestDelete, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

    def testDeleteItemsInCollection(self):

        tools.timing.reset()

        self._reopenRepository()
        k = self.rep.findPath('//CineGuide/KHepburn')
        for m in k.movies:
            tools.timing.begin("repository.TestDelete")
            m.delete()
            tools.timing.end("repository.TestDelete")

        self.assert_(len(k.movies) == 0)
        self.assert_(self.rep.check())

        self._reopenRepository()
        self.assert_(self.rep.check())

        tools.timing.results(verbose=False)

    def testCloudDelete(self):

        tools.timing.reset()

        k = self.rep.findPath('//CineGuide/KHepburn')
        k.delete(cloudAlias='remote')
        self.rep.commit()
        self.rep.check()
        self._reopenRepository()
        self.rep.check()

        tools.timing.results(verbose=False)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
