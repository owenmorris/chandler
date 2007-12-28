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
Unit tests for notes parcel
"""

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
from osaf.pim.tasks import Task, TaskStamp
import osaf.pim.mail as Mail
import osaf.pim.calendar.Calendar as Calendar
import logging

#import wingdbstub

from datetime import datetime
from chandlerdb.util.Path import Path


class StampingTest(TestDomainModel.DomainModelTestCase):
    """ Test Stamping in the Domain Model """
    def testStamping(self):
        # Make sure the domain model is loaded.
        self.loadParcel("osaf.pim")
        # @@@ Also make sure the default imap account is loaded, in order to
        # have a "me" EmailAddress
        view = self.view

        # Get the stamp kinds
        taskStamp = TaskStamp
        eventStamp = Calendar.EventStamp

        # Create a Task, and do all kinds of stamping on it
        aTask = Task("aTask", itsView=view)

        eventStamp(aTask).add()
        taskStamp(aTask).remove()

    def testStampingAgain(self):
        self.testStamping()

if __name__ == "__main__":
    unittest.main()
