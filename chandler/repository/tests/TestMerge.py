"""
Test merging of items
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.persistence.RepositoryError import MergeError
from repository.util.Path import Path


class TestMerge(RepositoryTestCase):
    """ Test item merging """

    def setUp(self):

        super(TestMerge, self).setUp()

        self.itemPath = Path('//Schema/Core/Item')

        kind = self.rep.find(self.itemPath)
        kind.newItem('p', self.rep)
        self.rep.commit()
        
    def merge(self, o, m):

        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        am = []

        oc = [c.itsName for c in pm.iterChildren()]
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = self.rep['p']
        ko = self.rep.findPath('//Schema/Core/Item')
        ao = []
        for i in xrange(o):
            ao.append(ko.itsKind.newItem('ao_%02d' %(i), po))
        view.commit()

        view = self.rep.setCurrentView(main)
        for i in xrange(m):
            am.append(km.itsKind.newItem('am_%02d' %(i), pm))
        main.commit()

        ic = [c.itsName for c in pm.iterChildren()]
        uc = oc[:]
        uc.extend([c.itsName for c in ao])
        uc.extend([c.itsName for c in am])
        self.assert_(ic == uc)

        c = pm._children

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
 
    def rename(self, o_name, m_name):

        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')

        cm = km.newItem('child', pm)
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = self.rep['p']
        co = po['child']
        co.rename(o_name)
        view.commit()

        view = self.rep.setCurrentView(main)
        cm.rename(m_name)
        main.commit()

    def move(self, o_name, m_name):

        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')

        cm = km.newItem('child', pm)
        km.newItem(m_name, self.rep)
        if o_name != m_name:
            km.newItem(o_name, self.rep)
            
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = self.rep['p']
        co = po['child']
        co.move(self.rep[o_name])
        view.commit()

        view = self.rep.setCurrentView(main)
        cm.move(self.rep[m_name])
        main.commit()

    def test1Merge1(self):
        self.rep.find(self.itemPath).newItem('c0', self.rep['p'])
        self.rep.commit()
        self.merge(1, 1)

    def test1Merge2(self):
        self.rep.find(self.itemPath).newItem('c0', self.rep['p'])
        self.rep.commit()
        self.merge(2, 2)

    def test1MergeN(self):
        self.rep.find(self.itemPath).newItem('c0', self.rep['p'])
        self.rep.commit()
        self.merge(5, 8)

    def test0Merge1(self):
        self.merge(1, 1)

    def test0Merge2(self):
        self.merge(2, 2)

    def test0MergeN(self):
        self.merge(6, 9)

    def testRenameSame(self):
        self.rename('foo', 'foo')

    def testRenameDifferent(self):
        try:
            self.rename('foo', 'bar')
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.RENAME)

    def testMoveSame(self):
        self.move('foo', 'foo')

    def testMoveDifferent(self):
        try:
            self.move('foo', 'bar')
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.MOVE)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
