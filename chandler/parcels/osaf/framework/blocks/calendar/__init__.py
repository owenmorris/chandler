# calendar blocks

from CalendarCanvas import (
    CalendarContainer,
    CalendarControl, 
    CanvasSplitterWindow
    
)

from AllDayCanvas import AllDayEventsCanvas
from TimedCanvas import TimedEventsCanvas

from CollectionCanvas import CollectionBlock
from CalendarBlocks import MiniCalendar, PreviewArea, PreviewPrefs



def installParcel(parcel, oldName=None):

    # pref instances
    PreviewPrefs.update(parcel, "previewPrefs")
