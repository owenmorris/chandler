"""
A helper class which sets up and tears down dual RamDB repositories
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, sys, os
import repository.persistence.DBRepository as DBRepository
import repository.item.Item as Item
import application.Parcel as Parcel
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.query.Query as Query
import datetime
import vobject

class ICalendarTestCase(unittest.TestCase):

    def runTest(self):
        self._setup()
        self.SummaryAndDateTimeImported()
        self.DateImportAsAllDay()
        self.ItemsToVobject()
        self.writeICalendarUnicodeBug3338()
        self.importRecurrence()
        self.importRecurrenceWithTimezone()
        self._teardown()

    def _setup(self):

        rootdir = os.environ['CHANDLERHOME']
        packs = (
         os.path.join(rootdir, 'repository', 'packs', 'chandler.pack'),
        )
        parcelpath = [os.path.join(rootdir, 'parcels')]

        namespaces = [
         'parcel:osaf.sharing',
         'parcel:osaf.contentmodel.calendar',
        ]

        self.repo = self._initRamDB(packs)
        self.manager = Parcel.Manager.get(self.repo.view,
                                          path=parcelpath)
        self.manager.loadParcels(namespaces)
        # create a sandbox root
        self.sandbox = Item.Item("sandbox", self.repo, None)
        self.repo.commit()

    def _teardown(self):
        pass

    def _initRamDB(self, packs):
        repo = DBRepository.DBRepository(None)
        repo.create(ramdb=True, stderr=False, refcounted=True)
        for pack in packs:
            repo.loadPack(pack)
        repo.commit()
        return repo

    def Import(self, view, filename):

        path = os.path.join(os.getenv('CHANDLERHOME') or '.',
                            'parcels', 'osaf', 'sharing', 'tests')

        sandbox = self.repo.findPath("//sandbox")

        conduit = Sharing.FileSystemConduit(parent=sandbox, sharePath=path,
                                            shareName=filename, view=view)
        format = ICalendar.ICalendarFormat(parent=sandbox)
        self.share = Sharing.Share(parent=sandbox, conduit=conduit,
                                   format=format)
        self.share.get()
        return format

    def SummaryAndDateTimeImported(self):
        format = self.Import(self.repo.view, 'Chandler.ics')
        event = format.findUID('BED962E5-6042-11D9-BE74-000A95BB2738')
        self.assert_(event.displayName == u'3 hour event',
         "SUMMARY of first VEVENT not imported correctly, displayName is %s"
         % event.displayName)
        evtime = datetime.datetime(2005,1,1, hour = 23, tzinfo = ICalendar.utc)
        evtime = evtime.astimezone(ICalendar.localtime).replace(tzinfo=None)
        self.assert_(event.startTime == evtime,
         "startTime not set properly, startTime is %s"
         % event.startTime)

    def DateImportAsAllDay(self):
        format = self.Import(self.repo.view, 'AllDay.ics')
        event = format.findUID('testAllDay')
        self.assert_(event.startTime == datetime.datetime(2005,1,1),
         "startTime not set properly for all day event, startTime is %s"
         % event.startTime)
        self.assert_(event.allDay == True,
         "allDay not set properly for all day event, allDay is %s"
         % event.allDay)
         
    def ItemsToVobject(self):
        """Tests itemsToVObject, which converts Chandler items to vobject."""
        event = Calendar.CalendarEvent(view = self.repo.view)
        event.displayName = "test"
        event.startTime = datetime.datetime(2010, 1, 1, 10)
        event.endTime = datetime.datetime(2010, 1, 1, 11)        

        cal = ICalendar.itemsToVObject(self.repo.view, [event])

        self.assert_(cal.vevent[0].summary[0].value == "test",
         "summary not set properly, summary is %s"
         % cal.vevent[0].summary[0].value)

        start = event.startTime.replace(tzinfo=ICalendar.localtime)

        self.assert_(cal.vevent[0].dtstart[0].value == start,
         "dtstart not set properly, dtstart is %s"
         % cal.vevent[0].summary[0].value)

        event = Calendar.CalendarEvent(view = self.repo.view)
        event.displayName = "test2"
        event.startTime = datetime.datetime(2010, 1, 1)
        event.allDay = True        

        cal = ICalendar.itemsToVObject(self.repo.view, [event])

        self.assert_(cal.vevent[0].dtstart[0].value == datetime.date(2010,1,1),
         "dtstart for allDay event not set properly, dtstart is %s"
         % cal.vevent[0].summary[0].value)
         # test bug 3509, all day event duration is off by one
         
    def writeICalendarUnicodeBug3338(self):
        event = Calendar.CalendarEvent(view = self.repo.view)
        event.displayName = u"unicode \u0633\u0644\u0627\u0645"
        event.startTime = datetime.datetime(2010, 1, 1, 10)
        event.endTime = datetime.datetime(2010, 1, 1, 11)

        coll = ItemCollection.ItemCollection(name="testcollection", 
                                             parent=self.sandbox)
        coll.add(event)
        filename = "unicode_export.ics"

        conduit = Sharing.FileSystemConduit(name="conduit", sharePath=".",
                            shareName=filename, view=self.repo.view)
        format = ICalendar.ICalendarFormat(name="format", view=self.repo.view)
        self.share = Sharing.Share(name="share",contents=coll, conduit=conduit,
                                    format=format, view=self.repo.view)
        if self.share.exists():
            self.share.destroy()
        self.share.create()
        self.share.put()
        cal=vobject.readComponents(file(filename, 'rb')).next()
        self.assertEqual(cal.vevent[0].summary[0].value, event.displayName)
        self.share.destroy()

    def importRecurrence(self):
        format = self.Import(self.repo.view, 'Recurrence.ics')
        event = format.findUID('5B30A574-02A3-11DA-AA66-000A95DA3228')
        third = event.getNextOccurrence().getNextOccurrence()
        self.assertEqual(third.displayName, 'Changed title')
        self.assertEqual(third.recurrenceID, datetime.datetime(2005, 8, 10))
        # while were at it, test bug 3509, all day event duration is off by one
        self.assertEqual(event.duration, datetime.timedelta(0))

    def importRecurrenceWithTimezone(self):
        format = self.Import(self.repo.view, 'RecurrenceWithTimezone.ics')
        event = format.findUID('FF14A660-02A3-11DA-AA66-000A95DA3228')
        third = event.modifications.first()
        print third.serializeMods().getvalue()
        self.assertEqual(third.rruleset.rrules.first().freq, 'daily')

         
# test import/export unicode

if __name__ == "__main__":
    unittest.main()
