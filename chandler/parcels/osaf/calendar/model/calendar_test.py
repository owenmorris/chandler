#!bin/env python

from model.persistence.FileRepository import FileRepository
from model.item.Item import Item
from OSAF.calendar.model.CalendarEvent import CalendarEvent
from OSAF.calendar.model.CalendarEvent import CalendarEventFactory
from mx import DateTime

rep = FileRepository('data')
rep.loadPack('model/packs/schema.pack', verbose=True)
rep.loadPack('parcels/OSAF/calendar/model/calendar.pack', verbose=True)

factory = CalendarEventFactory(rep)

foo = factory.NewItem()
foo.setAttribute('CalendarStartTime', DateTime.now())
foo.setAttribute('CalendarEndTime', DateTime.now())
foo.setAttribute('CalendarHeadline', "Test Event")

bar = factory.NewItem()
bar.setAttribute('CalendarStartTime', DateTime.now())
bar.setAttribute('CalendarEndTime', DateTime.now())
bar.setAttribute('CalendarHeadline', "Second Test Event")

rep.save()




