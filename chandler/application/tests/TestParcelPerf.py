__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest
import repository.tests.RepositoryTestCase as RepositoryTestCase
import osaf.pim.generate as generate
import util.timing

class TestParcelPerf(RepositoryTestCase.RepositoryTestCase):

    def testLoadGenerateCommitContacts(self):
        """ Test loading, generating, and commiting contacts """
        util.timing.reset()
        util.timing.begin("application.tests.testParcelPerf.testContacts-load")
        self.loadParcels( ['osaf.pim.contacts'] )
        util.timing.end("application.tests.testParcelPerf.testContacts-load")

        view = self.rep.view
        util.timing.begin("application.tests.testParcelPerf.testContacts-generate")
        generate.GenerateItems(view, 100, generate.GenerateContact)
        util.timing.end("application.tests.testParcelPerf.testContacts-generate")

        util.timing.begin("application.tests.testParcelPerf.testContacts-commit")
        view.commit()
        util.timing.end("application.tests.testParcelPerf.testContacts-commit")
        util.timing.results(verbose=False)


    def testCalendarEvents(self):
        """ Test loading, generating, and commiting calendar event """
        util.timing.reset()
        util.timing.begin("application.tests.testParcelPerf.testCalendarEvents-load")
        self.loadParcels( ['osaf.pim.calendar'] )
        util.timing.end("application.tests.testParcelPerf.testCalendarEvents-load")

        view = self.rep.view
        util.timing.begin("application.tests.testParcelPerf.testCalendarEvents-generate")
        generate.GenerateItems(view, 100, generate.GenerateCalendarEvent)
        util.timing.end("application.tests.testParcelPerf.testCalendarEvents-generate")

        util.timing.begin("application.tests.testParcelPerf.testCalendarEvents-commit")
        view.commit()
        util.timing.end("application.tests.testParcelPerf.testCalendarEvents-commit")
        util.timing.results(verbose=False)



    def testLoadAllParcelItems(self):
        """ Load the entire content model into the repository and then commit it"""
        def load(parent):
            count = 0
            for child in parent.iterChildren():
                count += 1 + load(child)
            return count

        self.loadParcels(['osaf.pim'])
        view = self.rep.view
        view.commit()

        ##TODO SHOULD NOT RUN IN RAMDB
        self._reopenRepository()
        util.timing.reset()
        util.timing.begin("repository.tests.TestLoadAll")
        count = load(view)
        util.timing.end("repository.tests.TestLoadAll")
        util.timing.results(verbose=False)

if __name__ == "__main__":
    unittest.main()
