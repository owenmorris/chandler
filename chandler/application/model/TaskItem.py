#!bin/env python

"""Model object representing a Task in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from InformationItem import InformationItem

from RdfRestriction import RdfRestriction
from RdfNamespace import dc
from RdfNamespace import chandler

from mx.DateTime import *
_DateTimeType = type(now())

class TaskItem(InformationItem):

    rdfs = Persist.Dict()

    rdfs[chandler.calendarDate] = RdfRestriction(_DateTimeType, 0)
    rdfs[chandler.dueByDate] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.isCompleted] = RdfRestriction(str, 1)
    rdfs[chandler.startTime] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.endTime] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.taskStatus] = RdfRestriction(str, 1)
    rdfs[chandler.reminder] = RdfRestriction(InformationItem, 0) #ReminderItem
    rdfs[chandler.recurrence] = RdfRestriction(InformationItem, 0) #RecurrencePattern
    rdfs[chandler.percentCompleted] = RdfRestriction(int, 1)
    rdfs[chandler.totalWork] = RdfRestriction(int, 1)
    rdfs[chandler.actualWork] = RdfRestriction(int, 1)

    def __init__(self):
        InformationItem.__init__(self)

    # calendarDates = property(getCalendarDates, setCalendarDates)
    # dueByDate = property(getDueByDates, setDueByDates)
    # isCompleted = property(getIsCompleted, setIsCompleted)
    # startTime = property(getStartTime, setStartTime)
    # endTime = property(getEndTime, setEndTime)
    # taskStatus = property(getTaskStatus, endTaskStatus)
    # reminders = property(getReminders, setReminders)
    # percentCompleted = property(getPercentCompleted, setPercentCompleted)
    # totalWork = property(getTotalWork, setTotalWork)
    # actualWork = property(getActualWork, setActualWork)



