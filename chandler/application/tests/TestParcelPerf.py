__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.tests.RepositoryTestCase as RepositoryTestCase
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import tools.timing

class TestParcelPerf(RepositoryTestCase.RepositoryTestCase):

    def testLoadGenerateCommitContacts(self):
        """ Test loading, generating, and commiting contacts """
        tools.timing.reset()
        tools.timing.begin("application.tests.testParcelPerf.testContacts-load")
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/contacts']
        )
        tools.timing.end("application.tests.testParcelPerf.testContacts-load")

        view = self.rep.view
        tools.timing.begin("application.tests.testParcelPerf.testContacts-generate")
        GenerateItems.GenerateContacts(view, 100)
        tools.timing.end("application.tests.testParcelPerf.testContacts-generate")

        tools.timing.begin("application.tests.testParcelPerf.testContacts-commit")
        view.commit()
        tools.timing.end("application.tests.testParcelPerf.testContacts-commit")
        tools.timing.results(verbose=False)


    def testCalendarEvents(self):
        """ Test loading, generating, and commiting calendar event """
        tools.timing.reset()
        tools.timing.begin("application.tests.testParcelPerf.testCalendarEvents-load")
        self.loadParcels(
         ['http://osafoundation.org/parcels/osaf/contentmodel/calendar']
        )
        tools.timing.end("application.tests.testParcelPerf.testCalendarEvents-load")

        view = self.rep.view
        tools.timing.begin("application.tests.testParcelPerf.testCalendarEvents-generate")
        GenerateItems.generateCalendarEventItems(view, 100, 30)
        tools.timing.end("application.tests.testParcelPerf.testCalendarEvents-generate")

        tools.timing.begin("application.tests.testParcelPerf.testCalendarEvents-commit")
        view.commit()
        tools.timing.end("application.tests.testParcelPerf.testCalendarEvents-commit")
        tools.timing.results(verbose=False)
        


    def testLoadAllParcelItems(self):
        """ Load the entire content model into the repository and then commit it"""
        def load(parent):
            count = 0
            for child in parent.iterChildren():
                count += 1 + load(child)
            return count

        self.loadParcels(['http://osafoundation.org/parcels/osaf/contentmodel'])
        self.rep.commit()

        ##TODO SHOULD NOT RUN IN RAMDB
        self._reopenRepository()
        tools.timing.reset()
        tools.timing.begin("repository.tests.TestLoadAll")
        count = load(self.rep.view)
        tools.timing.end("repository.tests.TestLoadAll")
        tools.timing.results(verbose=False)

if __name__ == "__main__":
    unittest.main()
