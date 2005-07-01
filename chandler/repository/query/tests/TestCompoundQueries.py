
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.query.tests.QueryTestCase as QueryTestCase

class TestCompoundQueries(QueryTestCase.QueryTestCase):

    def testDifferenceQuery(self):
        """ Test a difference query """
        results = self._compileQuery('testDifferenceQuery',"difference(for i in '//Schema/Core/Kind' where contains(i.itsName,'o'),for i in '//Schema/Core/Kind' where contains(i.itsName,'t'))")
        #@@@ TODO better result check
#        self._checkQuery(lambda i: not i.hasLocalAttributeValue("superKinds"), results)

    def testIntersectQuery(self):
        """ Test an intersection query """
        results = self._compileQuery('testIntersectionQuery',"intersect(for i in '//Schema/Core/Kind' where contains(i.itsName,'o'),for i in '//Schema/Core/Kind' where contains(i.itsName,'t'))")
        #@@@ TODO better result check
#        self._checkQuery(lambda i: not i.hasLocalAttributeValue("superKinds"), results)

    def testUnionQuery(self):
        """ Test a union query """
        import osaf.contentmodel.tests.GenerateItems as GenerateItems

        self.loadParcels(
         ['parcel:osaf.contentmodel']
        )

        #create test data
        view = self.rep.view
        GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateNote)
        GenerateItems.GenerateItems(view, 20, GenerateItems.GenerateCalendarEvent, days=5)
        GenerateItems.GenerateItems(view, 10, GenerateItems.GenerateContact)

        view.commit()

        results = self._compileQuery('testUnionQuery','union(for i in "//parcels/osaf/contentmodel/calendar/CalendarEvent" where True, for i in "//parcels/osaf/contentmodel/Note" where True, for i in "//parcels/osaf/contentmodel/contacts/Contact" where True)')
        # these checks could be more robust
        # check twice to make sure generator restarts
        self._checkQuery(lambda i: False, results)
        self._checkQuery(lambda i: False, results)

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
