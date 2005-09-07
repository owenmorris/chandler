from application import schema
from osaf import pim
from repository.item.Monitors import Monitors
import logging

logger = logging.getLogger(__name__)

from Sharing import (
    CloudXMLFormat, FileSystemConduit, ImportExportFormat, Share, ShareConduit,
    SimpleHTTPConduit, WebDAVAccount, WebDAVConduit
)

from ICalendar import ICalendarFormat


# The import/export mechanism needs a way to quickly map iCalendar UIDs to
# Chandler event items, so this singleton exists to store a ref collection
# containing imported calendar events, aliased by iCalendar UID:

class UIDMap(schema.Item):
    items = schema.Sequence("osaf.pim.CalendarEventMixin",
        otherName = "icalUIDMap",
        initialValue = {}
    )

    def icaluid_changed(self, op, item, attrName, *args, **kwds):

        if op == 'set':
            uid = getattr(item, 'icalUID', '')
            if uid:

                # @@@MOR These two lines are a workaround for not being able
                # to simply set a new alias -- Andi will have this fixed 
                # soon and I can get rid of these:
                if item in self.items:
                    self.items.remove(item)
                #

                self.items.append(item, uid)
                # logger.debug("uid_map -- added item %s, %s",
                #     item.getItemDisplayName(), uid)

        elif op == 'remove':
            self.items.remove(item)
            # logger.debug("uid_map -- Removed item %s",
            #     item.getItemDisplayName())


def installParcel(parcel, old_version=None):
    uid_map = UIDMap.update(parcel, 'uid_map')
    Monitors.attach(uid_map, 'icaluid_changed', 'set', 'icalUID')
    Monitors.attach(uid_map, 'icaluid_changed', 'remove', 'icalUID')
