
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase

class TestCompoundQueries(QueryTestCase.QueryTestCase):

    def testUnionQuery(self):
        """ Test a union query """
        import application
        import application.Globals as Globals
        import osaf.contentmodel.tests.GenerateItems as GenerateItems
        from osaf.framework.notifications.NotificationManager import NotificationManager
        import osaf.contentmodel.ItemCollection as ItemCollection

        Globals.repository = self.rep
        Globals.notificationManager = NotificationManager()

        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel']
        )

        #create test data
        GenerateItems.GenerateNotes(20)
        GenerateItems.generateCalendarEventItems(20,5)
        GenerateItems.GenerateContacts(10)
        self.rep.commit()

        import logging
        self.rep.logger.setLevel(logging.DEBUG)
        results = self._executeQuery('union(for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where True, for i in "//parcels/osaf/contentmodel/Note" where True, for i in "//parcels/osaf/contentmodel/contacts/Contact" where True)')
        # these checks could be more robust
        # check twice to make sure generator restarts
        self._checkQuery(lambda i: False, results)
        self._checkQuery(lambda i: False, results)

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
#    unittest.main()
    pass
