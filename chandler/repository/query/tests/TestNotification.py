
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import repository.query.Query as Query
import repository.item.Item as Item

import NotificationItem


class TestNotification(QueryTestCase.QueryTestCase):

    def testNotifyFor(self):
        """ Test query notification """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.manager.path.append(os.path.join(self.testdir,'parcels'))
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/contacts',
          'http://osafoundation.org/parcels/osaf/contentmodel',
          'http://testparcels.org/notification']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateContact)
        contact = GenerateItems.GenerateContact(view)
        contact.contactName.firstName = "Alexis"

        view.commit()

        # basic query processing
        queryString = 'for i in "//parcels/osaf/contentmodel/contacts/ContactName" where contains(i.firstName,"i"))'
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testQuery', p, k, queryString)
        k = self.rep.findPath('//parcels/notification/NotificationItem')
        notify_client = NotificationItem.NotificationItem('testNotifier',self.rep,k)
        item = notify_client
        self.rep.commit()

        q.subscribe(notify_client, 'handle', False, True)
        self._checkQuery(lambda i: not 'i' in i.firstName, q.resultSet)
        c = q.resultSet.first()
        self.assert_('i' in c.firstName)
        self.rep.commit()

        # now make c leave the query
        c.firstName = 'Harry'
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)
        self.assert_(c.firstName == 'Harry')

        # now make c come back into the query
        c.firstName = 'Michael'
        self.rep.commit()

        self.assert_('i' in c.firstName)
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

    def testMonitorFor(self):
        """ Test query notification via monitors """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.manager.path.append(os.path.join(self.testdir,'parcels'))
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/contacts',
          'http://osafoundation.org/parcels/osaf/contentmodel',
          'http://testparcels.org/notification']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateContact)
        contact = GenerateItems.GenerateContact(view)
        contact.contactName.firstName = "Alexis"

        self.rep.commit()

        # basic query processing
        queryString = 'for i in "//parcels/osaf/contentmodel/contacts/ContactName" where contains(i.firstName,"i"))'
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testQuery', p, k, queryString)

        # create an item to handle monitor notifications
        k = self.rep.findPath('//parcels/notification/NotificationItem')
        monitor_client = NotificationItem.NotificationItem('testMonitorNotifier', self.rep, k)

        # create an item to handle reguler commit notifications
        notify_client = NotificationItem.NotificationItem('testNotifier',self.rep, k)
        # save Notification items and query
        self.rep.commit()

        # subscribe via commit
        q.subscribe(notify_client, 'handle', False, True)
        # subscribe via monitors
        q.subscribe(monitor_client, 'handle', True, False)

        self._checkQuery(lambda i: not 'i' in i.firstName, q.resultSet)

        # get an item from the query
        c = q.resultSet.first()
        self.assert_('i' in c.firstName)
        self.rep.commit()

        #
        # Test monitor notifications
        #

        # make c leave the query
        c.firstName = 'Tom'
        (added, removed) = monitor_client.action
        print "120: added = " + str(len(added)) + " removed = " + str(len(removed))
        self.assert_(len(added) == 0 and len(removed) == 1)

        # make c re-enter the query
        c.firstName = 'Dick'
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

        # make c re-enter the query
        c.firstName = 'Harry'
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)

        #
        # Test commit notifications
        #

        self.rep.commit()

        (added, removed) = notify_client.action
        print "139: added = " + str(len(added)) + " removed = " + str(len(removed))
        self.assert_(len(added) == 0 and len(removed) == 1)
        self.assert_(c.firstName == 'Harry')

        # now make c come back into the query
        c.firstName = 'Michael'
        self.rep.commit()

        self.assert_('i' in c.firstName)
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

    def testNotifyUnion(self):
        """ Test notification of union query """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel']
        )

        #create test data
        view = self.rep.view
        GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateNote)
        GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateCalendarEvent, days=5)
        GenerateItems.GenerateItems(view, 10, GenerateItems.GenerateContact)

        # make sure there's at least one good data item
        import osaf.contentmodel.calendar.Calendar as Calendar
        import osaf.contentmodel.contacts.Contacts as Contacts
        import osaf.contentmodel.Notes as Notes
        event = GenerateItems.GenerateCalendarEvent(view, 1)
        event.displayName = "Meeting"
        note = GenerateItems.GenerateNote(view)
        note.displayName = "story idea"
        contact = GenerateItems.GenerateContact(view)
        contact.contactName.firstName = "Alexis"
        view.commit()

        queryString = 'union(for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where i.displayName == "Meeting", for i in "//parcels/osaf/contentmodel/Note" where contains(i.displayName,"idea"), for i in "//parcels/osaf/contentmodel/contacts/Contact" where contains(i.contactName.firstName,"i"))'

        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        union_query = Query.Query('testQuery', p, k, queryString)
        k = self.rep.findPath('//parcels/notification/NotificationItem')
        notify_client = NotificationItem.NotificationItem('testNotifier',self.rep,k)
        item = notify_client
        self.rep.commit()

        union_query.subscribe(notify_client, 'handle', False, True)
        union_query.resultSet.first() # force evaluation of some of the query at least

        #test first query in union
        for1_query = self._compileQuery('testNotifyUnionQuery1','for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where i.displayName == "Meeting"')        
        one = for1_query.resultSet.first()
        self.rep.commit()
        one.displayName = "Lunch"

        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)

        one.displayName = "Meeting"
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        
        # test second query in union
        for2_query = self._compileQuery('testNotifyUnionQuery2','for i in "//parcels/osaf/contentmodel/Note" where contains(i.displayName,"idea")')
        two = for2_query.resultSet.first()
        self.rep.commit()

        origName = two.displayName
        two.displayName = "Foo"
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)

        two.displayName = origName
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

        # test third query in Union -- has an item traversal
        for3_query = self._compileQuery('testNotifyUnionQuery3','for i in "//parcels/osaf/contentmodel/contacts/Contact" where contains(i.contactName.firstName,"i")')
        
        three = for3_query.resultSet.first()
        self.rep.commit()
        origName = three.contactName.firstName
        assert 'i' in origName, "origName is %s" % origName
        three.contactName.firstName = "Harry"

        self.rep.commit()
        (added, removed) = notify_client.action
#        self.assert_(len(added) == 0 and len(removed) == 1)
        three.contactName.firstName = origName

        self.rep.commit()
        (added, removed) = notify_client.action

        #The contact and it's name get changed
#        self.assert_(len(added) == 2 and len(removed) == 0)

    def tstRefCollectionQuery(self):
        """ Test notification on a query over ref collections """
        #@@@ need repository support - when monitors are used
        import repository.query.Query as Query
        kind = self.rep.findPath('//Schema/Core/Kind')

        k = self.rep.findPath('//parcels/notification/NotificationItem')
        notify_client = NotificationItem.NotificationItem('testNotifier',self.rep,k)
        item = notify_client
        self.rep.commit()

        queryString = "for i in $0 where True"
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testQuery', p, k, queryString)
        q.args ["$0"] = (kind.itsUUID, "attributes")
        q.subscribe(notify_client, 'handle', False, True)
        q.compile()

        for i in q:
            print i
        del kind.attributes[i.itsUUID]
        self.rep.commit()
        for i in q:
            print i

    def testBug2288(self):
        """ regression test for bug 2288 """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
            ['http://osafoundation.org/parcels/osaf/contentmodel/calendar']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateCalendarEvent)
        view.commit()

        queryString = "for i inevery '//parcels/osaf/contentmodel/calendar/CalendarEventMixin' where i.hasLocalAttributeValue('reminderTime')"
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('bug2288Query', p, k, queryString)
        view.commit()

        for i in q.resultSet:
            print i, hasattr(i, 'reminderTime'), i.hasLocalAttributeValue('reminderTime')

        k = self.rep.findPath('//parcels/notification/NotificationItem')
        notify_client = NotificationItem.NotificationItem('testNotifier', self.rep, k)
        monitor_client = NotificationItem.NotificationItem('testMonitorNotifier', self.rep, k)
        item = notify_client

        q.subscribe(notify_client, 'handle', False, True)
        q.subscribe(monitor_client, 'handle', True, False)
        ce = q.resultSet.first()
        self.rep.commit()

        # add the reminderTime attribute
        from datetime import datetime
        ce.reminderTime = datetime.now()
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        print len(q.resultSet)
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        print len(q.resultSet)
        
        # create a new event.  without the reminderTime attribute
        from osaf.contentmodel.calendar.Calendar import CalendarEvent
        monitor_client.action = ([],[])
        ev = CalendarEvent("test event", view=self.rep.view)
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 0 and len(removed) == 0)
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 0)

        # add the existing reminderTime attribute
        monitor_client.action = ([],[])
        ev.reminderTime = datetime.now()
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

        # remove the reminderTime attribute
        monitor_client.action = ([],[])
        #@@@ Monitor doesn't get called for delattr
        delattr(ev, 'reminderTime')
        (added, removed) = monitor_client.action
        print "Monitor: ", added, removed
#        self.assert_(len(added) == 0 and len(removed) == 1)
        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
