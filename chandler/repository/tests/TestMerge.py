"""
Test merging of items
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
from datetime import date
from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.persistence.RepositoryError import MergeError
from repository.util.Path import Path


class TestMerge(RepositoryTestCase):
    """ Test item merging """

    itemPath = Path('//Schema/Core/Item')
    kindPath = Path('//Schema/Core/Kind')
    attributePath = Path('//Schema/Core/Attribute')
    cPath = Path('//kinds/c')
    
    def setUp(self):

        super(TestMerge, self).setUp()

        item = self.rep.find(TestMerge.itemPath)
        kind = self.rep.find(TestMerge.kindPath)
        attribute = self.rep.find(TestMerge.attributePath)

        kinds = item.newItem('kinds', self.rep)
        item.newItem('cm', self.rep)
        item.newItem('co', self.rep)

        p = kind.newItem('p', kinds)
        p.addValue('superKinds', item)
        c = kind.newItem('c', kinds)
        c.addValue('superKinds', item)

        ap = attribute.newItem('ap', p)
        ap.otherName = 'ac'
        ap.cardinality = 'list'
        p.addValue('attributes', ap, alias='ap')

        ac = attribute.newItem('ac', c)
        ac.otherName = 'ap'
        ac.cardinality = 'single'
        c.addValue('attributes', ac, alias='ac')

        p.newItem('p', self.rep)

        self.rep.commit()
        
    def merge(self, o, m):

        pm = self.rep['p']
        km = self.rep.find(TestMerge.cPath)
        am = []

        oc = [c.itsName for c in pm.iterChildren()]
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = self.rep['p']
        ko = self.rep.find(TestMerge.cPath)
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
 
    def mergeRefs(self, o, m):

        pm = self.rep['p']
        cm = self.rep['cm']
        km = self.rep.find(TestMerge.cPath)
        am = []

        oc = [c.itsName for c in pm.ap]
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = self.rep['p']
        co = self.rep['co']
        ko = self.rep.find(TestMerge.cPath)
        ao = []
        for i in xrange(o):
            c = ko.newItem('ao_%02d' %(i), co)
            c.ac = po
            #po.ap.dir()
            ao.append(c)
        view.commit()

        view = self.rep.setCurrentView(main)
        for i in xrange(m):
            c = km.newItem('am_%02d' %(i), cm)
            c.ac = pm
            #pm.ap.dir()
            am.append(c)
        main.commit()

        ic = [c.itsName for c in pm.ap]
        uc = oc[:]
        uc.extend([c.itsName for c in ao])
        uc.extend([c.itsName for c in am])
        self.assert_(ic == uc)

        c = pm.ap

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
        km = self.rep.find(TestMerge.cPath)

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
        km = self.rep.find(TestMerge.cPath)

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
        self.rep.find(TestMerge.cPath).newItem('c0', self.rep['p'])
        self.rep.commit()
        self.merge(1, 1)

    def test1Merge2(self):
        self.rep.find(TestMerge.cPath).newItem('c0', self.rep['p'])
        self.rep.commit()
        self.merge(2, 2)

    def test1MergeN(self):
        self.rep.find(TestMerge.cPath).newItem('c0', self.rep['p'])
        self.rep.commit()
        self.merge(5, 8)
        self.assert_(self.rep.view.check(), 'view did not check out')

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
        ko = self.rep.find(TestMerge.cPath)
        ko.newItem('foo', po)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = self.rep['p']
        km = self.rep.find(TestMerge.cPath)
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
        km = self.rep.find(TestMerge.cPath)
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
        km = self.rep.find(TestMerge.cPath)
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
        km = self.rep.find(TestMerge.cPath)
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
        km = self.rep.find(TestMerge.cPath)
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

        main.commit()
        self.assert_(main['q'].getItemChild('i1') != None)

    def testRemove1ChangeOther(self):

        pm = self.rep['p']
        km = self.rep.find(TestMerge.cPath)
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

    def testMergeOverlapRefCollections1(self):

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
        main.commit()

        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapRefCollections2(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        vl = len(k.movies)
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m2.title = 'm2title'
        m3.title = 'm3title'
        k.born = b2 = date(1908, 05, 12)
        tf = m3.title
        k.movies.placeItem(m3, None)
        view.commit()

        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        ml = len(k.movies)
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m2.frenchTitle = 'm2titre'
        m3.frenchTitle = 'm3titre'
        k.died = d2 = date(2003, 06, 30)
        tl = m2.title
        k.movies.placeItem(m2, k.movies.last())
        main.commit()

        self.assert_(main.check(), 'main view did not check out')
        self.assert_(len(k.movies) == ml, 'length changed')
        self.assert_(len(k.movies) == vl, 'length changed')
        self.assert_(str(k.born) == str(b2))
        self.assert_(str(k.died) == str(d2))
        self.assert_(m2.title == 'm2title')
        self.assert_(m2.frenchTitle == 'm2titre')
        self.assert_(m3.title == 'm3title')
        self.assert_(m3.frenchTitle == 'm3titre')

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
        self.assert_(main.check(), 'main check failed')

    def testMergeNoOverlapVRSingle(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        m2 = view.findPath('//CineGuide/m2')
        m4 = view.findPath('//CineGuide/m4')
        m2.next = m4
        view.commit()
        self.assert_(view.check(), 'view check failed')
        
        view = self.rep.setCurrentView(main)
        m2 = main.findPath('//CineGuide/m2')
        m2.title = 'changed title'
        main.commit()

        m2 = main.findPath('//CineGuide/m2')
        m4 = main.findPath('//CineGuide/m4')
        self.assert_(m2.title == 'changed title')
        self.assert_(m2.next is m4)
        self.assert_(m4.previous is m2)
        self.assert_(main.check(), 'main check failed')

    def testMergeNoOverlapVRMulti(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m6 = view.findPath('//CineGuide/m6')
        m6.writers = k.movies.first().writers
        m6.frenchTitle = 'titre change'
        view.commit()
        self.assert_(view.check(), 'view check failed')
        
        view = self.rep.setCurrentView(main)
        m6 = main.findPath('//CineGuide/m6')
        m6.title = 'changed title'
        main.commit()

        m6 = main.findPath('//CineGuide/m6')
        self.assert_(m6.title == 'changed title')
        self.assert_(m6.frenchTitle == 'titre change')
        self.assert_(len(m6.writers) == 3)
        self.assert_(main.check(), 'main check failed')

    def testMergeOverlapV(self):

        def mergeFn(code, item, attribute, value):
            return item.getAttributeValue(attribute)

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title in view'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title in main'
        main.commit(mergeFn)

        self.assertEquals(m.title, 'changed title in main')

    def testMergeOverlapVSame(self):

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
        m.title = 'changed title'
        main.commit()

        self.assertEquals(m.title, 'changed title')

    def testMergeOverlapRSame(self):

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.director = m2.director
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.director = m2.director
        main.commit()

        self.assertEquals(m1.director, m2.director)
        self.assert_(main.check(), 'main view did not check out')

#    def testMergeOverlapR(self):
#
#        def mergeFn(code, item, attribute, value):
#            return item.getAttributeValue(attribute)
#
#        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
#                                     'cineguide.pack')
#        self.rep.loadPack(cineguidePack)
#        self.rep.commit()
#
#        view = self.rep.createView('view')
#        main = self.rep.setCurrentView(view)
#
#        k = view.findPath('//CineGuide/KHepburn')
#        m1 = k.movies.first()
#        m2 = k.movies.next(m1)
#        m1.director = m2.director
#        view.commit()
#        
#        view = self.rep.setCurrentView(main)
#        k = main.findPath('//CineGuide/KHepburn')
#        m1 = k.movies.first()
#        m2 = k.movies.next(m1)
#        m3 = k.movies.next(m2)
#        m4 = k.movies.next(m3)
#        m1.director = m4.director
#        main.commit(mergeFn)
#
#        self.assertEquals(m1.director, m2.director)

    def makeC0(self):

        p = self.rep['p']
        cm = self.rep['cm']
        c0 = self.rep.find(TestMerge.cPath).newItem('c0', cm)
        c0.ac = p
        self.rep.commit()

    def testRefs1Merge1(self):

        self.makeC0()
        self.mergeRefs(1, 1)
        self.assert_(self.rep.view.check(), 'view did not check out')

    def testRefs1Merge2(self):

        self.makeC0()
        self.mergeRefs(2, 2)
        self.assert_(self.rep.view.check(), 'view did not check out')

    def testRefs1MergeN(self):

        self.makeC0()
        self.mergeRefs(5, 8)
        self.assert_(self.rep.view.check(), 'view did not check out')


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
