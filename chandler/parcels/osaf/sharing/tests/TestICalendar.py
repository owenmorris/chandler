"""
A helper class which sets up and tears down dual RamDB repositories
"""
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, sys, os
import repository.persistence.DBRepository as DBRepository
import repository.item.Item as Item
import application.Parcel as Parcel
from application import schema
from osaf import pim, sharing
import osaf.sharing.ICalendar as ICalendar
from osaf.pim import ListCollection
import osaf.pim.calendar.Calendar as Calendar
import datetime
import vobject
import cStringIO
from PyICU import ICUtzinfo
from dateutil import tz
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from i18n.tests import uw

class ICalendarTestCase(unittest.TestCase):

    def runTest(self):
        self._setup()
        self.SummaryAndDateTimeImported()
        self.DateImportAsAllDay()
        self.ItemsToVobject()
        self.writeICalendarUnicodeBug3338()
        self.importRecurrence()
        self.importRecurrenceWithTimezone()
        self.importReminders()
        self.exportRecurrence()
        self.ExportFreeBusy()
        self._teardown()

    def _setup(self):

        rootdir = os.environ['CHANDLERHOME']
        packs = (
         os.path.join(rootdir, 'repository', 'packs', 'chandler.pack'),
        )
        parcelpath = [os.path.join(rootdir, 'parcels')]

        namespaces = [
         'osaf.sharing',
         'osaf.pim.calendar',
        ]

        self.repo = self._initRamDB(packs)
        view = self.repo.view
        self.manager = Parcel.Manager.get(view, path=parcelpath)
        self.manager.loadParcels(namespaces)
        # create a sandbox root
        self.sandbox = Item.Item("sandbox", view, None)
        view.commit()

    def _teardown(self):
        pass

    def _initRamDB(self, packs):
        repo = DBRepository.DBRepository(None)
        repo.create(ramdb=True, stderr=False, refcounted=True)
        view = repo.view
        for pack in packs:
            view.loadPack(pack)
        view.commit()
        return repo

    def Import(self, view, filename):

        sharePath = os.path.join(os.getenv('CHANDLERHOME') or '.',
                                 'parcels', 'osaf', 'sharing', 'tests')

        #sharePath is stored as schema.Text so convert to unicode
        sharePath = unicode(sharePath, sys.getfilesystemencoding())

        sandbox = view.findPath("//sandbox")

        conduit = sharing.FileSystemConduit(itsParent=sandbox, sharePath=sharePath,
                                            shareName=filename)
        format = ICalendar.ICalendarFormat(itsParent=sandbox)
        self.share = sharing.Share(itsParent=sandbox, conduit=conduit,
                                   format=format)
        self.share.sync(modeOverride='get')
        return format

    def SummaryAndDateTimeImported(self):
        format = self.Import(self.repo.view, u'Chandler.ics')
        event = Calendar.findUID(self.repo.view, 'BED962E5-6042-11D9-BE74-000A95BB2738')
        self.assert_(event.displayName == u'3 ho\u00FCr event',
         u"SUMMARY of first VEVENT not imported correctly, displayName is %s"
         % event.displayName)
        evtime = datetime.datetime(2005,1,1, hour = 23, tzinfo = ICalendar.utc)
        self.assert_(event.startTime == evtime,
         "startTime not set properly, startTime is %s"
         % event.startTime)

    def DateImportAsAllDay(self):
        format = self.Import(self.repo.view, u'AllDay.ics')
        event = Calendar.findUID(self.repo.view, 'testAllDay')
        self.assert_(event.startTime ==
                     datetime.datetime(2005,1,1, tzinfo=ICUtzinfo.floating),
         "startTime not set properly for all day event, startTime is %s"
         % event.startTime)
        self.assert_(event.allDay == True,
         "allDay not set properly for all day event, allDay is %s"
         % event.allDay)

    def ExportFreeBusy(self):
        format = self.Import(self.repo.view, u'AllDay.ics')
        collection = self.share.contents
        schema.ns('osaf.pim', self.repo.view).mine.addSource(collection)

        start = datetime.datetime(2005,1,1, tzinfo=ICUtzinfo.floating)
        end = start + datetime.timedelta(2)

        cal = ICalendar.itemsToFreeBusy(self.repo.view, start, end)
        self.assertEqual(cal.vfreebusy.freebusy.value[0][1], datetime.timedelta(1))

    def ItemsToVobject(self):
        """Tests itemsToVObject, which converts Chandler items to vobject."""
        event = Calendar.CalendarEvent(itsView = self.repo.view)
        event.anyTime = False
        event.displayName = uw("test")
        event.startTime = datetime.datetime(2010, 1, 1, 10,
                                            tzinfo=ICUtzinfo.default)
        event.endTime = datetime.datetime(2010, 1, 1, 11,
                                          tzinfo=ICUtzinfo.default)

        cal = ICalendar.itemsToVObject(self.repo.view, [event])

        self.assert_(cal.vevent.summary.value == uw("test"),
         u"summary not set properly, summary is %s"
         % cal.vevent.summary.value)

        start = event.startTime
        self.assert_(cal.vevent.dtstart.value == start,
         "dtstart not set properly, dtstart is %s"
         % cal.vevent.summary.value)

        event = Calendar.CalendarEvent(itsView = self.repo.view)
        event.displayName = uw("test2")
        event.startTime = datetime.datetime(2010, 1, 1, 
                                            tzinfo=ICUtzinfo.floating)
        event.allDay = True

        cal = ICalendar.itemsToVObject(self.repo.view, [event])

        self.assert_(cal.vevent.dtstart.value == datetime.date(2010,1,1),
         u"dtstart for allDay event not set properly, dtstart is %s"
         % cal.vevent.summary.value)
         # test bug 3509, all day event duration is off by one

    def writeICalendarUnicodeBug3338(self):
        event = Calendar.CalendarEvent(itsView = self.repo.view)
        event.displayName = u"unicode \u0633\u0644\u0627\u0645"
        event.startTime = datetime.datetime(2010, 1, 1, 10,
                                            tzinfo=ICUtzinfo.default)
        event.endTime = datetime.datetime(2010, 1, 1, 11,
                                          tzinfo=ICUtzinfo.default)

        coll = ListCollection("testcollection", itsParent=self.sandbox)
        coll.add(event)
        filename = u"unicode_export.ics"

        conduit = sharing.FileSystemConduit("conduit", sharePath=u".",
                            shareName=filename, itsView=self.repo.view)
        format = ICalendar.ICalendarFormat("format", itsView=self.repo.view)
        self.share = sharing.Share("share",contents=coll, conduit=conduit,
                                    format=format, itsView=self.repo.view)
        if self.share.exists():
            self.share.destroy()
        self.share.create()
        self.share.sync(modeOverride='put')
        cal=vobject.readComponents(file(filename, 'rb')).next()
        self.assertEqual(cal.vevent.summary.value, event.displayName)
        self.share.destroy()

    def importRecurrence(self):
        format = self.Import(self.repo.view, u'Recurrence.ics')
        event = Calendar.findUID(self.repo.view, '5B30A574-02A3-11DA-AA66-000A95DA3228')
        third = event.getNextOccurrence().getNextOccurrence()
        self.assertEqual(third.displayName, u'\u00FCChanged title')
        self.assertEqual(third.recurrenceID, datetime.datetime(2005, 8, 10, 
                                                    tzinfo=ICUtzinfo.floating))
        # while were at it, test bug 3509, all day event duration is off by one
        self.assertEqual(event.duration, datetime.timedelta(0))
        # make sure we imported the floating EXDATE
        event = Calendar.findUID(self.repo.view, '07f3d6f0-4c04-11da-b671-0013ce40e90f')
        self.assertEqual(event.rruleset.exdates[0], datetime.datetime(2005, 12, 6, 12, 30,
                                                    tzinfo=ICUtzinfo.floating))

    def importRecurrenceWithTimezone(self):
        format = self.Import(self.repo.view, u'RecurrenceWithTimezone.ics')
        event = Calendar.findUID(self.repo.view, 'FF14A660-02A3-11DA-AA66-000A95DA3228')
        # THISANDFUTURE change creates a new event, so there's nothing in
        # event.modifications
        self.assertEqual(event.modifications, None)

    def importUnusualTzid(self):
        format = self.Import(self.repo.view, u'UnusualTzid.ics')
        event = Calendar.findUID(self.repo.view, '42583280-8164-11da-c77c-0011246e17f0')
        self.assertEqual(event.startTime.tzinfo, ICUtzinfo.getInstance('US/Mountain'))

    def importReminders(self):
        format = self.Import(self.repo.view, u'RecurrenceWithAlarm.ics')
        future = Calendar.findUID(self.repo.view, 'RecurringAlarmFuture')
        reminder = future.reminders.first()
        # this will start failing in 2015...
        self.assertEqual(reminder.delta, datetime.timedelta(minutes=-5))
        second = future.getNextOccurrence()
        self.assert_(reminder in second.reminders)

        past = Calendar.findUID(self.repo.view, 'RecurringAlarmPast')
        reminder = past.expiredReminders.first()
        self.assertEqual(reminder.delta, datetime.timedelta(hours=-1))
        second = past.getNextOccurrence()
        self.assert_(reminder in second.expiredReminders)

    def exportRecurrence(self):
        eastern = ICUtzinfo.getInstance("US/Eastern")
        start = datetime.datetime(2005,2,1, tzinfo = eastern)
        vevent = vobject.icalendar.RecurringComponent(name='VEVENT')
        vevent.behavior = vobject.icalendar.VEvent

        vevent.add('dtstart').value = start

        # not creating a RuleSetItem, although it would be required for an item
        ruleItem = RecurrenceRule(None, itsView=self.repo.view)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.repo.view)
        ruleSetItem.addRule(ruleItem)

        vevent.rruleset = ruleSetItem.createDateUtilFromRule(start)
        self.assertEqual(vevent.rrule.value, 'FREQ=DAILY')


        event = Calendar.CalendarEvent(itsView = self.repo.view)
        event.anyTime = False
        event.displayName = uw("blah")
        event.startTime = start
        event.endTime = datetime.datetime(2005,3,1,1, tzinfo = eastern)

        ruleItem = RecurrenceRule(None, itsView=self.repo.view)
        ruleItem.until = datetime.datetime(2005,3,1, tzinfo = eastern)
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.repo.view)
        ruleSetItem.addRule(ruleItem)
        event.rruleset = ruleSetItem

        vcalendar = ICalendar.itemsToVObject(self.repo.view, [event])

        self.assertEqual(vcalendar.vevent.dtstart.serialize(),
                         'DTSTART;TZID=US/Eastern:20050201T000000\r\n')
        vcalendar.vevent = vcalendar.vevent.transformFromNative()
        self.assertEqual(vcalendar.vevent.rrule.serialize(),
                         'RRULE:FREQ=WEEKLY;UNTIL=20050302T045900Z\r\n')

        # move the second occurrence one day later
        nextEvent = event.getNextOccurrence()
        nextEvent.changeThis('startTime',
                             datetime.datetime(2005,2,9,
                                               tzinfo=ICUtzinfo.floating))

        nextEvent.getNextOccurrence().deleteThis()

        vcalendar = ICalendar.itemsToVObject(self.repo.view, [event])
        modified = vcalendar.vevent_list[1]
        self.assertEqual(modified.dtstart.serialize(),
                         'DTSTART:20050209T000000\r\n')
        self.assertEqual(modified.recurrence_id.serialize(),
                         'RECURRENCE-ID;TZID=US/Eastern:20050208T000000\r\n')
        self.assertEqual(vcalendar.vevent.exdate.serialize(),
                         'EXDATE;TZID=US/Eastern:20050215T000000\r\n')
        vcalendar.behavior.generateImplicitParameters(vcalendar)
        self.assertEqual(vcalendar.vtimezone.tzid.value, "US/Eastern")






# test import/export unicode

class TimeZoneTestCase(unittest.TestCase):

    def getICalTzinfo(self, lines):
        fileobj = cStringIO.StringIO("\r\n".join(lines))
        parsed = tz.tzical(fileobj)

        return parsed.get()

    def runConversionTest(self, expectedZone, icalZone):
        dt = datetime.datetime(2004, 10, 11, 13, 22, 21, tzinfo=icalZone)
        convertedZone = ICalendar.convertToICUtzinfo(dt).tzinfo
        self.failUnless(isinstance(convertedZone, ICUtzinfo))
        self.failUnlessEqual(expectedZone, convertedZone)

        dt = datetime.datetime(2004, 4, 11, 13, 9, 56, tzinfo=icalZone)
        convertedZone = ICalendar.convertToICUtzinfo(dt).tzinfo
        self.failUnless(isinstance(convertedZone, ICUtzinfo))
        self.failUnlessEqual(expectedZone, convertedZone)

    def testVenezuela(self):
        zone = self.getICalTzinfo([
            "BEGIN:VTIMEZONE",
            "TZID:America/Caracas",
            "LAST-MODIFIED:20050817T235129Z",
            "BEGIN:STANDARD",
            "DTSTART:19321213T204552",
            "TZOFFSETTO:-0430",
            "TZOFFSETFROM:+0000",
            "TZNAME:VET",
            "END:STANDARD",
            "BEGIN:STANDARD",
            "DTSTART:19650101T000000",
            "TZOFFSETTO:-0400",
            "TZOFFSETFROM:-0430",
            "TZNAME:VET",
            "END:STANDARD",
            "END:VTIMEZONE"])

        self.runConversionTest(
            ICUtzinfo.getInstance("America/Caracas"),
            zone)

    def testAustralia(self):

        zone = self.getICalTzinfo([
            "BEGIN:VTIMEZONE",
            "TZID:Australia/Sydney",
            "LAST-MODIFIED:20050817T235129Z",
            "BEGIN:STANDARD",
            "DTSTART:20050326T160000",
            "TZOFFSETTO:+1000",
            "TZOFFSETFROM:+0000",
            "TZNAME:EST",
            "END:STANDARD",
            "BEGIN:DAYLIGHT",
            "DTSTART:20051030T020000",
            "TZOFFSETTO:+1100",
            "TZOFFSETFROM:+1000",
            "TZNAME:EST",
            "END:DAYLIGHT",
            "END:VTIMEZONE"])

        self.runConversionTest(
            ICUtzinfo.getInstance("Australia/Sydney"),
            zone)

    def testFrance(self):

        zone = self.getICalTzinfo([
            "BEGIN:VTIMEZONE",
            "TZID:Europe/Paris",
            "LAST-MODIFIED:20050817T235129Z",
            "BEGIN:DAYLIGHT",
            "DTSTART:20050327T010000",
            "TZOFFSETTO:+0200",
            "TZOFFSETFROM:+0000",
            "TZNAME:CEST",
            "END:DAYLIGHT",
            "BEGIN:STANDARD",
            "DTSTART:20051030T030000",
            "TZOFFSETTO:+0100",
            "TZOFFSETFROM:+0200",
            "TZNAME:CET",
            "END:STANDARD",
            "END:VTIMEZONE"])

        self.runConversionTest(
            ICUtzinfo.getInstance("Europe/Paris"),
            zone)

    def testUS(self):
        zone = self.getICalTzinfo([
            "BEGIN:VTIMEZONE",
            "TZID:US/Pacific",
            "LAST-MODIFIED:20050817T235129Z",
            "BEGIN:DAYLIGHT",
            "DTSTART:20050403T100000",
            "TZOFFSETTO:-0700",
            "TZOFFSETFROM:+0000",
            "TZNAME:PDT",
            "END:DAYLIGHT",
            "BEGIN:STANDARD",
            "DTSTART:20051030T020000",
            "TZOFFSETTO:-0800",
            "TZOFFSETFROM:-0700",
            "TZNAME:PST",
            "END:STANDARD",
            "END:VTIMEZONE"])
        self.runConversionTest(
            ICUtzinfo.getInstance("US/Pacific"),
            zone)

if __name__ == "__main__":
    unittest.main()
