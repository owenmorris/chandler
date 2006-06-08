# calendar blocks

from CalendarCanvas import (
    CalendarContainer,
    CalendarControl, 
    CanvasSplitterWindow,
    CalendarPrefs,
    VisibleHoursEvent,
)

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