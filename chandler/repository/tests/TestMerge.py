"""
Test merging of items
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestMerge(RepositoryTestCase):
    """ Test item merging """

    def setUp(self):

        super(TestMerge, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()
        
    def merge(self, o, m):

        cm = self.rep.findPath('//CineGuide')
        km = self.rep.findPath('//CineGuide/KHepburn')
        am = []
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        co = self.rep.findPath('//CineGuide')
        ko = self.rep.findPath('//CineGuide/KHepburn')
        ao = []
        for i in xrange(o):
            ao.append(ko.itsKind.newItem('ao_%02d' %(i), co))
        view.commit()

        view = self.rep.setCurrentView(main)
        for i in xrange(m):
            am.append(km.itsKind.newItem('am_%02d' %(i), cm))
        main.commit()

        c = cm._children

        for i in xrange(o - 1):
            self.assert_(c.nextKey(ao[i].itsUUID) == ao[i + 1].itsUUID)
        for i in xrange(1, o):
            self.assert_(c.previousKey(ao[i].itsUUID) == ao[i - 1].itsUUID)

        self.assert_(c.nextKey(ao[o - 1].itsUUID) == am[0].itsUUID)
        self.assert_(c.previousKey(am[0].itsUUID) == ao[o - 1].itsUUID)

        for i in xrange(m - 1):
            self.assert_(c.nextKey(am[i].itsUUID) == am[i + 1].itsUUID)
        for i in xrange(1, m):
            self.assert_(c.previousKey(am[i].itsUUID) == am[i - 1].itsUUID)

        self.assert_(c.lastKey() == am[m - 1].itsUUID)
        
    def testMergeOne(self):
        self.merge(1, 1)

    def testMergeTwo(self):
        self.merge(2, 2)

    def testMergeBunch(self):
        self.merge(5, 8)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
