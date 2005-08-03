"""
Unit tests for notes parcel
"""

__revision__  = "$Revision: 5832 $"
__date__      = "$Date: 2005-06-30 23:01:20Z $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.mail as Mail
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import logging

#import wingdbstub

from datetime import datetime
from repository.util.Path import Path


class StampingTest(TestContentModel.ContentModelTestCase):
    """ Test Stamping in the Content Model """
    def testStamping(self):
        # Make sure the contentModel is loaded.
        self.loadParcel("parcel:osaf.contentmodel")
        # @@@ Also make sure the default imap account is loaded, in order to
        # have a "me" EmailAddress
        view = self.rep.view
        
        # Get the stamp kinds
        taskMixin = Task.TaskMixin.getKind(view)
        eventMixin = Calendar.CalendarEventMixin.getKind(view)
        add = 'add'
        remove = 'remove'

        # Create a Task, and do all kinds of stamping on it
        aTask = Task.Task("aTask", view=view)

        aTask.StampKind(add, eventMixin)
        aTask.StampKind(remove, taskMixin)

    def testStampingAgain(self):
        self.testStamping()

if __name__ == "__main__":
    unittest.main()
