
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import tools.timing

class TestSimpleQueries(QueryTestCase.QueryTestCase):

    def testOutBoxQueryWithMail(self):
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/mail']
        )

        import osaf.contentmodel.mail.Mail as Mail
        # create an outbound Mail item
        aMessage = Mail.MailMessage()
        aMessage.isInbound = True
        self.rep.commit()
        # now run the query

        qString = u"for i in '//parcels/osaf/contentmodel/mail/MailMessageMixin' where i.isInbound == True"
        results = self._executeQuery(qString)
        self._checkQuery(lambda i: not i.isInbound is True, results)

    def testKindQuery(self):
        """ Test a simulation of kindQuery """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where True')
        self._checkQuery(lambda i: False, results)

    def testFunctionKindQuery(self):
        """ Test calling a function in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where contains(i.itsName,"arc")')
        self._checkQuery(lambda i: not 'arc' in i.itsName, results)
                
    def testVariableQuery(self):
        """ Test query where source is specified in a variable """
        k = self.rep.findPath('//Schema/Core/Kind')
        results = self._executeQuery('for i in $1 where contains(i.itsName,"arc")', {"$1": ([k], None)})
        self._checkQuery(lambda i: not 'arc' in i.itsName, results)

    def testNotFunctionKindQuery(self):
        """ Test negating a function call in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where not contains(i.itsName,"arc")')
        self._checkQuery(lambda i: 'arc' in i.itsName, results)

    def testEqualityKindQuery(self):
        """ Test equality operator in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where i.itsName == "Item"')
        self._checkQuery(lambda i: not i.itsName == 'Item', results)

    def testInequalityKindQuery(self):
        """ Test inequality operator in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where i.itsName != "Item"')
        self._checkQuery(lambda i: not i.itsName != 'Item', results)

    def testLengthKindQuery(self):
        """ Test calling a unary function in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where len(i.attributes) >= 4')
        self._checkQuery(lambda i: not len(i.attributes) >= 4, results)
        
    def testAndKindQuery(self):
        """ Test AND operator in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where contains(i.itsName,"arc") and len(i.attributes) >= 4')
        self._checkQuery(lambda i: not ("arc" in i.itsName and len(i.attributes) >= 4), results)

    def testNotAndKindQuery(self):
        """ Test AND NOT operation in the query predicate """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where contains(i.itsName,"arc") and not len(i.attributes) >= 4')
        self._checkQuery(lambda i: not ('arc' in i.itsName and not len(i.attributes) >= 4), results)

    def testMethodCallQuery(self):
        """  """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where i.hasAttributeValue("superKinds")')
        self._checkQuery(lambda i: not i.hasAttributeValue("superKinds"), results)

    def testItemTraversalQuery(self):
        """ Test a multiple item path traversal in the query predicate """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

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
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

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

        queryString = u"for i in $0 where contains(i.itsName,'ttributes')"
        q = Query.Query(self.rep, queryString)
        q.args ["$0"] = (kind.itsUUID, "attributes")
        q.execute()

        self._checkQuery(lambda i: not 'ttributes' in i.itsName, q)

    def testWhereVariableQuery(self):
        """ Test using a variable in the where clause """
        queryString= 'for i in "//Schema/Core/Kind" where contains(i.itsName,$0)'
        import repository.query.Query as Query
        q = Query.Query(self.rep, queryString)
        pattern = 'arc'
        q.args = [ pattern ]
        q.execute()
        self._checkQuery(lambda i: not pattern in i.itsName, q)

    def testDateQuery(self):
        """ Test a date range in the query predicate """
        tools.timing.reset()
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

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

        # since GenerateCalenderEventItems generates events offset from now(),
        # need to dynamically compute the date range for the query
        import mx.DateTime
        now = mx.DateTime.now()
        year = now.year
        month = now.month
        startDateString = "%d-%d-%d" % (year,month,1)
        startDate = mx.DateTime.ISO.ParseDate(startDateString)
        startDateString = startDate.date
        endDateString = "%d-%d-%d" % (year,month+1,1)
        endDate = mx.DateTime.ISO.ParseDate(endDateString) -1
        endDateString = endDate.date
        
        queryString = u"for i in '//parcels/osaf/contentmodel/calendar/CalendarEvent' where i.startTime > date(\"%s\") and i.startTime < date(\"%s\")" % (startDate.date,endDate.date)
        results = self._executeQuery(queryString)
        self._checkQuery(lambda i: not (i.startTime > startDate and i.startTime < endDate), results)

    def testTextQuery(self):
        """ Test a free text query """

        def checkLob(lob, value):
            reader = lob.getReader()
            text = reader.read()
            reader.close()
            return value in text

        #@@@ use cineguide pack until we can do this from parcel.xml
        cineguidePack = os.path.join(self.rootdir,'repository', 'tests', 'data', 'packs', 'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        results = self._executeQuery(u"for i in ftcontains('femme AND homme') where True")
        self._checkQuery(lambda i: not (checkLob(i.synopsis,"femme") and checkLob(i.synopsis,"homme")), results)

        results = self._executeQuery(u"for i in ftcontains('femme AND homme','synopsis') where True")
        self._checkQuery(lambda i: not (checkLob(i.synopsis,"femme") and checkLob(i.synopsis,"homme")), results)

        results = self._executeQuery(u"for i in ftcontains('femme AND homme','synopsis') where len(i.title) < 10")
        self._checkQuery(lambda i: not (checkLob(i.synopsis,"femme") and checkLob(i.synopsis,"homme") and len(i.title) < 10), results)

    def testBug1815(self):
        """ Test that missing attributes don't blow up the query [Bug 1815] """
        results = self._executeQuery('for i in "//Schema/Core/Kind" where contains(i.itsNme,"arc")')
        self._checkQuery(lambda i: not "arc" in i.itsNme, results)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()

