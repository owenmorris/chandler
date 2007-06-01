#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Unit tests for generated data
"""

import util.timing

from osaf.pim.tests.TestDomainModel import DomainModelTestCase
from repository.tests.RepositoryTestCase import RepositoryTestCase
from debug.generate import GenerateItems, GenerateContact, GenerateCalendarEvent


class ContactsTest(DomainModelTestCase):

    def testGeneratedContacts(self):

        self.loadParcels(["osaf.pim.contacts", "osaf.pim.mail"])

        view = self.view
        GenerateItems(view, 100, GenerateContact)
        view.commit()


class TestParcelPerf(RepositoryTestCase):

    def testCalendarEvents(self):
        """ Test loading, generating, and commiting calendar event """
        util.timing.reset()
        util.timing.begin("application.tests.testParcelPerf.testCalendarEvents-load")
        self.loadParcels( ['osaf.pim.calendar'] )
        util.timing.end("application.tests.testParcelPerf.testCalendarEvents-load")

        view = self.view
        util.timing.begin("application.tests.testParcelPerf.testCalendarEvents-generate")
        GenerateItems(view, 100, GenerateCalendarEvent)
        util.timing.end("application.tests.testParcelPerf.testCalendarEvents-generate")

        util.timing.begin("application.tests.testParcelPerf.testCalendarEvents-commit")
        view.commit()
        util.timing.end("application.tests.testParcelPerf.testCalendarEvents-commit")
        util.timing.results(verbose=False)

    def testLoadGenerateCommitContacts(self):
        """ Test loading, generating, and commiting contacts """

        util.timing.reset()
        util.timing.begin("application.tests.testParcelPerf.testContacts-load")
        self.loadParcels(['osaf.pim.contacts'])
        util.timing.end("application.tests.testParcelPerf.testContacts-load")

        view = self.view
        util.timing.begin("application.tests.testParcelPerf.testContacts-generate")
        GenerateItems(view, 100, GenerateContact)
        util.timing.end("application.tests.testParcelPerf.testContacts-generate")

        util.timing.begin("application.tests.testParcelPerf.testContacts-commit")
        view.commit()
        util.timing.end("application.tests.testParcelPerf.testContacts-commit")
        util.timing.results(verbose=False)


class CalendarTest(DomainModelTestCase):

    def testGeneratedEvents(self):

        self.loadParcel("osaf.pim.calendar")

        view = self.view
        GenerateItems(view, 100, GenerateCalendarEvent, days=100)
        view.commit()
