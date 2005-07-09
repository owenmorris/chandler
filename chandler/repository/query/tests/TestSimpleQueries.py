
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004, 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase
import util.timing

class TestSimpleQueries(QueryTestCase.QueryTestCase):

    def testOutBoxQueryWithMail(self):
        self.loadParcels(
         ['parcel:osaf.contentmodel.mail']
        )

        import osaf.contentmodel.mail.Mail as Mail
        # create an outbound Mail item
        view = self.rep.view
        aMessage = Mail.MailMessage(view=view)
        aMessage.isInbound = True
        view.commit()
        # now run the query

        qString = u"for i in '//parcels/osaf/contentmodel/mail/MailMessageMixin' where i.isInbound == True"
        results = self._compileQuery('testOutboxQuery',qString)
        self._checkQuery(lambda i: not i.isInbound is True, results)

    def testKindQuery(self):
        """ Test a simulation of kindQuery """
        util.timing.reset()
        util.timing.begin("repository.query.tests.TestSimpleQueries.testKindQuery")
        results = self._compileQuery('testKindQuery','for i in "//Schema/Core/Kind" where True')
        self._checkQuery(lambda i: False, results)
        util.timing.end("repository.query.tests.TestSimpleQueries.testKindQuery")
        util.timing.results(verbose=False)

    def testFunctionKindQuery(self):
        """ Test calling a function in the query predicate """
        results = self._compileQuery('testFunctionQuery','for i in "//Schema/Core/Kind" where contains(i.itsName,"arc")')
        self._checkQuery(lambda i: not 'arc' in i.itsName, results)
                
    def testVariableKindQuery(self):
        """ Test query where source (kind) is specified in a variable """
        k = self.rep.findPath('//Schema/Core/Kind')
        results = self._compileQuery('testVariableKindQuery','for i in $1 where contains(i.itsName,"arc")', {"$1": ([k], None)})
        self._checkQuery(lambda i: not 'arc' in i.itsName, results)

    def testVariableRefCollectonQuery(self):
        """ Test query where source (ref collection) is specified in a variable """
        k = self.rep.findPath('//Schema/Core/Kind')
        results = self._compileQuery('testVariableRefCollectonQuery','for i in $1 where contains(i.itsName,"Kind")', {"$1": (k.itsUUID,'attributes')})
        self._checkQuery(lambda i: not 'Kind' in i.itsName, results)


    def testNotFunctionKindQuery(self):
        """ Test negating a function call in the query predicate """
        results = self._compileQuery('testNotFunctionKindQuery','for i in "//Schema/Core/Kind" where not contains(i.itsName,"arc")')
        self._checkQuery(lambda i: 'arc' in i.itsName, results)

    def testEqualityKindQuery(self):
        """ Test equality operator in the query predicate """
        results = self._compileQuery('testEqualityKindQuery','for i in "//Schema/Core/Kind" where i.itsName == "Item"')
        self._checkQuery(lambda i: not i.itsName == 'Item', results)

    def testInequalityKindQuery(self):
        """ Test inequality operator in the query predicate """
        results = self._compileQuery('testInequalityKindQuery','for i in "//Schema/Core/Kind" where i.itsName != "Item"')
        self._checkQuery(lambda i: not i.itsName != 'Item', results)

    def testLengthKindQuery(self):
        """ Test calling a unary function in the query predicate """
        results = self._compileQuery('testLengthKindQuery','for i in "//Schema/Core/Kind" where len(i.attributes) >= 4')
        self._checkQuery(lambda i: not len(i.attributes) >= 4, results)
        
    def testAndKindQuery(self):
        """ Test AND operator in the query predicate """
        results = self._compileQuery('testAndKindQuery','for i in "//Schema/Core/Kind" where contains(i.itsName,"arc") and len(i.attributes) >= 4')
        self._checkQuery(lambda i: not ("arc" in i.itsName and len(i.attributes) >= 4), results)

    def testNotAndKindQuery(self):
        """ Test AND NOT operation in the query predicate """
        results = self._compileQuery('testNotAndKindQuery','for i in "//Schema/Core/Kind" where contains(i.itsName,"arc") and not len(i.attributes) >= 4')
        self._checkQuery(lambda i: not ('arc' in i.itsName and not len(i.attributes) >= 4), results)

    def testMethodCallQuery(self):
        """  """
        results = self._compileQuery('testMethodCallQuery','for i in "//Schema/Core/Kind" where i.hasLocalAttributeValue("superKinds")')
        self._checkQuery(lambda i: not i.hasLocalAttributeValue("superKinds"), results)

    def testItemTraversalQuery(self):
        """ Test a multiple item path traversal in the query predicate """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
         ['parcel:osaf.contentmodel.contacts']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateContact)

        view.commit()
        
        results = self._compileQuery('testItemTraversalQuery',u"for i in '//parcels/osaf/contentmodel/contacts/Contact' where contains(i.contactName.firstName,'a')")
        self._checkQuery(lambda i: not 'a' in i.contactName.firstName, results)

    def testEnumerationQuery(self):
        """ Test an enumeration attribute in the query predicate """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
         ['parcel:osaf.contentmodel.calendar']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateCalendarEvent)

        view.commit()
        
        results = self._compileQuery('testEnumerationQuery',u"for i in '//parcels/osaf/contentmodel/calendar/CalendarEvent' where i.importance == 'fyi'")
        self._checkQuery(lambda i: not i.importance == 'fyi', results)

    def testRefCollectionQuery(self):
        """ Test a query over ref collections """
        import repository.query.Query as Query
        kind = self.rep.findPath('//Schema/Core/Kind')

        queryString = u"for i in $0 where contains(i.itsName,'ttributes')"
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testRefCollctionQuery', p, k, queryString)
        q.args ["$0"] = (kind.itsUUID, "attributes")

        self._checkQuery(lambda i: not 'ttributes' in i.itsName, q)

    def testWhereVariableQuery(self):
        """ Test using a variable in the where clause """
        queryString= 'for i in "//Schema/Core/Kind" where contains(i.itsName,$0)'
        import repository.query.Query as Query
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testWhereQuery', p, k, queryString)
        pattern = 'arc'
        q.args["$0"] = ( pattern, ) # one item tuple
        self._checkQuery(lambda i: not pattern in i.itsName, q)

    def testDateQuery(self):
        """ Test a date range in the query predicate """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
         ['parcel:osaf.contentmodel.calendar']
        )

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateCalendarEvent)

        view.commit()

        # since GenerateCalenderEventItems generates events offset from now(),
        # need to dynamically compute the date range for the query
        from datetime import date, datetime
        now = date.today()
        year = now.year
        month = now.month
        startDate = datetime(year, month, 1)
        if month == 12:
            month = 1
            year = year+1
        else:
            month = month+1
        endDate = datetime(year, month, 1)
        
        queryString = u"for i in '//parcels/osaf/contentmodel/calendar/CalendarEvent' where i.startTime > date(\"%s\") and i.startTime < date(\"%s\")" % (startDate.date(), endDate.date())
        results = self._compileQuery('testDateQuery',queryString)
        self._checkQuery(lambda i: not (i.startTime > startDate and i.startTime < endDate), results)

    def testTextQuery(self):
        """ Test a free text query """

        def checkLob(lob, value):
            reader = lob.getPlainTextReader()
            text = reader.read()
            reader.close()
            return value in text

        #@@@ use cineguide pack until we can do this from parcel.xml
        cineguidePack = os.path.join(self.rootdir,'repository', 'tests', 'data', 'packs', 'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

        results = self._compileQuery('testTextQuery1',u"for i in ftcontains('femme AND homme') where True")
        self._checkQuery(lambda i: not (checkLob(i.synopsis,"femme") and checkLob(i.synopsis,"homme")), results)

        results = self._compileQuery('testTextQuery2',u"for i in ftcontains('femme AND homme','synopsis') where True")
        self._checkQuery(lambda i: not (checkLob(i.synopsis,"femme") and checkLob(i.synopsis,"homme")), results)

        results = self._compileQuery('testTextQuery3',u"for i in ftcontains('femme AND homme','synopsis') where len(i.title) < 10")
        self._checkQuery(lambda i: not (checkLob(i.synopsis,"femme") and checkLob(i.synopsis,"homme") and len(i.title) < 10), results)

    def testBug1815(self):
        """ Test that missing attributes don't blow up the query [Bug 1815] """
        results = self._compileQuery('testTextQuery4','for i in "//Schema/Core/Kind" where contains(i.itsNme,"arc")')
        self._checkQuery(lambda i: not "arc" in i.itsNme, results)

    def testResetQueryString(self):
        """ Make sure we can change the query string and still get an answer"""
        import repository.query.Query as Query
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testResetQuery', p, k)
        self.assert_(len([ i for i in q]) == 0)
        q.queryString = 'for i in "//Schema/Core/Kind" where True'
        self.assert_(len([ i for i in q ]) == 17)
        q.queryString = 'for i in "//Schema/Core/Kind" where contains(i.itsName,"o")'
        self.assert_(len([ i for i in q ]) == 6)

    def testReloadQuery(self):
        """ Test to see that we can reload a query and it's result set from the store without recomputing the query contents """
        import repository.query.Query as Query
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testResetQuery', p, k, 'for i in "//Schema/Core/Kind" where True')
        self.assert_(len([ i for i in q ]) == 17)
        self.rep.check()
        self.rep.commit()
        uuid = q.itsUUID

        self._reopenRepository()
        q1 = self.rep.findUUID(uuid)
        self.assert_(len([ i for i in q1 ]) == 17)

    def testCopyQuery(self):
        """ Test to see that we can copy a query """
        import repository.query.Query as Query
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query('testCopyQuery', p, k, 'for i in "//Schema/Core/Kind" where True')
        self.assert_(len([ i for i in q ]) == 17)

        c = q.copy('testCopyQuery1')
        self.assert_(len([ i for i in c ]) == 17)
        self.assert_(c is not q)
        for i in q:
            if i not in c:
                self.fail()
        self.assert_(True)

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()

