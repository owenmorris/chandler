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
    subscribesTo = schema.One(ContentCollection, otherName="subscribers")

    def checkLog(self, op, item, other, index=-1):
        if len(self.log) == 0:
            return False
        
        # skip 'changed' entries unless we are looking for changes
        # this is due to mixing of _dispatchChanges in
        # view.dispatchNotifcations()
        for i in range(-1, -(len(self.log)+1), -1):
            rec = self.log[i]
            if op != 'changed' and rec[0] == 'changed':
                continue
            if op == 'changed' and rec[0] != 'changed':
                continue
            return rec[0] == op and (rec[3] == other or rec[3] == other.itsUUID)

    def onCollectionNotification(self, op, collection, name, other):
        self.log.append((op, collection, name, other))

class SimpleItem(schema.Item):
    """
    A dirt simple item -- think content item here, if you like
    """

    label = schema.One(schema.Text, displayName=u"My Label")
    collections = schema.Sequence(otherName='refCollection')
    appearsIn = schema.Sequence(otherName='set')

class ChildSimpleItem(SimpleItem):
    childData = schema.One(schema.Text, displayName=u"Child data")

class OtherSimpleItem(schema.Item):
    """
    Another dirt simple item -- think content item here, if you like
    """

    label = schema.One(schema.Text, displayName=u"My Label")
    collections = schema.Sequence(otherName='refCollection')
    appearsIn = schema.Sequence(otherName='set')


class CollectionTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def setUp(self):
        schema.reset()  # clear schema state before starting
        self.chandlerDir = os.environ['CHANDLERHOME']
        self.repoDir = os.path.join(self.chandlerDir, '__repository__')

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
        self.i = SimpleItem('i', label='i', itsView=self.view)
        self.i1 = SimpleItem('i1',label='i2', itsView=self.view)
        self.i2 = SimpleItem('i2',label='i3', itsView=self.view)

        self.b1 = ListCollection('b1', itsView=self.view)
        self.b2 = ListCollection('b2', itsView=self.view)

        self.nh = NotifyHandler('nh', itsView=self.view)
        self.nh1 = NotifyHandler('nh1', itsView=self.view)
        self.nh2 = NotifyHandler('nh2', itsView=self.view)

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
        u = UnionCollection('u', itsView=self.view,
                            sources=[ self.b1, self.b2 ])

        self.b1.notificationQueueSubscribe(self.nh)
        u.notificationQueueSubscribe(self.nh1)

        # add i to b1
        self.b1.add(self.i)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))

        # add i1 to b2
        self.b2.add(self.i1)
        self.view.dispatchNotifications()
        self.failIf(self.nh.checkLog("add", self.b2, self.i1))
        self.failUnless(self.nh1.checkLog("add", u, self.i1,))

        # remove i from b1
        self.b1.remove(self.i)
        self.view.dispatchNotifications()
        self.failIf(self.nh.checkLog("remove", self.b1, self.i1))
        self.failIf(self.nh.checkLog("remove", u, self.i1))        

    def testUnionAddSource(self):
        """
        test addSource
        """
        u = UnionCollection('u', itsView=self.view)
        u.notificationQueueSubscribe(self.nh)

        self.b1.add(self.i)
        self.b2.add(self.i)
        self.b2.add(self.i1)

        # make transient subscriptions
        self.view.notificationQueueSubscribe(self.b1, self.nh1)
        self.view.notificationQueueSubscribe(self.b2, self.nh2)

        u.addSource(self.b1)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add",u,self.i.itsUUID))

        print [ i for i in u ]
        u.addSource(self.b2)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add",u,self.i1.itsUUID))

        print [ i for i in u ]
        u.removeSource(self.b2)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("remove",u,self.i1.itsUUID))
        
        print [ i for i in u ]

    def testDifference(self):
        """
        Test DifferenceCollection
        """
        d = DifferenceCollection('d', itsView=self.view,
                                 sources=[ self.b1, self.b2 ])
        self.b1.notificationQueueSubscribe(self.nh)
        d.notificationQueueSubscribe(self.nh1)

        self.b1.add(self.i)
        self.view.dispatchNotifications()      
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.failUnless(self.nh1.checkLog("add", d, self.i))

        self.b1.add(self.i1)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", self.b1, self.i1))
        self.failUnless(self.nh1.checkLog("add", d, self.i1))

        self.b2.notificationQueueSubscribe(self.nh2)
        self.b2.add(self.i2)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("add", self.b2, self.i2))
        self.failIf(self.nh1.checkLog("add", d, self.i2))
        self.failIf(self.nh1.checkLog("remove", d, self.i2))     

        self.b2.add(self.i)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("add", self.b2, self.i))
        self.failUnless(self.nh1.checkLog("remove", d, self.i))

    def testItemCollection(self):
        """
        Test the ItemCollection expression
        """
        inclusions = ListCollection("inclusions", itsView=self.view)
        rule = KindCollection(itsView=self.view,
                              kind=self.i.itsKind)
        exclusions = ListCollection("exclusions", itsView=self.view)
        iu = UnionCollection("iu", itsView=self.view,
                             sources=[ inclusions, rule ])
        ic = DifferenceCollection("ic", itsView=self.view,
                                  sources=[ iu, exclusions ])

        inclusions.notificationQueueSubscribe(self.nh)
        rule.notificationQueueSubscribe(self.nh1)
        exclusions.notificationQueueSubscribe(self.nh2)

        nh3 = NotifyHandler("nh3", itsView=self.view)
        ic.notificationQueueSubscribe(nh3)

        inclusions.add(self.i)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", inclusions, self.i))
        self.failIf(nh3.checkLog("add", ic, self.i))

        it = OtherSimpleItem(itsView=self.view)
        inclusions.add(it)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", inclusions, it))
        self.failUnless(nh3.checkLog("add", ic, it))        

        nancy = SimpleItem("nancy", label="nancy", itsView=self.view)
        self.view.dispatchNotifications()
        self.failUnless(self.nh1.checkLog("add", rule, nancy))
        self.assertEqual(len(list(rule)), 4)
        self.assertEqual(len(list(ic)), 5)

        exclusions.add(self.i2)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("add", exclusions, self.i2))
        self.failUnless(nh3.checkLog("remove", ic, self.i2))
        
        exclusions.remove(self.i2)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("remove", exclusions, self.i2))
        self.failUnless(nh3.checkLog("add", ic, self.i2))

        self.assertEqual(len(list(rule)), 4)
        self.assertEqual(len(list(ic)), 5)

    def testKindCollection(self):
        """
        Test KindCollection
        """
        k = self.view.findPath('//Schema/Core/Kind')
        k1 = KindCollection(itsView=self.view,
                            kind=k)
        k2 = KindCollection(itsView=self.view,
                            kind=self.i.itsKind)
        k2.notificationQueueSubscribe(self.nh)

        i = SimpleItem("new i", itsView=self.view)
        self.view.dispatchNotifications()       
        self.failUnless(self.nh.checkLog("add", k2, i))

        i.delete()
        # note deleting an item Nulls references to it.
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("remove", k2, None))                        

    def testRecursiveKindCollection(self):
        """
        Test Recursive KindCollections
        """
        k = KindCollection(itsView=self.view,
                           kind=self.i.itsKind,
                           recursive=True)

        i = SimpleItem("new i", itsView=self.view)
        i1 = ChildSimpleItem("new child", itsView=self.view)

        flags = [isinstance(i,SimpleItem) for i in k ]
        self.view.dispatchNotifications()
        self.failUnless(False not in flags)

    def testFilteredCollection(self):
        f1 = FilteredCollection(itsView=self.view,
                                source=self.b1,
                                filterExpression=u"len(view[uuid].label) > 2",
                                filterAttributes=["label"])
        self.b1.notificationQueueSubscribe(self.nh)
        f1.notificationQueueSubscribe(self.nh1)

        self.b1.add(self.i)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", self.b1, self.i))
        self.failIf(self.nh1.checkLog("add", f1, self.i))

        self.b1.add(self.i2)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", self.b1, self.i2))
        self.failIf(self.nh1.checkLog("add", f1, self.i2))

        ted = SimpleItem("ted", label="ted", itsView=self.view)
        self.b1.add(ted)
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog("add", self.b1, ted))
        self.failUnless(self.nh1.checkLog("add", f1, ted))

        self.assertEqual(len(list(f1)),1)
        self.failUnless(ted in f1)
        self.failIf(self.i in f1)

        k1 = KindCollection(itsView=self.view,
                            kind=self.i.itsKind)
        f2 = FilteredCollection(itsView=self.view,
                                source=k1,
                                filterExpression=u"len(view[uuid].label) > 2",
                                filterAttributes=["label"])
        nh3 = NotifyHandler("nh3", itsView=self.view)

        k1.notificationQueueSubscribe(self.nh2)
        f2.notificationQueueSubscribe(nh3)

        fred = SimpleItem("fred", label="fred", itsView=self.view)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("add", k1, fred))
        self.failUnless(nh3.checkLog("add", f2, fred))

        john = SimpleItem("john", label="john", itsView=self.view)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("add", k1, john))
        self.failUnless(nh3.checkLog("add", f2, john))

        karen = SimpleItem("karen", label="karen", itsView=self.view)
        self.view.dispatchNotifications()
        self.failUnless(self.nh2.checkLog("add", k1, karen))
        self.failUnless(nh3.checkLog("add", f2, karen))

        x = SimpleItem("x", label="x", itsView=self.view)
        self.view.dispatchNotifications()
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
        self.view.dispatchNotifications()

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
        k1 = KindCollection(itsView=self.view,
                            kind=self.i.itsKind)
        f2 = FilteredCollection(itsView=self.view,
                                source=k1,
                                filterExpression=u"view[uuid].hasLocalAttributeValue('label')",
                                filterAttributes=["label"])
        nh3 = NotifyHandler("nh3", itsView=self.view)

        k1.notificationQueueSubscribe(self.nh2)
        f2.notificationQueueSubscribe(nh3)

        self.i.label = "xxx"
        print nh3.log
        self.view.dispatchNotifications()

        changed = False
        print nh3.log
        for i in nh3.log[::-1]:
            if i[0] == "changed" and i[1] == f2 and i[3] == self.i:
                changed = True
                break
        self.failUnless(changed)
        self.assertEqual(self.i.label,"xxx")

        delattr(self.i,"label")
        self.view.dispatchNotifications()

        self.failUnless(nh3.checkLog("remove", f2, self.i,-2))
        self.failUnless(self.nh2.checkLog("changed", k1, self.i))

    def testFilteredStack(self):
        """
        Test collections stacked on top of each other
        """
        k = KindCollection(itsView=self.view,
                           kind=self.i.itsKind)

        f = FilteredCollection(itsView=self.view,
                               source=k,
                               filterExpression=u"len(view[uuid].label) > 1",
                               filterAttributes=["label"])
        
        l = ListCollection(itsView=self.view)
        
        u = UnionCollection(itsView=self.view)
        u.notificationQueueSubscribe(self.nh)
        
        u.addSource(f)
        u.addSource(l)
        self.view.dispatchNotifications()
        
        self.i.label = "abcd"
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog('add', u, self.i))        

        self.i.label = "defg"
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog('changed', u, self.i))        

        self.i.label = "a"
        self.view.dispatchNotifications()
        self.failUnless(self.nh.checkLog('remove', u, self.i))                
        
    def testNumericIndex(self):
        k = KindCollection(itsView=self.view,
                           kind=self.i.itsKind)

        testCollection = IndexedSelectionCollection(itsView=self.view,
                                                    source=k)
        for i in ["z", "y", "x", "w", "v"]:
            it = SimpleItem(i, label=i, itsView=self.view)

        #@@@ this is a bug in len -- if you compute the length before you
        #create any indexes, you are out of luck
#        self.assertEqual(len(list(testCollection)),8)
        testCollection.indexName = "__adhoc__"
        testCollection.getCollectionIndex()

        self.assertEqual([x.label for x in testCollection],
                         [testCollection[i].label for i in xrange(0, len(testCollection))])


    def testAttributeIndex(self):
        k = KindCollection(itsView=self.view,
                           kind=self.i.itsKind)

        testCollection = IndexedSelectionCollection(itsView=self.view,
                                                    source=k)
        for i in ["z", "y", "x", "w", "v"]:
            it = SimpleItem(i, label=i, itsView=self.view)

        self.assertEqual(len(list(testCollection)),8)

        testCollection.indexName = "label"

        self.assertEqual([testCollection[i].label for i in xrange(0, len(testCollection))],['i','i2','i3','v','w','x','y','z'])

        testCollection[len(testCollection)-1].label = 'u'
        self.assertEqual([testCollection[i].label for i in xrange(0, len(testCollection))],['i','i2','i3','u','v','w','x','y'])

    def testDelayedCreation(self):
        uc = UnionCollection('u', itsView=self.view)
        uc.addSource(self.b1)
        uc.addSource(self.b2)
        self.failUnless(getattr(uc, uc.__collection__) is not None)

        kc = KindCollection(itsView=self.view,
                            kind=self.view.findPath('Schema/Core/Parcel'))
        self.failUnless(getattr(kc, kc.__collection__) is not None)

        fc = FilteredCollection(itsView=self.view,
                                filterExpression=u"len(view[uuid].label) > 2",
                                filterAttributes=[ "label" ],
                                source=self.b1)
        self.failUnless(getattr(fc, fc.__collection__) is not None)

        fc1 = FilteredCollection(itsView=self.view,
                                 source=self.b1,
                                 filterExpression=u"len(view[uuid].label) > 2",
                                 filterAttributes=[ "label" ])
        self.failUnless(getattr(fc1, fc1.__collection__) is not None)

    def testBug2755(self):
        """
        Test to verify that bug 2755
        <https://bugzilla.osafoundation.org/show_bug.cgi?id=2755>
        is fixed.
        """
        k1 = KindCollection(itsView=self.view,
                            kind=self.i.itsKind)

        for i in k1:
            self.failUnless(i != None)
            break;

        for i in k1:
            self.failUnless(i != None)

    def testInclusionExclusionCollection(self):
        trash = ListCollection(itsView=self.view)
        coll1 = InclusionExclusionCollection(itsView=self.view, trash=trash)
        coll2 = InclusionExclusionCollection(itsView=self.view, trash=trash)
        coll3 = InclusionExclusionCollection(itsView=self.view, trash=trash)
        note = pim.Note(itsView=self.view)

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

    def testRemoveItem(self):
        # Simulate removing an item from a not-mine collection, ensuring it
        # doesn't go into the All collection, but rather moves to the Trash
        # if it's not in any other collections

        trash = ListCollection(itsView=self.view)
        notes = KindCollection(itsView=self.view,
                               kind=pim.Note.getKind(self.view),
                               recursive=True)
        notMine = UnionCollection(itsView=self.view)
        mine = DifferenceCollection(itsView=self.view,
            sources=[notes, notMine]
        )
        all = InclusionExclusionCollection(itsView=self.view, source=mine,
            exclusions=trash, trash=None)
        coll1 = InclusionExclusionCollection(itsView=self.view, trash=trash)
        coll2 = InclusionExclusionCollection(itsView=self.view, trash=trash)
        coll3 = InclusionExclusionCollection(itsView=self.view, trash=trash)
        notMine.addSource(coll1)
        note = pim.Note(itsView=self.view)

        # note is only in a not-mine collection, so removing it from that
        # collection should put it in the trash, and not appear in all
        coll1.add(note)
        self.assert_(note in coll1)
        self.assert_(note not in all)
        coll1.remove(note)
        self.assert_(note not in coll1)
        self.assert_(note not in all)
        self.assert_(note in trash)

        # note is in two collections, one of them a not-mine, so it shouldn't
        # be in either trash nor all
        coll1.add(note)
        coll2.add(note)
        self.assert_(note in coll1)
        self.assert_(note in coll2)
        self.assert_(note not in trash)
        self.assert_(note not in all)

        # removing note from the only not-mine collection should not move the
        # item to trash, and the item should appear in all
        coll1.remove(note)
        self.assert_(note not in coll1)
        self.assert_(note in coll2)
        self.assert_(note not in trash)
        self.assert_(note in all)

        # removing note from one not-mine collection, but having it still
        # remain in another not-mine collection should not have the item go
        # to trash, nor appear in all
        coll1.add(note)
        coll3.add(note)
        notMine.addSource(coll3)
        self.assert_(note in coll1)
        self.assert_(note in coll2)
        self.assert_(note in coll3)
        self.assert_(note not in trash)
        self.assert_(note not in all)
        coll3.remove(note)
        self.assert_(note in coll1)
        self.assert_(note in coll2)
        self.assert_(note not in coll3)
        self.assert_(note not in trash)
        self.assert_(note not in all)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
