"""
Test merging of items
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
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
            ao.append(ko.newItem('ao_%02d' %(i), po))
        view.commit()

        view = self.rep.setCurrentView(main)
        for i in xrange(m):
            am.append(km.newItem('am_%02d' %(i), pm))
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

    def testRenameSameSame(self):
        self.rename('foo', 'foo')

    def testRenameSameDifferent(self):
        try:
            self.rename('foo', 'bar')
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.RENAME)

    def testMoveSame(self):
        self.move('foo', 'foo')

    def testMoveDifferent(self):
        try:
            self.move('foo', 'bar')
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.MOVE)
        else:
            self.assert_(False)

    def testCreateSameName(self):
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = self.rep['p']
        ko = self.rep.findPath('//Schema/Core/Item')
        ko.newItem('foo', po)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        km.newItem('foo', pm)

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.NAME)
        else:
            self.assert_(False)

    def testRenameDifferentSameName(self):
        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = self.rep['p']
        po['foo'].rename('baz')
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']
        pm['bar'].rename('baz')

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.NAME)
        else:
            self.assert_(False)

    def testMoveFirst(self):
        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = self.rep['p']
        po.placeChild(po['i1'], None)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']
        pm.placeChild(pm['i2'], None)
        main.commit()
        
        names = [c.itsName for c in pm.iterChildren()]
        self.assert_(names[0] == 'i1')
        self.assert_(len(names) == 4)

    def testChange1Remove1(self):

        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        km.newItem('q', self.rep)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = self.rep['p']
        po.placeChild(po['i1'], None)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']
        qm = self.rep['q']

        pm['i1'].move(qm)

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.MOVE)
        else:
            self.assert_(False)

    def testRemove1Change1(self):

        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        km.newItem('q', self.rep)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = self.rep['p']
        qo = self.rep['q']
        po['i1'].move(qo)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']

        pm.placeChild(pm['i1'], None)

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.MOVE)
        else:
            self.assert_(False)

    def testRemove1ChangeOther(self):

        pm = self.rep['p']
        km = self.rep.findPath('//Schema/Core/Item')
        km.newItem('q', self.rep)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        self.rep.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = self.rep['p']
        qo = self.rep['q']
        po['i1'].move(qo)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']
        pm['foo'].rename('baz')
        main.commit()

        names = [c.itsName for c in pm.iterChildren()]
        self.assert_(names[0] == 'baz')
        self.assert_(len(names) == 3)

    def testMergeNoOverlapRefCollections(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.writers.clear()
        main.commit()

    def testMergeOverlapRefCollections(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.BUG)
        else:
            self.assert_(False)

    def testMergeNoOverlapRV(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        k.movies.clear()
        main.commit()

        self.assert_(m.title == 'changed title')
        self.assert_(len(m.actors) == 0)

    def testMergeNoOverlapVR(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.writers.clear()
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        main.commit()

        self.assert_(m.title == 'changed title')
        self.assert_(len(m.writers) == 0)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
