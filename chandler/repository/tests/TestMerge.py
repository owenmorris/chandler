#   Copyright (c) 2004-2006 Open Source Applications Foundation
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
Test merging of items
"""

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

        view = self.rep.view
        item = view.find(TestMerge.itemPath)
        kind = view.find(TestMerge.kindPath)
        attribute = view.find(TestMerge.attributePath)

        kinds = item.newItem('kinds', view)
        item.newItem('cm', view)
        item.newItem('co', view)

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

        p.newItem('p', view)

        view.commit()
        
    def merge(self, o, m):

        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        am = []

        oc = [c.itsName for c in pm.iterChildren()]
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = view['p']
        ko = view.find(TestMerge.cPath)
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
        uc.extend([c.itsName for c in am])
        uc.extend([c.itsName for c in ao])
        self.assert_(ic == uc)

        c = pm._children

        for i in xrange(o - 1):
            self.assert_(c.nextKey(ao[i].itsUUID) == ao[i + 1].itsUUID)
        for i in xrange(1, o):
            self.assert_(c.previousKey(ao[i].itsUUID) == ao[i - 1].itsUUID)

        self.assert_(c.nextKey(am[m - 1].itsUUID) == ao[0].itsUUID)
        self.assert_(c.previousKey(ao[0].itsUUID) == am[m - 1].itsUUID)

        for i in xrange(m - 1):
            self.assert_(c.nextKey(am[i].itsUUID) == am[i + 1].itsUUID)
        for i in xrange(1, m):
            self.assert_(c.previousKey(am[i].itsUUID) == am[i - 1].itsUUID)

        self.assert_(c.lastKey() == ao[o - 1].itsUUID)
 
    def mergeRefs(self, o, m):

        main = self.rep.view
        pm = main['p']
        cm = main['cm']
        km = main.find(TestMerge.cPath)
        am = []

        oc = [c.itsName for c in pm.ap]
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = view['p']
        co = view['co']
        ko = view.find(TestMerge.cPath)
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
        uc.extend([c.itsName for c in am])
        uc.extend([c.itsName for c in ao])
        self.assert_(ic == uc)

        c = pm.ap

        for i in xrange(o - 1):
            self.assert_(c.nextKey(ao[i].itsUUID) == ao[i + 1].itsUUID)
        for i in xrange(1, o):
            self.assert_(c.previousKey(ao[i].itsUUID) == ao[i - 1].itsUUID)

        self.assert_(c.nextKey(am[m - 1].itsUUID) == ao[0].itsUUID)
        self.assert_(c.previousKey(ao[0].itsUUID) == am[m - 1].itsUUID)

        for i in xrange(m - 1):
            self.assert_(c.nextKey(am[i].itsUUID) == am[i + 1].itsUUID)
        for i in xrange(1, m):
            self.assert_(c.previousKey(am[i].itsUUID) == am[i - 1].itsUUID)

        self.assert_(c.lastKey() == ao[o - 1].itsUUID)
 
    def rename(self, o_name, m_name):

        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)

        cm = km.newItem('child', pm)
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = view['p']
        co = po['child']
        co.rename(o_name)
        view.commit()

        view = self.rep.setCurrentView(main)
        cm.rename(m_name)
        main.commit()

    def move(self, o_name, m_name):

        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)

        cm = km.newItem('child', pm)
        km.newItem(m_name, self.rep)
        if o_name != m_name:
            km.newItem(o_name, self.rep)
            
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        po = view['p']
        co = po['child']
        co.move(view[o_name])
        view.commit()

        view = self.rep.setCurrentView(main)
        cm.move(main[m_name])
        main.commit()

    def test1Merge1(self):
        view = self.rep.view
        view.find(TestMerge.cPath).newItem('c0', view['p'])
        view.commit()
        self.merge(1, 1)

    def test1Merge2(self):
        view = self.rep.view
        view.find(TestMerge.cPath).newItem('c0', view['p'])
        view.commit()
        self.merge(2, 2)

    def test1MergeN(self):
        view = self.rep.view
        view.find(TestMerge.cPath).newItem('c0', view['p'])
        view.commit()
        self.merge(5, 8)
        self.assert_(view.check(), 'view did not check out')

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
        po = view['p']
        ko = view.find(TestMerge.cPath)
        ko.newItem('foo', po)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('foo', pm)

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.NAME)
        else:
            self.assert_(False)

    def testRenameDifferentSameName(self):
        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = view['p']
        po['foo'].rename('baz')
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = main['p']
        pm['bar'].rename('baz')

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.NAME)
        else:
            self.assert_(False)

    def testMoveFirst(self):
        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = view['p']
        po.placeChild(po['i1'], None)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = main['p']
        pm.placeChild(pm['i2'], None)
        main.commit()
        
        names = [c.itsName for c in pm.iterChildren()]
        self.assert_(names[0] == 'i2')
        self.assert_(len(names) == 4)

    def testChange1Remove1(self):

        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('q', self.rep)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = view['p']
        po.placeChild(po['i1'], None)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = main['p']
        qm = main['q']

        pm['i1'].move(qm)

        try:
            main.commit()
        except MergeError, e:
            #print e
            self.assert_(e.getReasonCode() == MergeError.MOVE)
        else:
            self.assert_(main.check())
            #self.assert_(False)

    def testRemove1Change1(self):

        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('q', self.rep)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = view['p']
        qo = view['q']
        po['i1'].move(qo)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = main['p']

        pm.placeChild(pm['i1'], None)

        main.commit()
        self.assert_(main['q'].getItemChild('i1') != None)

    def testRemove1ChangeOther(self):

        main = self.rep.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('q', self.rep)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)
        po = view['p']
        qo = view['q']
        po['i1'].move(qo)
        view.commit()
        
        view = self.rep.setCurrentView(main)
        pm = main['p']
        pm['foo'].rename('baz')
        main.commit()

        names = [c.itsName for c in pm.iterChildren()]
        self.assert_(names[0] == 'baz')
        self.assert_(len(names) == 3)

    def testMergeNoOverlapRefCollections(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        self.assert_(main.check(), "main didn't check out")

    def testMergeOverlapRefCollections1(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        def onItemMerge(_self, code, attribute, value):
            return value

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

        type(m).onItemMerge = onItemMerge
        main.commit()
        del type(m).onItemMerge

        self.assertEquals(m.title, 'changed title in main')

    def testMergeOverlapVSame(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

    def testMergeOverlapVDifferentNoCallback(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title again'

        try:
            version = main.itsVersion
            main.commit()
        except MergeError:
            self.assert_(main.check())
            self.assert_(main.itsVersion == version)
            self.assertEquals(m.title, 'changed title again')

    def testMergeOverlapVDifferentWithCallback(self):

        def mergeFn(code, item, attribute, value):
            return item.getAttributeValue(attribute)

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title again'

        main.commit(mergeFn)
        self.assert_(main.check())
        self.assertEquals(m.title, 'changed title')

    def testMergeOverlapRSame(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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

    def testMergeOverlapRDifferent(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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
        m3 = k.movies.next(m2)
        m4 = k.movies.next(m3)
        m1.director = m4.director

        try:
            main.commit()
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.REF)

        self.assertEquals(m1.director, m4.director)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapRDifferentWithCallbackNew(self):

        def mergeFn(code, item, attribute, newValue):
            return newValue

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

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
        m3 = k.movies.next(m2)
        m4 = k.movies.next(m3)
        m1.director = m4.director

        main.commit(mergeFn)
        self.assertEquals(m1.director, m4.director)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapIndexes(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('n', 'numeric')
        k.movies.addIndex('t', 'attribute', attribute='title')
        main.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.title = 'Foo'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m4 = k.movies.next(m3)
        m4.title = 'Bar'
        main.commit()

        self.assert_(k.movies.getByIndex('t', 7) is m1)
        self.assert_(k.movies.getByIndex('t', 3) is m4)

    def makeC0(self):

        view = self.rep.view
        p = view['p']
        cm = view['cm']
        c0 = view.find(TestMerge.cPath).newItem('c0', cm)
        c0.ac = p
        view.commit()

    def testRefs1Merge1(self):

        view = self.rep.view
        self.makeC0()
        self.mergeRefs(1, 1)
        self.assert_(view.check(), 'view did not check out')

    def testRefs1Merge2(self):

        view = self.rep.view
        self.makeC0()
        self.mergeRefs(2, 2)
        self.assert_(view.check(), 'view did not check out')

    def testRefs1MergeN(self):

        view = self.rep.view
        self.makeC0()
        self.mergeRefs(5, 8)
        self.assert_(view.check(), 'view did not check out')

    def testMergeOverlapVRef(self):

        def mergeFn(code, item, attribute, newValue):
            oldValue = getattr(item, attribute)
            return newValue

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        c['m2'].next = m1
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        c['m2'].next = c['m4']

        main.commit(mergeFn)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeSetVRef(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        main.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        m1.title = 'foo'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        c['m2'].next = m1

        main.commit()
        self.assert_(main.check(), 'main view did not check out')

    def testMergeSubIndex(self):

        main = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        main.loadPack(cineguidePack)
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('t', 'value', attribute='title', ranges=[(0, 1)])
        m1 = k.movies.first()
        m1.director.directed.addIndex('T', 'subindex',
                                      superindex=(k, 'movies', 't'))
        main.commit()

        view = self.rep.createView('view')
        main = self.rep.setCurrentView(view)

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        m1.title = 'Foo'
        view.commit()
        
        view = self.rep.setCurrentView(main)
        k = main.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m2.director = m1.director
        m3.delete()

        main.commit()
        self.assert_(main.check(), 'main view did not check out')


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
