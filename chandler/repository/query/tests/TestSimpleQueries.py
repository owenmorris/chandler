
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import tools.timing

class TestSimpleQueries(QueryTestCase.QueryTestCase):

    def testKindQuery(self):
        """ Test a simulation of kindQuery """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where True')
        self._checkQuery(lambda i: False, results)

    def testFunctionKindQuery(self):
        """ Test calling a function in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where contains(i.itsName,"arc")')
        self._checkQuery(lambda i: not 'arc' in i.itsName, results)
                
    def testVariableQuery(self):
        """ Test query where source is specified in a variable """
        k = self.rep.findPath('//Schema/Core/Kind')
        results = self._executeQuery(u'for i in $1 where contains(i.itsName,"arc")', [k])
        self._checkQuery(lambda i: not 'arc' in i.itsName, results)

    def testNotFunctionKindQuery(self):
        """ Test negating a function call in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where not contains(i.itsName,"arc")')
        self._checkQuery(lambda i: 'arc' in i.itsName, results)

    def testEqualityKindQuery(self):
        """ Test equality operator in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where i.itsName == "Item"')
        self._checkQuery(lambda i: not i.itsName == 'Item', results)

    def testInequalityKindQuery(self):
        """ Test inequality operator in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where i.itsName != "Item"')
        self._checkQuery(lambda i: not i.itsName != 'Item', results)

    def testLengthKindQuery(self):
        """ Test calling a unary function in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where len(i.attributes) >= 4')
        self._checkQuery(lambda i: not len(i.attributes) >= 4, results)
        
    def testAndKindQuery(self):
        """ Test AND operator in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where contains(i.itsName,"arc") and len(i.attributes) >= 4')
        self._checkQuery(lambda i: not ("arc" in i.itsName and len(i.attributes) >= 4), results)

    def testNotAndKindQuery(self):
        """ Test AND NOT operation in the query predicate """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where contains(i.itsName,"arc") and not len(i.attributes) >= 4')
        self._checkQuery(lambda i: not ('arc' in i.itsName and not len(i.attributes) >= 4), results)

    def testMethodCallQuery(self):
        """  """
        results = self._executeQuery(u'for i in "//Schema/Core/Kind" where i.hasAttributeValue("superKinds")')
        self._checkQuery(lambda i: not i.hasAttributeValue("superKinds"), results)

    def testItemTraversalQuery(self):
        """ Test a multiple item path traversal in the query predicate """
        tools.timing.reset()
        tools.timing.begin("Setup Infrastructure")
        import application
        import application.Globals as Globals
        import osaf.contentmodel.tests.GenerateItems as GenerateItems
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.repository = self.rep
        Globals.notificationManager = NotificationManager()
        tools.timing.end("Setup Infrastructure")

        tools.timing.begin("Load Contacts Parcel")
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/contacts']
        )
        tools.timing.end("Load Contacts Parcel")

        tools.timing.begin("Generate Contacts")
        GenerateItems.GenerateContacts(100)
        tools.timing.end("Generate Contacts")

        tools.timing.begin("Commit Contacts")
        self.rep.commit()
        tools.timing.end("Commit Contacts")
#        tools.timing.results()
        
        results = self._executeQuery(u"for i in '//parcels/osaf/contentmodel/contacts/Contact' where contains(i.contactName.firstName,'a')")
        self._checkQuery(lambda i: not 'a' in i.contactName.firstName, results)

    def testEnumerationQuery(self):
        """ Test an enumeration attribute in the query predicate """
        tools.timing.reset()
        tools.timing.begin("Setup Infrastructure")
        import application
        import application.Globals as Globals
        import osaf.contentmodel.tests.GenerateItems as GenerateItems
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.repository = self.rep
        Globals.notificationManager = NotificationManager()
        tools.timing.end("Setup Infrastructure")

        tools.timing.begin("Load Calendar Parcel")
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/calendar']
        )
        tools.timing.end("Load Calendar Parcel")

        tools.timing.begin("Generate Calendar Events")
        GenerateItems.generateCalendarEventItems(100,30)
        tools.timing.end("Generate Calendar Events")

        tools.timing.begin("Commit Calendar Events")
        self.rep.commit()
        tools.timing.end("Commit Calendar Events")
#        tools.timing.results()
        
        results = self._executeQuery(u"for i in '//parcels/osaf/contentmodel/calendar/CalendarEvent' where i.importance == 'fyi'")
        self._checkQuery(lambda i: not i.importance == 'fyi', results)

    def testRefCollectionQuery(self):
        """ Test a query over ref collections """
        import repository.query.Query as Query
        kind = self.rep.findPath('//Schema/Core/Kind')
        refcol = kind.attributes

        queryString = u"for i in $0 where contains(i.itsName,'ttributes')"
        q = Query.Query(self.rep, queryString)
        q.args = [ refcol ]
        q.execute()

        self._checkQuery(lambda i: not 'ttributes' in i.itsName, q)

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()

