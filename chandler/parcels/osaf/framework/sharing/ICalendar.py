import Sharing
import application.Parcel
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.calendar.Calendar as Calendar
from chandlerdb.util.UUID import UUID
import StringIO
import vobject
import logging
import mx

logger = logging.getLogger('ICalendar')
logger.setLevel(logging.INFO)

class ICalendarFormat(Sharing.ImportExportFormat):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ICalendarFormat"

    __calendarEventPath = "//parcels/osaf/contentmodel/calendar/CalendarEvent"

    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def importProcess(self, text, extension=None, item=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        if item is None:
            item = ItemCollection.ItemCollection()
        else:
            if isinstance(item, Sharing.Share):
                if item.contents is None:
                    item.contents = ItemCollection.ItemCollection()
                item = item.contents

        if not isinstance(item, ItemCollection.ItemCollection):
            print "Only a share or an item collection can be passed in"
            #@@@MOR Raise something

        # @@@MOR Total hack
        newtext = []
        for c in text:
            if ord(c) > 127:
                c = " "
            newtext.append(c)
        text = "".join(newtext)

        input = StringIO.StringIO(text)
        calendar = vobject.readComponents(input, validate=True).next()

        countNew = 0
        countUpdated = 0
        eventKind = self.itsView.findPath(self.__calendarEventPath)

        for event in calendar.vevent:
            # See if we have a corresponding item already, or create one
            uuid = UUID(event.uid[0].value[:36]) # @@@MOR, stripping "-RID"
            eventItem = self.itsView.findUUID(uuid)
            if eventItem is None:
                # @@@MOR This needs to use the new defaultParent framework
                # to determine the parent
                eventItem = application.Parcel.NewItem(self.itsView,
                 None, self.itsView.findPath("//userdata"),
                 eventKind, uuid)
                countNew += 1
            else:
                countUpdated += 1

            try:
                eventItem.displayName = event.summary[0].value
            except AttributeError:
                eventItem.displayName = ""

            try:
                eventItem.description = event.description[0].value
                # print "Has a description:", eventItem.description
            except AttributeError:
                eventItem.description = ""

            dt = event.dtstart[0].value
            eventItem.startTime = \
             mx.DateTime.ISO.ParseDateTime(dt.isoformat())

            try:
                dt = event.dtend[0].value
                eventItem.endTime = \
                 mx.DateTime.ISO.ParseDateTime(dt.isoformat())
            except:
                eventItem.duration = mx.DateTime.DateTimeDelta(0, 1)

            item.add(eventItem)
            # print "Imported", eventItem.displayName, eventItem.startTime,
            #  eventItem.duration, eventItem.endTime
        logger.info("...iCalendar import of %d new items, %d updated" % \
         (countNew, countUpdated))

        return item

    def exportProcess(self, item, depth=0):
        # item is the whole collection
        pass
