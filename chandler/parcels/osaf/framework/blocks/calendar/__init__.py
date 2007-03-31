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

# calendar blocks

from CalendarCanvas import (
    CalendarContainer,
    CalendarControl, 
    CanvasSplitterWindow,
    VisibleHoursEvent,
)

from osaf.preferences import CalendarPrefs

from AllDayCanvas import AllDayEventsCanvas
from TimedCanvas import TimedEventsCanvas

from CollectionCanvas import CollectionBlock
from CalendarBlocks import MiniCalendar, PreviewArea, PreviewPrefs



def installParcel(parcel, oldName=None):

    from osaf.framework.blocks import BlockEvent
    
    # pref instances
    PreviewPrefs.update(parcel, "previewPrefs")
    CalendarPrefs.update(parcel, "calendarPrefs")

    # events
    for eventName in ('GoToNext', 'GoToPrev',
                      'GoToToday', 'GoToDate',
                      'DayView', 'WeekView',
                      'GoToCalendarItem'):
        BlockEvent.template(eventName,
                            dispatchToBlockName='MainCalendarControl'
                            ).install(parcel)
