
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import repository.query.Query as Query
import repository.item.Item as Item
import repository.util.UUID as UUID

import NotificationItem


class TestNotification(QueryTestCase.QueryTestCase):

    def testNotifyFor(self):
        """ Test query notification """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems
        import osaf.contentmodel.ItemCollection as ItemCollection

        self.manager.path.append(os.path.join(self.testdir,'parcels'))
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/contacts',
          'http://osafoundation.org/parcels/osaf/contentmodel',
          'http://testparcels.org/notification']
        )

        GenerateItems.GenerateContacts(100)
        contact = GenerateItems.GenerateContact()
        contact.displayName = "Alexis"

        self.rep.commit()

        # basic query processing
        queryString = 'for i in "//parcels/osaf/contentmodel/contacts/ContactName" where contains(i.firstName,"i"))'
        q = Query.Query(self.rep, queryString)
#        notify_client = self.rep.findPath('//parcels/notification/testNotifier')      
        k = self.rep.findPath('//parcels/notification/NotificationItem')
        notify_client = NotificationItem.NotificationItem('testNotifier',self.rep,k)
        item = notify_client
        self.rep.commit()

        q.subscribe(notify_client, 'handle')
        r = q.execute()
        results = [ i for i in q ]
        self._checkQuery(lambda i: not 'i' in i.firstName, results)
        c = results[0]
        self.assert_('i' in c.firstName)

        # now make c leave the query
        c.firstName = 'Harry'
        self.rep.commit()
        self.assert_(notify_client.action == 'exited')
        self.assert_(c.firstName == 'Harry')

        # now make c come back into the query
        c.firstName = 'Michael'
        self.rep.commit()
        #import wingdbstub
        self.assert_('i' in c.firstName)
        self.assert_(notify_client.action == 'entered')

    def testNotifyUnion(self):
        """ Test notification of union query """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel']
        )

        #create test data
        GenerateItems.GenerateNotes(20)
        GenerateItems.generateCalendarEventItems(20,5)
        GenerateItems.GenerateContacts(10)
        # make sure there's at least one good data item
        import osaf.contentmodel.calendar.Calendar as Calendar
        import osaf.contentmodel.contacts.Contacts as Contacts
        import osaf.contentmodel.Notes as Notes
        event = GenerateItems.GenerateCalendarEvent(1)
        event.displayName = "Meeting"
        note = GenerateItems.GenerateNote()
        note.displayName = "story idea"
        contact = GenerateItems.GenerateContact()
        contact.displayName = "Alexis"
        
        self.rep.commit()

        queryString = 'union(for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where i.displayName == "Meeting", for i in "//parcels/osaf/contentmodel/Note" where contains(i.displayName,"idea"), for i in "//parcels/osaf/contentmodel/contacts/Contact" where contains(i.contactName.firstName,"i"))'

        union_query = Query.Query(self.rep, queryString)
        k = self.rep.findPath('//parcels/notification/NotificationItem')
        notify_client = NotificationItem.NotificationItem('testNotifier',self.rep,k)
        item = notify_client
        self.rep.commit()

        union_query.subscribe(notify_client, 'handle')
        union_query.execute()
        union_results = [i for i in union_query ]

        #test first query in union
        for1_results = self._compileQuery('for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where i.displayName == "Meeting"')
        for i in for1_results:
            one = i
            break
        self.rep.commit()
        one.displayName = "Lunch"

        self.rep.commit()
        self.assert_(notify_client.action == 'exited')
        one.displayName = "Meeting"

        self.rep.commit()
        self.assert_(notify_client.action == 'entered')
        
        # test second query in union
        for2_results = self._compileQuery('for i in "//parcels/osaf/contentmodel/Note" where contains(i.displayName,"idea")')
        for i in for2_results:
            two = i
            break
        self.rep.commit()
        origName = two.displayName
        two.displayName = "Foo"

        self.rep.commit()
        self.assert_(notify_client.action == 'exited')
        two.displayName = origName

        self.rep.commit()
        self.assert_(notify_client.action == 'entered')

        # test third query in Union -- has an item traversal
        for3_results = self._compileQuery('for i in "//parcels/osaf/contentmodel/contacts/Contact" where contains(i.contactName.firstName,"i")')
        for i in for3_results:
            three = i
            break

        self.rep.commit()
        origName = three.contactName.firstName
        three.contactName.firstName = "Harry"

        self.rep.commit()
        self.assert_(notify_client.action == 'exited')
        three.contactName.firstName = origName

        self.rep.commit()
        self.assert_(notify_client.action == 'entered')

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
        q = Query.Query(self.rep, queryString)
        q.args ["$0"] = (kind.itsUUID, "attributes")
        q.subscribe(notify_client, 'handle')
        q.execute()

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
