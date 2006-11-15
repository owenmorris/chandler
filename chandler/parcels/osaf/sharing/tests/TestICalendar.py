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

"""
A helper class which sets up and tears down dual RamDB repositories
"""

import unittest, os, sys
from util.testcase import SingleRepositoryTestCase
import repository.persistence.DBRepository as DBRepository
import repository.item.Item as Item
import application.Parcel as Parcel
from application import schema
from osaf import pim, sharing
import osaf.sharing.ICalendar as ICalendar
from osaf.pim import ListCollection, Remindable
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.TimeZone import convertToICUtzinfo
import datetime
import vobject
import cStringIO
from PyICU import ICUtzinfo
from dateutil import tz
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from i18n.tests import uw

class ICalendarTestCase(SingleRepositoryTestCase):

    def setUp(self):
        super(ICalendarTestCase, self).setUp()
        
        # create a sandbox root
        self.sandbox = Item.Item("sandbox", self.view, None)
        self.view.commit()

    def Import(self, view, filename):

        sharePath = os.path.join(os.getenv('CHANDLERHOME') or '.',
                                 'parcels', 'osaf', 'sharing', 'tests')

        #sharePath is stored as schema.Text so convert to unicode
        sharePath = unicode(sharePath, sys.getfilesystemencoding())

        sandbox = view.findPath("//sandbox")

        conduit = sharing.FileSystemConduit(itsParent=self.sandbox, sharePath=sharePath,
                                            shareName=filename)
        format = ICalendar.ICalendarFormat(itsParent=self.sandbox)
        self.share = sharing.Share(itsParent=self.sandbox, conduit=conduit,
                                   format=format)
        self.share.sync(modeOverride='get')
        return format

    def testSummaryAndDateTimeImported(self):
        format = self.Import(self.view, u'Chandler.ics')
        event = pim.EventStamp(Calendar.findUID(
                                    self.view,
                                   'BED962E5-6042-11D9-BE74-000A95BB2738'))
        self.assertEqual(event.summary, u'3 ho\u00FCr event',
                 u"SUMMARY of first VEVENT not imported correctly, displayName is %s"
                 % event.summary)
        evtime = datetime.datetime(2005,1,1, hour = 23, tzinfo = ICalendar.utc)
        self.assert_(event.startTime == evtime,
         "startTime not set properly, startTime is %s"
         % event.startTime)

    def testDateImportAsAllDay(self):
        format = self.Import(self.view, u'AllDay.ics')
        event = pim.EventStamp(Calendar.findUID(self.view, 'testAllDay'))
        self.failUnless(pim.has_stamp(event, pim.EventStamp))
        self.assert_(event.startTime ==
                     datetime.datetime(2005,1,1, tzinfo=ICUtzinfo.floating),
         "startTime not set properly for all day event, startTime is %s"
         % event.startTime)
        self.assert_(event.allDay == True,
         "allDay not set properly for all day event, allDay is %s"
         % event.allDay)

    def testExportFreeBusy(self):
        format = self.Import(self.view, u'AllDay.ics')
        collection = self.share.contents
        schema.ns('osaf.pim', self.view).mine.addSource(collection)

        start = datetime.datetime(2005,1,1, tzinfo=ICUtzinfo.floating)
        end = start + datetime.timedelta(2)

        cal = ICalendar.itemsToFreeBusy(self.view, start, end)
        self.assertEqual(cal.vfreebusy.freebusy.value[0][1], datetime.timedelta(1))

    def testItemsToVobject(self):
        """Tests itemsToVObject, which converts Chandler items to vobject."""
        event = Calendar.CalendarEvent(itsView = self.view)
        event.anyTime = False
        event.summary = uw("test")
        event.startTime = datetime.datetime(2010, 1, 1, 10,
                                            tzinfo=ICUtzinfo.default)
        event.endTime = datetime.datetime(2010, 1, 1, 11,
                                          tzinfo=ICUtzinfo.default)

        cal = ICalendar.itemsToVObject(self.view, [event])

        self.failUnlessEqual(cal.vevent.summary.value, uw("test"),
         u"summary not set properly, summary is %s"
         % cal.vevent.summary.value)

        start = event.startTime
        self.assert_(cal.vevent.dtstart.value == start,
         "dtstart not set properly, dtstart is %s"
         % cal.vevent.summary.value)

        event = Calendar.CalendarEvent(itsView = self.view)
        event.summary = uw("test2")
        event.startTime = datetime.datetime(2010, 1, 1, 
                                            tzinfo=ICUtzinfo.floating)
        event.allDay = True

        cal = ICalendar.itemsToVObject(self.view, [event])

        self.assert_(cal.vevent.dtstart.value == datetime.date(2010,1,1),
         u"dtstart for allDay event not set properly, dtstart is %s"
         % cal.vevent.summary.value)
         # test bug 3509, all day event duration is off by one

    def testWriteICalendarUnicodeBug3338(self):
        event = Calendar.CalendarEvent(itsView = self.view)
        event.summary = u"unicode \u0633\u0644\u0627\u0645"
        event.startTime = datetime.datetime(2010, 1, 1, 10,
                                            tzinfo=ICUtzinfo.default)
        event.endTime = datetime.datetime(2010, 1, 1, 11,
                                          tzinfo=ICUtzinfo.default)

        coll = ListCollection("testcollection", itsParent=self.sandbox)
        coll.add(event.itsItem)
        filename = u"unicode_export.ics"

        conduit = sharing.FileSystemConduit("conduit", sharePath=u".",
                            shareName=filename, itsView=self.view)
        format = ICalendar.ICalendarFormat("format", itsView=self.view)
        self.share = sharing.Share("share",contents=coll, conduit=conduit,
                                    format=format, itsView=self.view)
        if self.share.exists():
            self.share.destroy()
        self.share.create()
        self.share.sync(modeOverride='put')
        cal=vobject.readComponents(file(filename, 'rb')).next()
        self.assertEqual(cal.vevent.summary.value, event.summary)
        self.share.destroy()

    def testImportRecurrence(self):
        format = self.Import(self.view, u'Recurrence.ics')
        event = Calendar.findUID(self.view, '5B30A574-02A3-11DA-AA66-000A95DA3228')
        third = event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()
        self.assertEqual(third.summary, u'\u00FCChanged title')
        self.assertEqual(third.recurrenceID, datetime.datetime(2005, 8, 10, 
                                                    tzinfo=ICUtzinfo.floating))
        # while were at it, test bug 3509, all day event duration is off by one
        self.assertEqual(event.duration, datetime.timedelta(0))
        # make sure we imported the floating EXDATE
        event = Calendar.findUID(self.view, '07f3d6f0-4c04-11da-b671-0013ce40e90f')
        self.assertEqual(event.rruleset.exdates[0], datetime.datetime(2005, 12, 6, 12, 30,
                                                    tzinfo=ICUtzinfo.floating))

    def testImportRecurrenceWithTimezone(self):
        format = self.Import(self.view, u'RecurrenceWithTimezone.ics')
        event = Calendar.findUID(self.view, 'FF14A660-02A3-11DA-AA66-000A95DA3228')
        # THISANDFUTURE change creates a new event, so there's nothing in
        # event.modifications
        self.assertEqual(event.modifications, None)
        # Bug 6994, EXDATEs need to have ICU timezones, or they won't commit
        # (unless we're suffering from Bug 7023, in which case tzinfos are
        # changed silently, often to GMT, without raising an exception)
        self.assertEqual(event.rruleset.exdates[0].tzinfo,
                         ICUtzinfo.getInstance('US/Central'))
        

    def testImportUnusualTzid(self):
        format = self.Import(self.view, u'UnusualTzid.ics')
        event = pim.EventStamp(Calendar.findUID(
                                self.view,
                                '42583280-8164-11da-c77c-0011246e17f0'))
        self.assertEqual(event.startTime.tzinfo,
                         ICUtzinfo.getInstance('US/Mountain'))

    def testImportReminders(self):
        format = self.Import(self.view, u'RecurrenceWithAlarm.ics')
        future = Calendar.findUID(self.view, 'RecurringAlarmFuture')
        reminder = Remindable(future).getUserReminder()
        # this will start failing in 2015...
        self.assertEqual(reminder.delta, datetime.timedelta(minutes=-5))
        second = pim.EventStamp(future).getFirstOccurrence().getNextOccurrence()
        self.assert_(reminder in Remindable(second).reminders)

        past = Calendar.findUID(self.view, 'RecurringAlarmPast')
        reminder = Remindable(past).getUserReminder()
        self.assertEqual(reminder.delta, datetime.timedelta(hours=-1))
        second = pim.EventStamp(past).getFirstOccurrence().getNextOccurrence()
        self.assert_(reminder in Remindable(second).expiredReminders)

    def testImportAbsoluteReminder(self):
        format = self.Import(self.view, u'AbsoluteReminder.ics')
        event = Calendar.findUID(self.view, 'I-have-an-absolute-reminder')
        reminder = Remindable(event).getUserReminder()
        self.failUnless(reminder is not None, "No reminder was set")
        self.failUnlessEqual(reminder.absoluteTime,
                             datetime.datetime(2006, 9, 25, 8,
                                    tzinfo=ICUtzinfo.getInstance('US/Pacific')))


    def testExportRecurrence(self):
        eastern = ICUtzinfo.getInstance("US/Eastern")
        start = datetime.datetime(2005,2,1, tzinfo = eastern)
        vevent = vobject.icalendar.RecurringComponent(name='VEVENT')
        vevent.behavior = vobject.icalendar.VEvent

        vevent.add('dtstart').value = start

        # not creating a RuleSetItem, although it would be required for an item
        ruleItem = RecurrenceRule(None, itsView=self.view)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.view)
        ruleSetItem.addRule(ruleItem)

        vevent.rruleset = ruleSetItem.createDateUtilFromRule(start)
        self.assertEqual(vevent.rrule.value, 'FREQ=DAILY')


        event = Calendar.CalendarEvent(itsView = self.view)
        event.anyTime = False
        event.summary = uw("blah")
        event.startTime = start
        event.endTime = datetime.datetime(2005,3,1,1, tzinfo = eastern)

        ruleItem = RecurrenceRule(None, itsView=self.view)
        ruleItem.until = datetime.datetime(2005,3,1, tzinfo = eastern)
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.view)
        ruleSetItem.addRule(ruleItem)
        event.rruleset = ruleSetItem

        vcalendar = ICalendar.itemsToVObject(self.view, [event])

        self.assertEqual(vcalendar.vevent.dtstart.serialize(),
                         'DTSTART;TZID=US/Eastern:20050201T000000\r\n')
        vcalendar.vevent = vcalendar.vevent.transformFromNative()
        self.assertEqual(vcalendar.vevent.rrule.serialize(),
                         'RRULE:FREQ=WEEKLY;UNTIL=20050302T045900Z\r\n')

        # move the second occurrence one day later
        nextEvent = event.getFirstOccurrence().getNextOccurrence()
        nextEvent.changeThis(pim.EventStamp.startTime.name,
                             datetime.datetime(2005,2,9,
                                               tzinfo=ICUtzinfo.floating))

        nextEvent.getNextOccurrence().deleteThis()

        vcalendar = ICalendar.itemsToVObject(self.view, [event])
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
        convertedZone = convertToICUtzinfo(dt).tzinfo
        self.failUnless(isinstance(convertedZone, ICUtzinfo))
        self.failUnlessEqual(expectedZone, convertedZone)

        dt = datetime.datetime(2004, 4, 11, 13, 9, 56, tzinfo=icalZone)
        convertedZone = convertToICUtzinfo(dt).tzinfo
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

            
class ICalendarMergeTestCase(SingleRepositoryTestCase):
    ETAG = 0
    before = None
    after = None

    def setUp(self):
        super(ICalendarMergeTestCase, self).setUp()
        
        view = self.view

        # create a sandbox root
        self.sandbox = Item.Item("sandbox", view, None)
        
        collection = ListCollection("testCollection", self.sandbox,
                                    displayName=uw("Test Collection"))

        share = sharing.Share(itsView=view, contents=collection,
            conduit=sharing.InMemoryConduit(itsView=view,
                                            shareName=uw("viewmerging")),
            format=sharing.CalDAVFormat(itsView=view)
        )

        view.commit()
        
        self.shareUUID = share.itsUUID
        
    @property
    def collection(self):
        return self.share.contents
        
    @property
    def share(self):
        return self.view.findUUID(self.shareUUID)

    def _doSync(self, *icalendarLines):

        if not self.share.exists():
            self.share.create()

        # directly inject the data on the "server" ... i.e. the Conduit
        data = "\r\n".join(icalendarLines)
        self.share.conduit.inject('import.ics', data)

        # Now sync; it's as if icalendarLines were what was on the server
        self.share.sync()
        
        
    def testUpdateMod(self):
        # Test for one problem in bug 7019
        # Create the original ... (We could also use self._doSync here)
        startTime = datetime.datetime(2006, 4, 17, 13,
                                      tzinfo=ICUtzinfo.floating)
        
        rrule = RecurrenceRule(
            itsParent=self.sandbox,
            freq="weekly"
        )
        rruleset = RecurrenceRuleSet(
            itsParent=self.sandbox,
            rrules=[rrule]
        )
        event = pim.CalendarEvent(
            itsParent=self.sandbox,
            startTime=startTime,
            duration=datetime.timedelta(hours=1),
            summary=u'Meeting Weakly',
            allDay=False,
            anyTime=False,
            icalUID=u'9cf1f128-c416-11da-9051-000a95d7eed8',
        )
        
        event.rruleset = rruleset
        self.collection.add(event.itsItem)
        
        # Change the occurrence on September 4 to 4pm on the 6th
        recurrenceID = startTime.replace(month=9, day=4)
        newStartTime = recurrenceID.replace(day=6, hour=16)
        occurrence = event.getRecurrenceID(recurrenceID)
        occurrence.changeThis(pim.EventStamp.startTime.name, newStartTime)
        
        self.view.commit()
        
        # Now import the iCalendar
        self._doSync(
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//PYVOBJECT//NONSGML Version 1//EN",
            "BEGIN:VEVENT",
            "UID:9cf1f128-c416-11da-9051-000a95d7eed8",
            "DTSTART:20060417T130000",
            "DTEND:20060417T140000",
            "DESCRIPTION:\n",
            "RRULE:FREQ=WEEKLY",
            "SUMMARY:PPD meeting",
            "END:VEVENT",
            "BEGIN:VEVENT",
            "UID:9cf1f128-c416-11da-9051-000a95d7eed8",
            "RECURRENCE-ID:20060904T130000",
            "DTSTART:20060906T160000",
            "DTEND:20060906T170000",
            "DESCRIPTION:\\n",
            "SUMMARY:Meeting Weakly",
            "END:VEVENT",
            "BEGIN:VEVENT",
            "UID:9cf1f128-c416-11da-9051-000a95d7eed8",
            "RECURRENCE-ID:20061016T130000",
            "DTSTART:20061016T141500",
            "DTEND:20061016T151500",
            "DESCRIPTION:\n",
            "SUMMARY:Meeting Weakly",
            "END:VEVENT",
            "END:VCALENDAR"
        )

        sharedItem = self.collection.first()
        self.failUnless(pim.has_stamp(sharedItem, pim.EventStamp))
        
        sharedEvent = pim.EventStamp(sharedItem)
        self.failUnlessEqual(sharedEvent.startTime.replace(tzinfo=None),
                             datetime.datetime(2006, 4, 17, 13))
                             
        mods = list(sharedEvent.modifications)
        self.failUnlessEqual(len(mods), 2, "A modification was lost on import")
        
        eventMod = pim.EventStamp(mods[1])
        self.failUnlessEqual(eventMod.startTime.replace(tzinfo=None),
                             datetime.datetime(2006, 10, 16, 14, 15))
        self.failUnlessEqual(eventMod.recurrenceID.replace(tzinfo=None),
                             datetime.datetime(2006, 10, 16, 13))

    def testExcludeOccurrence(self):
        Calendar.ensureIndexed(self.collection)
    
        self._doSync(
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//PYVOBJECT//NONSGML Version 1//EN",
            "BEGIN:VEVENT",
            "UID:f60de354-5ef1-11db-ea01-f67872a529d1",
            "DTSTART:20061015T103000",
            "DTEND:20061015T113000",
            "DESCRIPTION:",
            "RRULE:FREQ=DAILY;UNTIL=20061112T235900",
            "SUMMARY:Daily",
            "END:VEVENT",
            "END:VCALENDAR"
       )

        self._doSync(
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//PYVOBJECT//NONSGML Version 1//EN",
            "BEGIN:VEVENT",
            "UID:f60de354-5ef1-11db-ea01-f67872a529d1",
            "DTSTART:20061015T103000",
            "DTEND:20061015T113000",
            "EXDATE:20061016T103000",
            "DESCRIPTION:",
            "RRULE:FREQ=DAILY;UNTIL=20061112T235900",
            "SUMMARY:Daily",
            "END:VEVENT",
            "END:VCALENDAR"
        )
        
        start = datetime.datetime(2006, 10, 14, 
                                  tzinfo=ICUtzinfo.floating)
        end = start + datetime.timedelta(days=7)
        events = list(Calendar.recurringEventsInRange(self.view, start, end,
                                                 filterColl=self.collection))
                                                  
        self.failUnlessEqual(len(events), 5)


if __name__ == "__main__":
    unittest.main()
