
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import repository.query.Query as Query

class TestNotification(QueryTestCase.QueryTestCase):

    def testNotify(self):
        """ Test query notification """
        import application
        import application.Globals as Globals
        import osaf.contentmodel.tests.GenerateItems as GenerateItems
        from osaf.framework.notifications.NotificationManager import NotificationManager
        import osaf.contentmodel.ItemCollection as ItemCollection

        Globals.repository = self.rep
        Globals.notificationManager = NotificationManager()

        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/contacts',
          'http://osafoundation.org/parcels/osaf/contentmodel']
        )

        GenerateItems.GenerateContacts(100)

        self.rep.commit()

        ic = ItemCollection.NamedCollection()
        
        # basic query processing
        queryString = 'for i in "//parcels/osaf/contentmodel/contacts/ContactName" where contains(i.firstName,"i"))'
        q = Query.Query(self.rep, queryString)
        q.subscribe()
        r = q.execute()
        results = [ i for i in q ]
        self._checkQuery(lambda i: not 'i' in i.firstName, results)
        c = results[0]
        self.assert_('i' in c.firstName)
        # now make c leave the query
        c.firstName = 'Harry'
        self.rep.commit()
        self.assert_(c.firstName == 'Harry')
        # now make c come back into the query
        c.firstName = 'Michael'
        self.rep.commit()
        self.assert_('i' in c.firstName)
        #@@@ still need a way to check the notification results...

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
