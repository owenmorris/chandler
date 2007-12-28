#   Copyright (c) 2004-2007 Open Source Applications Foundation
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

import unittest, os, logging
from datetime import date
from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
from chandlerdb.persistence.RepositoryError import MergeError
from chandlerdb.persistence.RepositoryView import otherViewWins
from chandlerdb.util.Path import Path
from chandlerdb.item.Sets import Set, KindSet, Intersection
from chandlerdb.item.ItemError import ChildNameError

class TestMerge(RepositoryTestCase):
    """ Test item merging """

    itemPath = Path('//Schema/Core/Item')
    kindPath = Path('//Schema/Core/Kind')
    attributePath = Path('//Schema/Core/Attribute')
    cPath = Path('//kinds/c')
    
    def setUp(self):

        super(TestMerge, self).setUp()

        view = self.view
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

        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        am = []

        oc = [c.itsName for c in pm.iterChildren()]
        view = self.rep.createView('view')

        po = view['p']
        ko = view.find(TestMerge.cPath)
        ao = []
        for i in xrange(o):
            ao.append(ko.newItem('ao_%02d' %(i), po))
        view.commit()

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

        main = self.view
        pm = main['p']
        cm = main['cm']
        km = main.find(TestMerge.cPath)
        am = []

        oc = [c.itsName for c in pm.ap]
        
        view = self.rep.createView('view')

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

        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)

        cm = km.newItem('child', pm)
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        co = po['child']
        co.rename(o_name)
        view.commit()

        cm.rename(m_name)
        main.commit()

    def move(self, o_name, m_name):

        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)

        cm = km.newItem('child', pm)
        km.newItem(m_name, main)
        if o_name != m_name:
            km.newItem(o_name, main)
            
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        co = po['child']
        co.move(view[o_name])
        view.commit()

        cm.move(main[m_name])
        main.commit()

    def test1Merge1(self):
        view = self.view
        view.find(TestMerge.cPath).newItem('c0', view['p'])
        view.commit()
        self.merge(1, 1)

    def test1Merge2(self):
        view = self.view
        view.find(TestMerge.cPath).newItem('c0', view['p'])
        view.commit()
        self.merge(2, 2)

    def test1MergeN(self):
        view = self.view
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
            level = self.setLoggerLevel(logging.CRITICAL)
            self.rename('foo', 'bar')
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.RENAME)
        else:
            self.assert_(False)
        finally:
            self.setLoggerLevel(level)

    def testMoveSame(self):
        self.move('foo', 'foo')

    def testMoveDifferent(self):
        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            self.move('foo', 'bar')
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.MOVE)
        else:
            self.assert_(False)
        finally:
            self.setLoggerLevel(level)

    def testCreateSameName(self):
        main = self.view
        view = self.rep.createView('view')
        po = view['p']
        ko = view.find(TestMerge.cPath)
        ko.newItem('foo', po)
        view.commit()
        
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('foo', pm)

        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            main.commit()
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.NAME)
        else:
            self.assert_(False)
        finally:
            self.setLoggerLevel(level)

    def testRenameDifferentSameName(self):
        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        po['foo'].rename('baz')
        view.commit()
        
        pm = main['p']
        pm['bar'].rename('baz')

        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            main.commit()
        except ChildNameError:
            pass
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.NAME)
        else:
            self.assert_(False)
        finally:
            self.setLoggerLevel(level)

    def testMoveFirst(self):
        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        po.placeChild(po['i1'], None)
        view.commit()
        
        pm = main['p']
        pm.placeChild(pm['i2'], None)
        main.commit()
        
        names = [c.itsName for c in pm.iterChildren()]
        self.assert_(names[0] == 'i2')
        self.assert_(len(names) == 4)

    def testChange1Remove1(self):

        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('q', main)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        po.placeChild(po['i1'], None)
        view.commit()
        
        pm = main['p']
        qm = main['q']

        pm['i1'].move(qm)

        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            main.commit()
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.MOVE)
        else:
            self.assert_(main.check())
        finally:
            self.setLoggerLevel(level)

    def testRemove1Change1(self):

        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('q', main)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        qo = view['q']
        po['i1'].move(qo)
        view.commit()
        
        pm = main['p']

        pm.placeChild(pm['i1'], None)

        main.commit()
        self.assert_(main['q'].getItemChild('i1') != None)

    def testRemove1ChangeOther(self):

        main = self.view
        pm = main['p']
        km = main.find(TestMerge.cPath)
        km.newItem('q', main)
        km.newItem('foo', pm)
        km.newItem('bar', pm)
        km.newItem('i1', pm)
        km.newItem('i2', pm)
        main.commit()
        
        view = self.rep.createView('view')

        po = view['p']
        qo = view['q']
        po['i1'].move(qo)
        view.commit()
        
        pm = main['p']
        pm['foo'].rename('baz')
        main.commit()

        names = [c.itsName for c in pm.iterChildren()]
        self.assert_(names[0] == 'baz')
        self.assert_(len(names) == 3)

    def testMergeNoOverlapRefCollections(self):

        main = self.view
        self.loadCineguide(main)
        main.commit()

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.writers.clear()
        main.commit()

        self.assert_(main.check(), "main didn't check out")

    def testMergeOverlapRefCollections1(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()
        view.commit()

        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()
        main.commit()

        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapRefCollections2(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

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

    def testMergeOverlapRefCollectionsDelete(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        del m.actors
        view.commit()

        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.actors.clear()
        main.commit(otherViewWins)

        self.assert_(main.check(), 'main view did not check out')

    def testMergeNoOverlapRV(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        k.movies.clear()
        main.commit()

        self.assert_(m.title == 'changed title')
        self.assert_(len(m.actors) == 0)

    def testMergeNoOverlapVR(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.writers.clear()
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        main.commit()

        self.assert_(m.title == 'changed title')
        self.assert_(len(m.writers) == 0)
        self.assert_(main.check(), 'main check failed')

    def testMergeNoOverlapVRSingle(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        m2 = view.findPath('//CineGuide/m2')
        m4 = view.findPath('//CineGuide/m4')
        m2.next = m4
        view.commit()
        self.assert_(view.check(), 'view check failed')
        
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

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m6 = view.findPath('//CineGuide/m6')
        m6.writers = k.movies.first().writers
        m6.frenchTitle = 'titre change'
        view.commit()
        self.assert_(view.check(), 'view check failed')
        
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

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title in view'
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title in main'

        type(m).onItemMerge = onItemMerge
        main.commit()
        del type(m).onItemMerge

        self.assertEquals(m.title, 'changed title in main')

    def testMergeOverlapVSame(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        main.commit()

        self.assertEquals(m.title, 'changed title')

    def testMergeOverlapVDifferentNoCallback(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title again'

        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            version = main.itsVersion
            main.commit()
        except MergeError:
            self.assert_(main.check())
            self.assert_(main.itsVersion == version)
            self.assertEquals(m.title, 'changed title')
        finally:
            self.setLoggerLevel(level)

    def testMergeOverlapVDifferentWithCallback(self):

        def mergeFn(code, item, attribute, value):
            return item.getAttributeValue(attribute)

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title'
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m = k.movies.first()
        m.title = 'changed title again'

        main.commit(mergeFn)
        self.assert_(main.check())
        self.assertEquals(m.title, 'changed title')

    def testMergeOverlapRSame(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.director = m2.director
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.director = m2.director
        main.commit()

        self.assertEquals(m1.director, m2.director)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapRDifferent(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.director = m2.director
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m4 = k.movies.next(m3)
        m1.director = m4.director

        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            main.commit()
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.REF)
        finally:
            self.setLoggerLevel(level)

        self.assertEquals(m1.director, m2.director)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapRDifferentWithCallbackNew(self):

        def mergeFn(code, item, attribute, newValue):
            return newValue

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.director = m2.director
        view.commit()
        
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

        main = self.view
        self.loadCineguide(main, False)
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('n', 'numeric')
        k.movies.addIndex('t', 'attribute', attribute='title')
        main.commit()

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m1.title = 'Foo'
        view.commit()
        
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

        view = self.view
        p = view['p']
        cm = view['cm']
        c0 = view.find(TestMerge.cPath).newItem('c0', cm)
        c0.ac = p
        view.commit()

    def testRefs1Merge1(self):

        view = self.view
        self.makeC0()
        self.mergeRefs(1, 1)
        self.assert_(view.check(), 'view did not check out')

    def testRefs1Merge2(self):

        view = self.view
        self.makeC0()
        self.mergeRefs(2, 2)
        self.assert_(view.check(), 'view did not check out')

    def testRefs1MergeN(self):

        view = self.view
        self.makeC0()
        self.mergeRefs(5, 8)
        self.assert_(view.check(), 'view did not check out')

    def testMergeOverlapVRef(self):

        def mergeFn(code, item, attribute, newValue):
            oldValue = getattr(item, attribute)
            return newValue

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        c['m2'].next = m1
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        c['m2'].next = c['m4']

        main.commit(mergeFn)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeOverlapVRefOther(self):

        def mergeFn(code, item, attribute, newValue):
            oldValue = getattr(item, attribute)
            return oldValue

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        c['m2'].next = m1
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        c['m2'].next = c['m4']

        main.commit(mergeFn)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeSetVRef(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        m1.title = 'foo'
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        c['m2'].next = m1

        main.commit()
        self.assert_(main.check(), 'main view did not check out')

    def testMergeSubIndex(self):

        from chandlerdb.util.c import saveUUIDs

        uuids = []
        saveUUIDs(uuids)

#        from chandlerdb.util.c import UUID, loadUUIDs
#        input = file('uuids_ad06.txt')
#        loadUUIDs([UUID(uuid.strip()) for uuid in input if len(uuid) > 1])
#        input.close()
        
        try:
            main = self.view
            self.loadCineguide(main, False)
            k = main.findPath('//CineGuide/KHepburn')
            m1 = k.movies.first()
            m1.director.itsKind.getAttribute('directed').type = m1.itsKind
            k.set = KindSet(m1.itsKind, True)
            k.set.addIndex('t', 'value', attribute='title', ranges=[(0, 1)])
            m1.director.directed.addIndex('T', 'subindex',
                                          superindex=(k, 'set', 't'))
            main.commit()

            view = self.rep.createView('view')

            k = view.findPath('//CineGuide/KHepburn')
            c = k.itsParent
            m1 = k.movies.first()
            m1.title = 'Foo'
            view.commit()
        
            k = main.findPath('//CineGuide/KHepburn')
            c = k.itsParent
            m1 = k.movies.first()
            m2 = k.movies.next(m1)
            m3 = k.movies.next(m2)
            m2.director = m1.director
            m3.delete()

            main.commit()
        finally:
            saveUUIDs(None)
            #loadUUIDs(None)

        if not main.check():

            from random import randint
            name = "uuids_%0.4x.txt" %(randint(0, 65535))
            outFile = file(name, 'w')
            print "Saving uuids to", name
            for uuid in uuids:
                print >>outFile, uuid.str64()
            outFile.close()

            self.assert_(False, 'main view did not check out')

    def testMergeChangeDelete(self):

        def mergeFn(code, item, attribute, newValue):
            if code == MergeError.DELETE:
                return True
            return newValue

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        c = k.itsParent
        m1 = k.movies.first()
        m1.delete()
        view.commit()
        
        main.deferDelete()
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m1.title = 'Foo'
        m1.director = k.movies.next(m1).director

        try:
            level = self.setLoggerLevel(logging.CRITICAL)
            main.commit(None)
        except MergeError, e:
            self.assert_(e.getReasonCode() == MergeError.DELETE)
        else:
            if not m1.isDeleted():
                self.assert_(False, "MergeError not caught")
        finally:
            self.setLoggerLevel(level)

        main.commit(mergeFn)
        self.assert_(m1.isDeleted())
        self.assert_(main.check(), 'main view did not check out')

    def testMergeAddIndexDelete(self):

        main = self.view
        self.loadCineguide(main)

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m1.delete()
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('new', 'numeric')

        main.commit(None)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeAddIndexElsewhereDelete(self):

        main = self.view
        self.loadCineguide(main, False)
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m3.set = Set((k, 'movies'))
        main.commit()

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m1.delete()
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m2 = k.movies.next(m1)
        m3 = k.movies.next(m2)
        m = k.movies.last()
        m.set = Set((m3, 'set'))
        m.set.addIndex('new', 'numeric')

        main.commit(None)
        self.assert_(main.check(), 'main view did not check out')

    def testMergeDeleteValueChangeRefs(self):

        main = self.view
        self.loadCineguide(main, False)
        k = main.findPath('//CineGuide/KHepburn')
        m1 = k.movies.first()
        m1.itsName = 'm1'
        k.movies.remove(m1)
        main.commit()

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        m1 = view.findPath('//CineGuide/m1')
        k.movies.append(m1)
        view.commit()

        k.movies.remove(k.movies.first())
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        del k.movies

        main.commit(None)
        self.assert_(not hasattr(k, 'movies'), 'movies is back')
        self.assert_(main.check(), 'main view did not check out')

    def testMergeConflictKeepsIncoming(self):

        def mergeFn(code, item, attribute, newValue):
            if code == MergeError.DELETE:
                return True
            return getattr(item, attribute, newValue)

        main = self.view
        self.loadCineguide(main, False)
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('t', 'value', attribute='title')
        main.commit()

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        k.movies.first().title = 'View Changed Title'
        view.commit()

        k = main.findPath('//CineGuide/KHepburn')
        k.movies.first().title = 'Main Changed Title'
        main.commit(mergeFn)

        self.assert_(main.check(), 'main view did not check out')

    def testMergeConflictKeepChangeNewIndex(self):

        def mergeFn(code, item, attribute, newValue):
            if code == MergeError.DELETE:
                return True
            return newValue

        main = self.view
        self.loadCineguide(main, False)
        movies = main.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m3 = movies.next(m2)
        main.commit()

        view = self.rep.createView('view')

        movies = view.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m3 = movies.next(m2)
        m1.title = 'View Changed Title'
        m3.set = Set((movies._owner(), 'movies'))
        m3.set.addIndex('t', 'attribute', attribute='title')
        view.commit()

        movies = main.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m3 = movies.next(m2)
        m1.title = 'Main Changed Title'
        main.commit(mergeFn)

        self.assert_(main.check(), 'main view did not check out')

    def testMergeMergeIndexShuffle(self):

        main = self.view
        self.loadCineguide(main, False)
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('n', 'numeric')
        k.movies.addIndex('t', 'value', attribute='title')
        lb = list(k.movies.iterindexkeys('n'))
        main.commit()

        view = self.rep.createView('view')

        k = view.findPath('//CineGuide/KHepburn')
        ml = k.movies.last()
        ml.title = 'Modified Title'
        mdv = k.movies.previous(k.movies.previous(ml))
        mdv.delete()
        view.commit()
        
        k = main.findPath('//CineGuide/KHepburn')
        ml = k.movies.last()
        mp = k.movies.previous(ml)
        mp.title = 'Previous Modified Title'
        mdm = k.movies.previous(k.movies.previous(mp))
        mdm.delete()
        view.commit()

        main.commit(None)
        la = list(k.movies.iterindexkeys('n'))

        lb.remove(mdv.itsUUID)
        lb.remove(mdm.itsUUID)

        self.assert_(lb == la, 'numeric index shuffled')
        self.assert_(main.check(), 'main view did not check out')

    def testMergeNewSuperIndex(self):

        def mergeFn(code, item, attribute, newValue):
            if code == MergeError.DELETE:
                return True
            return newValue

        main = self.view
        self.loadCineguide(main, False)
        movies = main.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m3 = movies.next(m2)
        m3.set = Set((movies._owner(), 'movies'))
        main.commit()

        view = self.rep.createView('view')

        movies = view.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m2.set = Intersection((m3, 'set'), (m1.director, 'directed'))
        m3 = movies.next(m2)
        m1.title = 'View Changed Title'
        m3.set.addIndex('t', 'attribute', attribute='title')
        view.commit()

        movies = main.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m2.set = Intersection((m3, 'set'), (m1.director, 'directed'))
        m3 = movies.next(m2)
        m3.set.addIndex('t', 'attribute', attribute='title')
        m2.set.addIndex('s', 'subindex', superindex=(m3, 'set', 't'))
        m1.title = 'Main Changed Title'
        main.commit(mergeFn)

        self.assert_(main.check(), 'main view did not check out')

    def testMergeNewSubIndex(self):

        def mergeFn(code, item, attribute, newValue):
            if code == MergeError.DELETE:
                return True
            return getattr(item, attribute)

        main = self.view
        self.loadCineguide(main, False)
        k = main.findPath('//CineGuide/KHepburn')
        k.movies.addIndex('t', 'value', attribute='title')
        main.commit()

        view = self.rep.createView('view')

        movies = view.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m2 = movies.next(m1)
        m1.title = 'Foo'
        m2.title = 'Bar'
        view.commit()

        k = main.findPath('//CineGuide/KHepburn')
        actor = k.itsKind.newItem('actor', k.itsParent)
        actor.born = k.born
        actor.name = "an actor"
        actor.set = Set((k, 'movies'))
        actor.set.addIndex('t', 'subindex', superindex=(k, 'movies', 't'))
        main.commit(mergeFn)

        self.assert_(main.check(), 'main view did not check out')

    def testMergeCorrelatedAttributes(self):

        def mergeFn(code, item, attribute, newValue):
            if code == MergeError.DELETE:
                return True
            return newValue

        main = self.view
        self.loadCineguide(main, False)
        movies = main.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m1.itsKind.declareCorrelation(set(['a', 'b']))
        main.commit()

        view = self.rep.createView('view')
        movies = view.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m1.a = 3
        view.commit()

        movies = main.findPath('//CineGuide/KHepburn').movies
        m1 = movies.first()
        m1.b = 5
        main.commit(mergeFn)

        self.assert_(m1.sum == 8, 'sum != 8')        


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
