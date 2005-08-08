import os,unittest
from osaf.pim.collections import *
from repository.persistence.DBRepository import DBRepository

class CollectionTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def setUp(self):
        schema.reset()  # clear schema state before starting
        self.chandlerDir = os.environ['CHANDLERHOME']
        self.repoDir = os.path.join(self.chandlerDir,'__repository__')

        rep = DBRepository(self.repoDir)
        kwds = { 'create': True, 'refcounted':True, 'ramdb':True }
        rep.create(**kwds)

        if rep.findPath("//Schema") is None:
            rep.loadPack(os.path.join(self.chandlerDir, 'repository', 'packs', 'schema.pack'))
            rep.loadPack(os.path.join(self.chandlerDir, 'repository', 'packs', 'chandler.pack'))
        self.view = rep.getCurrentView()

    def tearDown(self):
        self.failUnless(schema.reset().check(), "check() failed")

class CollectionTests(CollectionTestCase):

    def setUp(self):
        super(CollectionTests, self).setUp()
        self.i = SimpleItem('i', label='i', view=self.view)
        self.i1 = SimpleItem('i1',label='i2', view=self.view)
        self.i2 = SimpleItem('i2',label='i3', view=self.view)

        self.b1 = ListCollection('b1', view=self.view)
        self.b2 = ListCollection('b2', view=self.view)

        self.nh = NotifyHandler('nh', view=self.view)
        self.nh1 = NotifyHandler('nh1', view=self.view)
        self.nh2 = NotifyHandler('nh2', view=self.view)

        self.failUnless(self.i)
        self.failUnless(self.i1)
        self.failUnless(self.i2)
        self.failUnless(self.b1)
        self.failUnless(self.b2)
        self.failUnless(self.nh)
        self.failUnless(self.nh1)
        self.failUnless(self.nh2)

    def testUnion(self):
        """
        Test UnionCollection
        """
        u = UnionCollection('u', view=self.view)
        u.left = self.b1
        u.right= self.b2

        self.b1.subscribers.append(self.nh)
        u.subscribers.append(self.nh1)

        self.b1.add(self.i)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.b2.add(self.i1)

        self.failIf(self.nh.checkLog("add", self.b2, self.i1))
        self.failUnless(self.nh1.checkLog("add", u, self.i1,))
        self.b1.remove(self.i)

        self.failIf(self.nh.checkLog("remove", self.b1, self.i1))
        self.failIf(self.nh.checkLog("remove", u, self.i1))        

    def testDifference(self):
        """
        Test DifferenceCollection
        """
        d = DifferenceCollection('d', view=self.view)
        d.left = self.b1
        d.right = self.b2
        self.b1.subscribers.append(self.nh)
        d.subscribers.append(self.nh1)
        #
        self.b1.add(self.i)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.failUnless(self.nh1.checkLog("add", d, self.i))

        self.b1.add(self.i1)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i1))
        self.failUnless(self.nh1.checkLog("add", d, self.i1))

        self.b2.subscribers.append(self.nh2)
        self.b2.add(self.i2)
        self.failUnless(self.nh2.checkLog("add", self.b2, self.i2))
        self.failIf(self.nh1.checkLog("add", d, self.i2))
        self.failIf(self.nh1.checkLog("remove", d, self.i2))
        

        self.b2.add(self.i)
        self.failUnless(self.nh2.checkLog("add", self.b2, self.i))
        self.failUnless(self.nh1.checkLog("remove", d, self.i))

    def testItemCollection(self):
        """
        Test the ItemCollection expression
        """

        inclusions = ListCollection("inclusions", view=self.view)
        rule = KindCollection(view=self.view)
        rule.kind = self.i.itsKind
        exclusions = ListCollection("exclusions", view=self.view)
        iu = UnionCollection("iu", view=self.view)
        iu.left = inclusions
        iu.right = rule
        ic = DifferenceCollection("ic", view=self.view)
        ic.left = iu
        ic.right = exclusions

        inclusions.subscribers.append(self.nh)
        rule.subscribers.append(self.nh1)
        exclusions.subscribers.append(self.nh2)

        nh3 = NotifyHandler("nh3", view=self.view)
        ic.subscribers.append(nh3)

        inclusions.add(self.i)
        self.failUnless(self.nh.checkLog("add", inclusions, self.i))
        self.failIf(nh3.checkLog("add", ic, self.i))

        it = OtherSimpleItem(view=self.view)
        inclusions.add(it)
        self.failUnless(self.nh.checkLog("add", inclusions, it))
        self.failUnless(nh3.checkLog("add", ic, it))        

        nancy = SimpleItem("nancy", label="nancy", view=self.view)
        self.failUnless(self.nh1.checkLog("add", rule, nancy))
        self.assertEqual(len(list(rule)), 4)
        self.assertEqual(len(list(ic)), 5)

        exclusions.add(self.i2)
        self.failUnless(self.nh2.checkLog("add", exclusions, self.i2))
        self.failUnless(nh3.checkLog("remove", ic, self.i2))
        
        exclusions.remove(self.i2)
        self.failUnless(self.nh2.checkLog("remove", exclusions, self.i2))
        self.failUnless(nh3.checkLog("add", ic, self.i2))

        self.assertEqual(len(list(rule)), 4)
        self.assertEqual(len(list(ic)), 5)

    def testKindCollection(self):
        """
        Test KindCollection
        """
        k = self.view.findPath('//Schema/Core/Kind')
        k1 = KindCollection(view=self.view)
        k1.kind = k
        k2 = KindCollection(view=self.view)
        k2.kind  = self.i.itsKind
        k2.subscribers.append(self.nh)

        i = SimpleItem("new i", view=self.view)
        self.failUnless(self.nh.checkLog("add", k2, i))

        i.delete()
        # note deleting an item Nulls references to it.
        self.failUnless(self.nh.checkLog("remove", k2, None))                        

    def testFilteredCollection(self):
        f1 = FilteredCollection(view=self.view)
        f1.source = self.b1
        f1.filterExpression = "len(item.label) > 2"
        self.b1.subscribers.append(self.nh)
        f1.subscribers.append(self.nh1)

        self.b1.add(self.i)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.failIf(self.nh1.checkLog("add", f1, self.i))

        self.b1.add(self.i2)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i2))
        self.failIf(self.nh1.checkLog("add", f1, self.i2))

        ted = SimpleItem("ted", label="ted", view=self.view)
        self.b1.add(ted)
        self.failUnless(self.nh.checkLog("add", self.b1, ted))
        self.failUnless(self.nh1.checkLog("add", f1, ted))

        self.assertEqual(len(list(f1)),1)
        self.failUnless(ted in f1)
        self.failIf(self.i in f1)

        k1 = KindCollection(view=self.view)
        k1.kind = self.i.itsKind
        f2 = FilteredCollection(view=self.view)
        f2.source = k1
        f2.filterExpression = "len(item.label) > 2"
        nh3 = NotifyHandler("nh3", view=self.view)

        k1.subscribers.append(self.nh2)
        f2.subscribers.append(nh3)

        fred = SimpleItem("fred", label="fred", view=self.view)
        self.failUnless(self.nh2.checkLog("add", k1, fred))
        self.failUnless(nh3.checkLog("add", f2, fred))

        john = SimpleItem("john", label="john", view=self.view)
        self.failUnless(self.nh2.checkLog("add", k1, john))
        self.failUnless(nh3.checkLog("add", f2, john))

        karen = SimpleItem("karen", label="karen", view=self.view)
        self.failUnless(self.nh2.checkLog("add", k1, karen))
        self.failUnless(nh3.checkLog("add", f2, karen))

        x = SimpleItem("x", label="x", view=self.view)
        self.failUnless(self.nh2.checkLog("add", k1, x))
        self.failIf(nh3.checkLog("add", f2, x))

#        print self.nh2.log[-1],len(self.nh2.log)
#        print nh3.log[-1], len(nh3.log)
#        print "setting label"
#        print x.label
        x.label = "xxxx"
#        print x.label

        # simulate idle loop
        self.view.mapChanges(mapChangesCallable, True)

        self.failUnless(nh3.checkLog("add", f2, x))
#        print self.nh2.log[-1], len(self.nh2.log)
#        print nh3.log[-1], len(nh3.log)

        self.assertEqual(len(list(f2)),5)
        self.failUnless(ted in k1 and ted in f2)
        self.failUnless(fred in k1 and fred in f2)
        self.failUnless(x in k1)
        self.failIf(x not in f2)

        x.label="zzz"

    def testFilters(self):
        from application.Parcel import Manager as ParcelManager
        manager = \
                ParcelManager.get(self.view, \
                                  path=[os.path.join(self.repoDir, 'parcels')])
        manager.loadParcels(['parcel:osaf.pim'])

        k = KindCollection(view=self.view)
        kind = self.view.findPath('//parcels/osaf/pim/ContentItem')
        print kind
        
    def testIndices(self):
        k = KindCollection(view=self.view)
        k.kind = self.i.itsKind
        k.subscribers.append(self.nh)

        for i in ["z", "y", "x", "w", "v"]:
            it = SimpleItem(i, label=i, view=self.view)

        self.assertEqual(len(list(k)),8)
        k.addIndex('n', 'numeric')
        k.addIndex('a', 'attribute', attribute='label')

        self.assertEqual([x.label for x in k.iterindexvalues('n')],
                         [k.getByIndex('n',i).label for i in xrange(0, k.size())])

        self.assertEqual([i.label for i in k.iterindexvalues('a')],['i','i2','i3','v','w','x','y','z'])

        k.lastInIndex('a').label = 'u'
        self.assertEqual([i.label for i in k.iterindexvalues('a')],['i','i2','i3','u','v','w','x','y'])

    def testDelayedCreation(self):
        uc = UnionCollection('u', view=self.view)
        uc.left = self.b1
        uc.right = self.b2
        self.failUnless(uc.rep is not None)

        kc = KindCollection(view=self.view)
        kc.kind = self.view.findPath('Schema/Core/Parcel')
        self.failUnless(kc.rep is not None)

        fc = FilteredCollection(view=self.view)
        fc.filterExpression = "len(item.label) > 2"
        fc.source = self.b1
        self.failUnless(fc.rep is not None)


#if __name__ == "__main__":
##    import hotshot
##    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
##    profiler.run('unittest.main()')
##    profiler.close()
    #unittest.main()
