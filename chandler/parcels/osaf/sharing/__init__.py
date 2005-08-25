from application import schema
from osaf import pim

from Sharing import (
    CloudXMLFormat, FileSystemConduit, ImportExportFormat, Share, ShareConduit,
    SimpleHTTPConduit, WebDAVAccount, WebDAVConduit
)

from ICalendar import ICalendarFormat


# The import/export mechanism needs a way to quickly map iCalendar UIDs to
# Chandler event items, so this singleton exists to store a ref collection
# containing imported calendar events, aliased by iCalendar UID:

class UIDMap(schema.Item):
    items = schema.Sequence(pim.CalendarEventMixin,
        inverse = "icalUIDMap",
        initialValue = {}
    )

def installParcel(parcel, old_version=None):
    UIDMap.update(parcel, "uid_map")
