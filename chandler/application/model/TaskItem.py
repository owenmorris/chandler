#!bin/env python

"""Model object representing a Task in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from InformationItem import InformationItem

from RdfNamespace import dc
from RdfNamespace import chandler
from RdfNamespace import ical
from RdfNamespace import foaf

class TaskItem(InformationItem):

    rdfs[chandler.calendarDate] = (mx.DateTime, 0)
    rdfs[chandler.dueByDate] = (mx.DateTime, 1)
    rdfs[chandler.isCompleted] = (str, 1)
    rdfs[chandler.startTime] = (mx.DateTime, 1)
    rdfs[chandler.endTime] = (mx.DateTime, 1)
    rdfs[chandler.taskStatus] = (str, 1)
    rdfs[chandler.reminder] = (Reminder, 0)
    rdfs[chandler.recurrence] = (RecurrencePattern, 0)
    rdfs[chandler.percentCompleted] = (int, 1)
    rdfs[chandler.totalWork] = (int, 1)
    rdfs[chandler.actualWork] = (int, 1)

    calendarDates = property(getCalendarDates, setCalendarDates)
    dueByDate = property(getDueByDates, setDueByDates)
    isCompleted = property(getIsCompleted, setIsCompleted)
    startTime = property(getStartTime, setStartTime)
    endTime = property(getEndTime, setEndTime)
    taskStatus = property(getTaskStatus, endTaskStatus)
    reminders = property(getReminders, setReminders)
    percentCompleted = property(getPercentCompleted, setPercentCompleted)
    totalWork = property(getTotalWork, setTotalWork)
    actualWork = property(getActualWork, setActualWork)

    def __init__(self):
        InformationItem.__init__(self)



