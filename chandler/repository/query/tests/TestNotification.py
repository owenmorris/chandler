
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import repository.query.Query as Query
import repository.item.Item as Item
import chandlerdb.util.UUID as UUID

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
        GenerateItems.GenerateContacts(view, 100)
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

        q.subscribe(notify_client, 'handle')
        self._checkQuery(lambda i: not 'i' in i.firstName, q.resultSet)
        c = q.resultSet.next()
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
        GenerateItems.GenerateContacts(view, 100)
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
        q.subscribe(notify_client, 'handle')
        # subscribe via monitors
        q.monitor(monitor_client, 'handle')

        self._checkQuery(lambda i: not 'i' in i.firstName, q.resultSet)

        # get an item from the query
        c = q.resultSet.next()
        self.assert_('i' in c.firstName)
        self.rep.commit()

        #
        # Test monitor notifications
        #

        # make c leave the query
        c.firstName = 'Tom'
        (added, removed) = monitor_client.action
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
        GenerateItems.GenerateNotes(view, 20)
        GenerateItems.generateCalendarEventItems(view, 20, 5)
        GenerateItems.GenerateContacts(view, 10)
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

        union_query.subscribe(notify_client, 'handle')
        union_query.resultSet.next() # force evaluation of some of the query at least

        #test first query in union
        for1_query = self._compileQuery('testNotifyUnionQuery1','for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where i.displayName == "Meeting"')        
        one = for1_query.resultSet.next()
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
        two = for2_query.resultSet.next()
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
        
        three = for3_query.resultSet.next()
        self.rep.commit()
        origName = three.contactName.firstName
        three.contactName.firstName = "Harry"

        self.rep.commit()
        (added, removed) = notify_client.action
        self.assert_(len(added) == 0 and len(removed) == 1)
        three.contactName.firstName = origName

        self.rep.commit()
        (added, removed) = notify_client.action

        #The contact and it's name get changed
        self.assert_(len(added) == 2 and len(removed) == 0)

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
        q.subscribe(notify_client, 'handle')
        q.compile()

        for i in q:
            print i
        del kind.attributes[i.itsUUID]
        self.rep.commit()
        for i in q:
            print i


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
