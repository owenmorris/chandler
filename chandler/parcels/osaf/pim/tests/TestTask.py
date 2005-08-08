"""
Unit tests for task
"""

__revision__  = "$ $"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.tasks import Task
import osaf.pim.tests.TestContentModel as TestContentModel

from repository.util.Path import Path

class TaskTest(TestContentModel.ContentModelTestCase):
    """ Test Task """

    def testTask(self):
        """ Simple test for creating instances of tasks """

        def _verifyTask(task):
            self.assert_(task != None)
            self.assertEqual(task.displayName, "test headline")
            self.assertEqual(task.getItemDisplayName(), "test headline")

            self.assertEqual(task.importance, 'important')
            self.assertEqual(task.getAttributeValue('importance'), 'important')
            self.assertEqual(task.about, "test headline")
        
        self.loadParcel("parcel:osaf.pim.tasks")

        # Check that the globals got created by the parcel
        view = self.rep.view
        taskPath = Path('//parcels/osaf/pim/tasks')
        self.assert_(Task.getKind(view) != None)
        self.assert_(view.find(Path(taskPath, 'Task')) != None)

        self.assertEqual(Task.getKind(view),
                         view.find(Path(taskPath, 'Task')))

        # Construct A Sample Item
        taskItem = Task("TestTask", view=view)
        taskItem.displayName = "test headline"
        taskItem.importance = "important"

        self._reopenRepository()
        view = self.rep.view

        contentItemParent = view.findPath("//userdata")

        taskItem2 = contentItemParent.getItemChild("TestTask")
        _verifyTask(taskItem2)

if __name__ == "__main__":
    unittest.main()
