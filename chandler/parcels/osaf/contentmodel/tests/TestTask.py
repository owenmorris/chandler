"""
Unit tests for task
"""

__revision__  = "$ $"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems

import mx.DateTime as DateTime

from repository.util.Path import Path

""" LMDTODO Add tests for getAbout, getDisplay?, whoAttribute """

class TaskTest(TestContentModel.ContentModelTestCase):
    """ Test Task """

    def testTask(self):
        """ Simple test for creating instances of tasks """

        def _verifyTask(task):
            self.assert_(task != None)
            self.assertEqual(task.headline, "test headline")
            self.assertEqual(task.getAttributeValue('headline'),
                              "test headline")
            self.assertEqual(task.getItemDisplayName(), "test headline")

            self.assertEqual(task.importance, 'important')
            self.assertEqual(task.getAttributeValue('importance'), 'important')
            self.assertEqual(task.getAbout(), "test headline")
            self.assertEqual(task.getWho(), ' ')
            self.assertEqual(task.getDate(), ' ')
        
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/tasks")

        # Check that the globals got created by the parcel
        taskPath = Path('//parcels/osaf/contentmodel/tasks')
        self.assert_(Task.TaskParcel.getTaskKind() != None)
        self.assert_(self.rep.find(Path(taskPath, 'Task')) != None)

        self.assertEqual(Task.TaskParcel.getTaskKind(),
                         self.rep.find(Path(taskPath, 'Task')))

        # Construct A Sample Item
        taskItem = Task.Task("TestTask")
        taskItem.headline = "test headline"
        taskItem.importance = "important"

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata/contentitems")

        taskItem2 = contentItemParent.getItemChild("TestTask")
        _verifyTask(taskItem2)

if __name__ == "__main__":
    unittest.main()
