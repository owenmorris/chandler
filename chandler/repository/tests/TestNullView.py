"""
Test nullRepositoryView and importing of items across views
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path
from repository.persistence.RepositoryView import nullRepositoryView


class TestNullView(RepositoryTestCase):
    """ Test nullRepositoryView """

    def setUp(self):

        super(TestNullView, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.kh = self.rep.findPath('//CineGuide/KHepburn')
        self.kh.movies.addIndex('t', 'attribute', attribute='title')
        self.rep.commit()

        nullRepositoryView.closeView()
        nullRepositoryView.openView()

    def testImport(self):

        nullRepositoryView.importItem(self.kh)

        self.assert_(self.kh.itsView is nullRepositoryView)
        self.assert_(self.kh.itsParent.itsView is nullRepositoryView)
        self.assert_(self.kh.itsKind.itsView is nullRepositoryView)

        self.assert_(self.rep.check())
        self.assert_(nullRepositoryView.check())

    def testCreate(self):

        nullRepositoryView.importItem(self.kh)
        m1 = self.kh.movies.first()
        m9 = m1.itsKind.newItem('m9', self.kh.itsParent)
        m9.title = 'ZZ'
        m9.director = m1.director
        self.assert_(m9.itsView is self.kh.itsView)
        self.assert_(self.kh.itsView is nullRepositoryView)

        kh = self.rep.findPath('//CineGuide/KHepburn')
        self.assert_(kh.itsView is self.rep.view)
        self.assert_(kh.itsView is not nullRepositoryView)

        kh.movies.append(m9)
        self.assert_(m9.itsView is kh.itsView)
        self.assert_(m9.itsView is self.rep.view)
        self.assert_(m9.itsView is not nullRepositoryView)
        self.assert_(kh.movies.last('t') is m9)

        self.assert_(self.rep.check())
        self.assert_(nullRepositoryView.check())


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
