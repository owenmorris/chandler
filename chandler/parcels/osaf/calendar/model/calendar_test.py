#!bin/env python

from repository.persistence.FileRepository import FileRepository
from repository.item.Item import Item
from OSAF.calendar.model.CalendarEvent import CalendarEvent
from OSAF.calendar.model.CalendarEvent import CalendarEventFactory
from mx import DateTime

rep = FileRepository('data')
rep.open()
rep.loadPack('model/packs/schema.pack', verbose=True)
rep.loadPack('parcels/OSAF/calendar/model/calendar.pack', verbose=True)

factory = CalendarEventFactory(rep)

foo = factory.NewItem()
foo.setAttributeValue('CalendarStartTime', DateTime.now())
foo.setAttributeValue('CalendarEndTime', DateTime.now())
foo.setAttributeValue('CalendarHeadline', "Test Event")

bar = factory.NewItem()
bar.setAttributeValue('CalendarStartTime', DateTime.now())
bar.setAttributeValue('CalendarEndTime', DateTime.now())
bar.setAttributeValue('CalendarHeadline', "Second Test Event")

rep.close()
