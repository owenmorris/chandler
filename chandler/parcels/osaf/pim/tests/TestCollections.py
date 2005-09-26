import os,unittest
from osaf.pim.collections import *
from osaf import pim
from repository.persistence.DBRepository import DBRepository

class NotifyHandler(schema.Item):
    """
    An item that exists only to handle notifications
    we should change notifications to work on callables -- John is cool with that.
    """
    log = schema.Sequence(initialValue=[])
    collectionEventHandler = schema.One(schema.String, initialValue="onCollectionEvent")

    def checkLog(self, op, item, other, index=-1):
        if len(self.log) == 0:
            return False
        
        # skip 'changed' entries unless we are looking for changes
        # this is due to mixing of mapChangesCallables in collections.deliverNotifications
        for i in range(-1, -(len(self.log)+1), -1):
            rec = self.log[i]
            if op != 'changed' and rec[0] == 'changed':
                continue
            if op == 'changed' and rec[0] != 'changed':
                continue
            return rec[0] == op and rec[3] == other 

    def onCollectionEvent(self, op, item, name, other, *args):
        self.log.append((op, item, name, other, args))

class SimpleItem(schema.Item):
    """
    A dirt simple item -- think content item here, if you like
    """

    label = schema.One(schema.String, displayName=u"My Label")

class ChildSimpleItem(SimpleItem):
    childData = schema.One(schema.String, displayName=u"Child data")

class OtherSimpleItem(schema.Item):
    """
    Another dirt simple item -- think content item here, if you like
    """

    label = schema.One(schema.String, displayName=u"My Label")

class CollectionTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def setUp(self):
        schema.reset()  # clear schema state before starting
        self.chandlerDir = os.environ['CHANDLERHOME']
        self.repoDir = os.path.join(self.chandlerDir, u'__repository__')

        rep = DBRepository(self.repoDir)
        kwds = { 'create': True, 'refcounted':True, 'ramdb':True }
        rep.create(**kwds)
        view = rep.view

        if view.findPath("//Schema") is None:
            view.loadPack(os.path.join(self.chandlerDir, 'repository', 'packs', 'schema.pack'))
            view.loadPack(os.path.join(self.chandlerDir, 'repository', 'packs', 'chandler.pack'))
        self.view = view

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

        self.failUnless(self.i is not None)
        self.failUnless(self.i1 is not None)
        self.failUnless(self.i2 is not None)
        self.failUnless(self.b1 is not None)
        self.failUnless(self.b2 is not None)
        self.failUnless(self.nh is not None) 
        self.failUnless(self.nh1 is not None)
        self.failUnless(self.nh2 is not None)

    def testUnion(self):
        """
        Test UnionCollection
        """
        u = UnionCollection('u', view=self.view)
        u.addSource(self.b1)
        u.addSource(self.b2)

        self.b1.subscribers.add(self.nh)
        u.subscribers.add(self.nh1)

        # add i to b1
        self.b1.add(self.i)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))

        # add i1 to b2
        self.b2.add(self.i1)
        deliverNotifications(self.view)
        self.failIf(self.nh.checkLog("add", self.b2, self.i1))
        self.failUnless(self.nh1.checkLog("add", u, self.i1,))

        # remove i from b1
        self.b1.remove(self.i)
        deliverNotifications(self.view)
        self.failIf(self.nh.checkLog("remove", self.b1, self.i1))
        self.failIf(self.nh.checkLog("remove", u, self.i1))        

    def testUnionAddSource(self):
        """
        test addSource
        """
        u = UnionCollection('u', view=self.view)
        u.subscribers.add(self.nh)

        self.b1.add(self.i)
        self.b2.add(self.i)
        self.b2.add(self.i1)
        self.b1.subscribers.add(self.nh1)
        self.b2.subscribers.add(self.nh2)

        print [ i for i in u ]
        u.addSource(self.b1)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add",u,self.i))

        print [ i for i in u ]
        u.addSource(self.b2)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add",u,self.i1))

        print [ i for i in u ]
        u.removeSource(self.b2)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("remove",u,self.i1))
        
        print [ i for i in u ]

    def testDifference(self):
        """
        Test DifferenceCollection
        """
        d = DifferenceCollection('d', view=self.view)
        d.sources = [ self.b1, self.b2 ]
        self.b1.subscribers.add(self.nh)
        d.subscribers.add(self.nh1)

        self.b1.add(self.i)
        deliverNotifications(self.view)      
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.failUnless(self.nh1.checkLog("add", d, self.i))

        self.b1.add(self.i1)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i1))
        self.failUnless(self.nh1.checkLog("add", d, self.i1))

        self.b2.subscribers.add(self.nh2)
        self.b2.add(self.i2)
        deliverNotifications(self.view)
        self.failUnless(self.nh2.checkLog("add", self.b2, self.i2))
        self.failIf(self.nh1.checkLog("add", d, self.i2))
        self.failIf(self.nh1.checkLog("remove", d, self.i2))     

        self.b2.add(self.i)
        deliverNotifications(self.view)
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
        iu.addSource(inclusions)
        iu.addSource(rule)
        ic = DifferenceCollection("ic", view=self.view)
        ic.sources = [ iu, exclusions ]

        inclusions.subscribers.add(self.nh)
        rule.subscribers.add(self.nh1)
        exclusions.subscribers.add(self.nh2)

        nh3 = NotifyHandler("nh3", view=self.view)
        ic.subscribers.add(nh3)

        inclusions.add(self.i)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add", inclusions, self.i))
        self.failIf(nh3.checkLog("add", ic, self.i))

        it = OtherSimpleItem(view=self.view)
        inclusions.add(it)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add", inclusions, it))
        self.failUnless(nh3.checkLog("add", ic, it))        

        nancy = SimpleItem("nancy", label="nancy", view=self.view)
        deliverNotifications(self.view)
        self.failUnless(self.nh1.checkLog("add", rule, nancy))
        self.assertEqual(len(list(rule)), 4)
        self.assertEqual(len(list(ic)), 5)

        exclusions.add(self.i2)
        deliverNotifications(self.view)
        self.failUnless(self.nh2.checkLog("add", exclusions, self.i2))
        self.failUnless(nh3.checkLog("remove", ic, self.i2))
        
        exclusions.remove(self.i2)
        deliverNotifications(self.view)
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
        k2.subscribers.add(self.nh)

        i = SimpleItem("new i", view=self.view)
        deliverNotifications(self.view)       
        self.failUnless(self.nh.checkLog("add", k2, i))

        i.delete()
        # note deleting an item Nulls references to it.
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("remove", k2, None))                        

    def testRecursiveKindCollection(self):
        """
        Test Recursive KindCollections
        """
        k = KindCollection(view=self.view)
        k.kind = self.i.itsKind
        k.recursive = True

        i = SimpleItem("new i", view=self.view)
        i1 = ChildSimpleItem("new child", view=self.view)

        flags = [isinstance(i,SimpleItem) for i in k ]
        deliverNotifications(self.view)
        self.failUnless(False not in flags)

    def testFilteredCollection(self):
        f1 = FilteredCollection(view=self.view)
        f1.source = self.b1
        f1.filterExpression = "len(item.label) > 2"
        f1.filterAttributes = ["label"]
        self.b1.subscribers.add(self.nh)
        f1.subscribers.add(self.nh1)

        self.b1.add(self.i)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.failIf(self.nh1.checkLog("add", f1, self.i))

        self.b1.add(self.i2)
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog("add", self.b1, self.i2))
        self.failIf(self.nh1.checkLog("add", f1, self.i2))

        ted = SimpleItem("ted", label="ted", view=self.view)
        self.b1.add(ted)
        deliverNotifications(self.view)
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
        f2.filterAttributes = ["label"]
        nh3 = NotifyHandler("nh3", view=self.view)

        k1.subscribers.add(self.nh2)
        f2.subscribers.add(nh3)

        fred = SimpleItem("fred", label="fred", view=self.view)
        deliverNotifications(self.view)
        self.failUnless(self.nh2.checkLog("add", k1, fred))
        self.failUnless(nh3.checkLog("add", f2, fred))

        john = SimpleItem("john", label="john", view=self.view)
        deliverNotifications(self.view)
        self.failUnless(self.nh2.checkLog("add", k1, john))
        self.failUnless(nh3.checkLog("add", f2, john))

        karen = SimpleItem("karen", label="karen", view=self.view)
        deliverNotifications(self.view)
        self.failUnless(self.nh2.checkLog("add", k1, karen))
        self.failUnless(nh3.checkLog("add", f2, karen))

        x = SimpleItem("x", label="x", view=self.view)
        deliverNotifications(self.view)
        self.failUnless(self.nh2.checkLog("add", k1, x))
        self.failIf(nh3.checkLog("add", f2, x))

#        print self.nh2.log[-1],len(self.nh2.log)
#        for i in f2:
#            print i
#        print nh3.log[-1], len(nh3.log)
#        print "setting label"
#        print x.label
        x.label = "xxxx"
#        print x.label

        pos = len(nh3.log)
        # simulate idle loop
        deliverNotifications(self.view)

        #@@@ TODO - the following assert is broken until we have a way of
        # locating the KindCollection for a specific Kind
#        print nh3.log[-1], len(nh3.log)
#        for i in f2:
#            print i
        gotChanged = False
        for i in nh3.log[pos:]:
            if i[0] == 'changed' and i[1] == f2 and i[3] == x:
                gotChanged=True
                break
        self.failUnless(gotChanged)

#        print self.nh2.log[-1], len(self.nh2.log)
#        print nh3.log[-1], len(nh3.log)

        self.assertEqual(len(list(f2)),5)
        self.failUnless(ted in k1 and ted in f2)
        self.failUnless(fred in k1 and fred in f2)
        self.failUnless(x in k1)
        self.failIf(x not in f2)

        x.label="zzz"


    def testFilteredDelete(self):
        """
        Test deleting an item from a FilteredCollection by updating an
        attribute of an item in the source.
        """
        k1 = KindCollection(view=self.view)
        k1.kind = self.i.itsKind
        f2 = FilteredCollection(view=self.view)
        f2.source = k1
        f2.filterExpression = "item.hasLocalAttributeValue('label')"
        f2.filterAttributes = ["label"]
        nh3 = NotifyHandler("nh3", view=self.view)

        k1.subscribers.add(self.nh2)
        f2.subscribers.add(nh3)

        self.i.label = "xxx"
        print nh3.log
        deliverNotifications(self.view)

        changed = False
        print nh3.log
        for i in nh3.log[::-1]:
            if i[0] == "changed" and i[1] == f2 and i[3] == self.i:
                changed = True
                break
        self.failUnless(changed)
        self.assertEqual(self.i.label,"xxx")

        delattr(self.i,"label")
        deliverNotifications(self.view)
        print nh3.log
        self.failUnless(nh3.checkLog("remove", f2, self.i,-2))
        self.failUnless(nh3.checkLog("changed", k1, self.i))

    def testFilters(self):
        from application.Parcel import Manager as ParcelManager
        manager = \
                ParcelManager.get(self.view, \
                                  path=[os.path.join(self.repoDir, 'parcels')])
        manager.loadParcels(['osaf.pim'])

        k = KindCollection(view=self.view)
        kind = self.view.findPath('//parcels/osaf/pim/ContentItem')
    
    def testFilteredStack(self):
        """
        Test collections stacked on top of each other
        """
        k = KindCollection(view=self.view)
        k.kind = self.i.itsKind

        f = FilteredCollection(view=self.view)
        f.source = k
        f.filterExpression = "len(item.label) > 1"
        f.filterAttributes = ["label"]
        
        l = ListCollection(view=self.view)
        
        u = UnionCollection(view=self.view)
        u.subscribers.add(self.nh)
        
        u.addSource(f)
        u.addSource(l)
        deliverNotifications(self.view)
        
        self.i.label = "abcd"
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog('add', u, self.i))        

        self.i.label = "defg"
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog('changed', u, self.i))        

        self.i.label = "a"
        deliverNotifications(self.view)
        self.failUnless(self.nh.checkLog('remove', u, self.i))                
        
    def testNumericIndex(self):
        k = KindCollection(view=self.view)
        k.kind = self.i.itsKind

        for i in ["z", "y", "x", "w", "v"]:
            it = SimpleItem(i, label=i, view=self.view)

        #@@@ this is a bug in len -- if you compute the length before you
        #create any indexes, you are out of luck
#        self.assertEqual(len(list(k)),8)
        k.indexName = "__adhoc__"
        k.createIndex()

        self.assertEqual([x.label for x in k],
                         [k[i].label for i in xrange(0, len(k))])


    def testAttributeIndex(self):
        k = KindCollection(view = self.view)
        k.kind = self.i.itsKind

        for i in ["z", "y", "x", "w", "v"]:
            it = SimpleItem(i, label=i, view=self.view)

        self.assertEqual(len(list(k)),8)

        k.indexName = "label"
        k.createIndex()

        self.assertEqual([k[i].label for i in xrange(0, len(k))],['i','i2','i3','v','w','x','y','z'])

        k[len(k)-1].label = 'u'
        self.assertEqual([k[i].label for i in xrange(0, len(k))],['i','i2','i3','u','v','w','x','y'])

    def testDelayedCreation(self):
        uc = UnionCollection('u', view=self.view)
        uc.addSource(self.b1)
        uc.addSource(self.b2)
        self.failUnless(uc.rep is not None)

        kc = KindCollection(view=self.view)
        kc.kind = self.view.findPath('Schema/Core/Parcel')
        self.failUnless(kc.rep is not None)

        fc = FilteredCollection(view=self.view)
        fc.filterExpression = "len(item.label) > 2"
        fc.filterAttributes = [ "label" ]
        fc.source = self.b1
        self.failUnless(fc.rep is not None)

        fc1 = FilteredCollection(view=self.view)
        fc1.source = self.b1
        fc1.filterExpression = "len(item.label) > 2"
        fc1.filterAttributes = [ "label" ]
        self.failUnless(fc1.rep is not None)

    def testBug2755(self):
        """
        Test to verify that bug 2755
        <https://bugzilla.osafoundation.org/show_bug.cgi?id=2755>
        is fixed.
        """
        k1 = KindCollection(view=self.view)
        k1.kind = self.i.itsKind

        for i in k1:
            self.failUnless(i != None)
            break;

        for i in k1:
            self.failUnless(i != None)

    def testInclusionExclusionCollection(self):
        trash = ListCollection(view=self.view)
        coll1 = InclusionExclusionCollection(view=self.view).setup(trash=trash)
        coll2 = InclusionExclusionCollection(view=self.view).setup(trash=trash)
        coll3 = InclusionExclusionCollection(view=self.view).setup(trash=trash)
        note = pim.Note(view=self.view)

        # Ensure that removing an item from its last collection puts it into
        # the trash
        coll1.add(note)
        self.assert_(note in coll1)
        self.assert_(note not in trash)
        coll1.remove(note)
        self.assert_(note not in coll1)
        self.assert_(note in trash)

        # Ensure that adding an item to the trash removes it from all
        # collections
        coll1.add(note)
        coll2.add(note)
        self.assert_(note in coll1)
        self.assert_(note in coll2)
        trash.add(note)
        self.assert_(note not in coll1)
        self.assert_(note not in coll2)

        # Ensure that then removing it from the trash puts it back in those
        # collections (only if it was there before)
        trash.remove(note)
        self.assert_(note in coll1)
        self.assert_(note in coll2)
        self.assert_(note not in coll3)

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
