
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
        import osaf.pim.tests.GenerateItems as GenerateItems

        self.manager.path.append(os.path.join(self.testdir,'parcels'))
        self.loadParcels(
         ['osaf.pim.contacts',
          'osaf.pim',
          'repository.query.tests.NotificationItem']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateContact)
        contact = GenerateItems.GenerateContact(view)
        contact.contactName.firstName = "Alexis"

        view.commit()

        # basic query processing
        queryString = 'for i in "//parcels/osaf/pim/contacts/ContactName" where contains(i.firstName,"i"))'
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        q = Query.Query('testQuery', p, k, queryString)
        notify_client = NotificationItem.NotificationItem('testNotifier',view)
        item = notify_client
        view.commit()

        q.subscribe(notify_client, 'handle', False, True)
        self._checkQuery(lambda i: not 'i' in i.firstName, q.resultSet)
        c = q.resultSet.first()
        self.assert_('i' in c.firstName)
        view.commit()

        # now make c leave the query
        c.firstName = 'Harry'
        view.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)
        self.assert_(c.firstName == 'Harry')

        # now make c come back into the query
        c.firstName = 'Michael'
        view.commit()

        self.assert_('i' in c.firstName)
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

    def testMonitorFor(self):
        """ Test query notification via monitors """
        import osaf.pim.tests.GenerateItems as GenerateItems

        self.manager.path.append(os.path.join(self.testdir,'parcels'))
        self.loadParcels(
         ['osaf.pim.contacts',
          'osaf.pim',
          'repository.query.tests.parcels.notification']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateContact)
        contact = GenerateItems.GenerateContact(view)
        contact.contactName.firstName = "Alexis"

        view.commit()

        # basic query processing
        queryString = 'for i in "//parcels/osaf/pim/contacts/ContactName" where contains(i.firstName,"i"))'
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        q = Query.Query('testQuery', p, k, queryString)

        # create an item to handle monitor notifications
        monitor_client = NotificationItem.NotificationItem('testMonitorNotifier', view)

        # create an item to handle reguler commit notifications
        notify_client = NotificationItem.NotificationItem('testNotifier', view)
        # save Notification items and query
        view.commit()

        # subscribe via commit
        q.subscribe(notify_client, 'handle', False, True)
        # subscribe via monitors
        q.subscribe(monitor_client, 'handle', True, False)

        self._checkQuery(lambda i: not 'i' in i.firstName, q.resultSet)

        # get an item from the query
        c = q.resultSet.first()
        self.assert_('i' in c.firstName)
        view.commit()

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

        view.commit()

        (added, removed) = notify_client.action
        print "139: added = " + str(len(added)) + " removed = " + str(len(removed))
        self.assert_(len(added) == 0 and len(removed) == 1)
        self.assert_(c.firstName == 'Harry')

        # now make c come back into the query
        c.firstName = 'Michael'
        view.commit()

        self.assert_('i' in c.firstName)
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

    #def testNotifyUnion(self):
    #    """ Test notification of union query """
    #    import osaf.pim.tests.GenerateItems as GenerateItems

    #    self.loadParcels(
    #     ['osaf.pim']
    #    )

        #create test data
    #    view = self.rep.view
    #    GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateNote)
    #    GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateCalendarEvent, days=5)
    #    GenerateItems.GenerateItems(view, 10, GenerateItems.GenerateContact)

        # make sure there's at least one good data item
    #    import osaf.pim.calendar.Calendar as Calendar
    #    import osaf.pim.contacts as Contacts
    #    event = GenerateItems.GenerateCalendarEvent(view, 1)
    #    event.displayName = u"Meeting"
    #    note = GenerateItems.GenerateNote(view)
    #    note.displayName = u"story idea"
    #    contact = GenerateItems.GenerateContact(view)
    #    contact.contactName.firstName = "Alexis"
    #    view.commit()

    #    queryString = 'union(for i in "//parcels/osaf/pim/calendar/CalendarEvent" where i.displayName == u"Meeting", for i in "//parcels/osaf/pim/Note" where contains(i.displayName, u"idea"), for i in "//parcels/osaf/pim/contacts/Contact" where contains(i.contactName.firstName,"i"))'

    #    p = view.findPath('//Queries')
    #    k = view.findPath('//Schema/Core/Query')
    #    union_query = Query.Query('testQuery', p, k, queryString)
    #    notify_client = NotificationItem.NotificationItem('testNotifier',view)
    #    item = notify_client
    #    view.commit()

    #    union_query.subscribe(notify_client, 'handle', False, True)
    #    union_query.resultSet.first() # force evaluation of some of the query at least

        #test first query in union
    #    for1_query = self._compileQuery('testNotifyUnionQuery1','for i in "//parcels/osaf/pim/calendar/CalendarEvent" where i.displayName == u"Meeting"')        
    #    one = for1_query.resultSet.first()
    #    view.commit()
    #    one.displayName = u"Lunch"

    #    view.commit()
    #    (added, removed) = notify_client.action
    #    self.assert_(len(added) == 0 and len(removed) == 1)

    #    one.displayName = u"Meeting"
    #    view.commit()
    #    (added, removed) = notify_client.action
    #    self.assert_(len(added) == 1 and len(removed) == 0)
        
        # test second query in union
    #    for2_query = self._compileQuery('testNotifyUnionQuery2','for i in "//parcels/osaf/pim/Note" where contains(i.displayName,u"idea")')
    #    two = for2_query.resultSet.first()
    #    view.commit()

    #    origName = two.displayName
    #    two.displayName = u"Foo"
    #    view.commit()
    #    (added, removed) = notify_client.action
    #    self.assert_(len(added) == 0 and len(removed) == 1)

    #    two.displayName = origName
    #    view.commit()
    #    (added, removed) = notify_client.action
    #    self.assert_(len(added) == 1 and len(removed) == 0)

        # test third query in Union -- has an item traversal
    #    for3_query = self._compileQuery('testNotifyUnionQuery3','for i in "//parcels/osaf/pim/contacts/Contact" where contains(i.contactName.firstName,"i")')
        
    #    three = for3_query.resultSet.first()
    #    view.commit()
    #    origName = three.contactName.firstName
    #    assert 'i' in origName, "origName is %s" % origName
    #    three.contactName.firstName = "Harry"

    #    view.commit()
    #    (added, removed) = notify_client.action
#        self.assert_(len(added) == 0 and len(removed) == 1)
    #    three.contactName.firstName = origName

    #    view.commit()
    #    (added, removed) = notify_client.action

        #The contact and it's name get changed
#        self.assert_(len(added) == 2 and len(removed) == 0)

    def tstRefCollectionQuery(self):
        """ Test notification on a query over ref collections """
        #@@@ need repository support - when monitors are used
        import repository.query.Query as Query
        kind = view.findPath('//Schema/Core/Kind')

        notify_client = NotificationItem.NotificationItem('testNotifier',view)
        item = notify_client
        view.commit()

        queryString = "for i in $0 where True"
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        q = Query.Query('testQuery', p, k, queryString)
        q.args ["$0"] = (kind.itsUUID, "attributes")
        q.subscribe(notify_client, 'handle', False, True)
        q.compile()

        for i in q:
            print i
        del kind.attributes[i.itsUUID]
        view.commit()
        for i in q:
            print i

    def testBug2288(self):
        """ regression test for bug 2288 """
        import osaf.pim.tests.GenerateItems as GenerateItems

        self.loadParcels(
            ['osaf.pim.calendar']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateCalendarEvent)
        view.commit()

        queryString = "for i inevery '//parcels/osaf/pim/calendar/CalendarEventMixin' where i.hasLocalAttributeValue('reminderTime')"
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        q = Query.Query('bug2288Query', p, k, queryString)
        view.commit()

        for i in q.resultSet:
            print i, hasattr(i, 'reminderTime'), i.hasLocalAttributeValue('reminderTime')

        notify_client = NotificationItem.NotificationItem('testNotifier', view)
        monitor_client = NotificationItem.NotificationItem('testMonitorNotifier', view)
        item = notify_client

        q.subscribe(notify_client, 'handle', False, True)
        q.subscribe(monitor_client, 'handle', True, False)
        ce = q.resultSet.first()
        view.commit()

        # add the reminderTime attribute
        from datetime import datetime
        ce.reminderTime = datetime.now()
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        print len(q.resultSet)
        view.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        print len(q.resultSet)
        
        # create a new event.  without the reminderTime attribute
        from osaf.pim.calendar.Calendar import CalendarEvent
        monitor_client.action = ([],[])
        ev = CalendarEvent("test event", view=self.rep.view)
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)
        view.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 0)

        # add the existing reminderTime attribute
        monitor_client.action = ([],[])
        ev.reminderTime = datetime.now()
        (added, removed) = monitor_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)
        view.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 1 and len(removed) == 0)

        # remove the reminderTime attribute
        monitor_client.action = ([],[])
        #@@@ Monitor doesn't get called for delattr
        delattr(ev, 'reminderTime')
        (added, removed) = monitor_client.action
        print "Monitor: ", added, removed
#        self.assert_(len(added) == 0 and len(removed) == 1)
        view.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
