#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
Unit tests for task
"""

import unittest, os

import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.tasks import Task
import osaf.pim.tests.TestDomainModel as TestDomainModel

from repository.util.Path import Path
from i18n.tests import uw

class TaskTest(TestDomainModel.DomainModelTestCase):
    """ Test Task """

    def testTask(self):
        """ Simple test for creating instances of tasks """

        def _verifyTask(task):
            self.assert_(task != None)
            self.assertEqual(task.displayName, uw("test headline"))
            self.assertEqual(task.getItemDisplayName(), uw("test headline"))

            self.assertEqual(task.importance, 'important')
            self.assertEqual(task.getAttributeValue('importance'), 'important')
            self.assertEqual(task.about, uw("test headline"))

        self.loadParcel("osaf.pim.tasks")

        # Check that the globals got created by the parcel
        view = self.rep.view
        taskPath = Path('//parcels/osaf/pim/tasks')
        self.assert_(Task.getKind(view) != None)
        self.assert_(view.find(Path(taskPath, 'Task')) != None)

        self.assertEqual(Task.getKind(view),
                         view.find(Path(taskPath, 'Task')))

        # Construct A Sample Item
        taskItem = Task("TestTask", itsView=view)
        taskItem.displayName = uw("test headline")
        taskItem.importance = "important"

        self._reopenRepository()
        view = self.rep.view

        contentItemParent = view.findPath("//userdata")

        taskItem2 = contentItemParent.getItemChild("TestTask")
        _verifyTask(taskItem2)

if __name__ == "__main__":
    unittest.main()
