#!bin/env python

"""Model object representing a Task in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from InformationItem import InformationItem

class TaskItem(InformationItem):
    def __init__(self):
        InformationItem.__init__(self)
        self.title = None
        self.calendarDate = None
        self.dateDueBy = None
        self.isCompleted = None
        self.dateCompleted = None
        self.dateStart = None
        self.dateEnd = None
        self.recurrencePattern = None
        self.taskStatus = None



