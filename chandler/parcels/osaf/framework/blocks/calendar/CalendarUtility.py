#   Copyright (c) 2007 Open Source Applications Foundation
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

from datetime import timedelta
from PyICU import GregorianCalendar

GregorianCalendarInstance = GregorianCalendar()
ONE_WEEK = timedelta(7)

def getCalendarRange(targetDate, rangeType='week', firstDayOfWeek=None):
    """
    For week or month ranges, find the first preceding day whose weekday matches
    firstDayOfWeek, and the first day of the following range.  For day
    rangeType, just return targetDate.
    """
    if rangeType == 'day':
        return targetDate, targetDate + timedelta(1)
    
    if firstDayOfWeek is None:
        firstDayOfWeek = GregorianCalendarInstance.getFirstDayOfWeek()
    # ICU has sunday = 1, weekday() has monday = 0, so adjust by 2
    dayAdjust = (firstDayOfWeek - targetDate.weekday() - 2) % 7
    if dayAdjust != 0:
        dayAdjust -= 7
        
    if rangeType == 'week':
        start = targetDate + timedelta(dayAdjust)
        return start, start + ONE_WEEK
    
    if rangeType == 'multiweek':
        # find the first week of the month
        first_day_of_week = (targetDate.day + dayAdjust) % 7
        if first_day_of_week == 0:
            first_day_of_week = 7
            
        if first_day_of_week == 1:
            start = targetDate.replace(day=1)
        else:
            start = targetDate.replace(day=first_day_of_week) - ONE_WEEK

        end = start + 3 * ONE_WEEK
        month = end.month
        while end.month == month:
            end += ONE_WEEK
        #if end.day == 7:
            #end -= ONE_WEEK
        return start, end
