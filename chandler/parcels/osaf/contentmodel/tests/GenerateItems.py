"""
Generate sample items: calendar, contacts, etc.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import random

from mx import DateTime

import OSAF.contentmodel.calendar.Calendar as Calendar

HEADLINES = ["Dinner", "Lunch", "Meeting", "Movie", "Games"]

DURATIONS = [30, 60, 90, 120, 150, 180]

def GenerateCalendarEvent(days):
    event = Calendar.CalendarEvent()
    event.headline = random.choice(HEADLINES)
    
    # Choose random days, hours
    startDelta = DateTime.DateTimeDelta(random.randint(0, days),
                                        random.randint(0, 24))
    
    event.startTime = DateTime.now() + startDelta
    
    # Choose random minutes
    event.duration = DateTime.DateTimeDelta(0, 0, random.choice(DURATIONS))
    
def GenerateCalendarEvents(count, days):
    """ Generate _count_ events over the next _days_ number of days """
    for index in range(count):
        GenerateCalendarEvent(days)
