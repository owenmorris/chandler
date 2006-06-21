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

import tools.QAUITestAppLib as QAUITestAppLib
from application import schema
from application.dialogs import RecurrenceDialog
import osaf.framework.scripting as scripting
import wx
from i18n.tests import uw

evtDate = "4/18/05"
evtSecondDate = "4/19/05"
evtThirdDate = "4/20/05"
evtRecurrenceEnd = "4/18/06"

#initialization
fileName = "TestNewEvent.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewEvent")

# Make sure we're not showing timezones now (we'll put it back below)
tzPrefs = schema.ns('osaf.app', QAUITestAppLib.App_ns.itsView).TimezonePrefs
oldTZPref = tzPrefs.showUI
tzPrefs.showUI = False

try:
    # Create a vanilla event; leave the timezone alone so we can make sure
    # it's floating.
    event = QAUITestAppLib.UITestItem("Event", logger)
    event.SetAttr(displayName=uw("Birthday Party"),
                  startDate=evtDate,
                  startTime="6:00 PM", 
                  location=uw("Club101"),
                  status="FYI",
                  body=uw("This is a birthday party invitation"))

    # Check a few things: that those attributes got set right, plus
    # a few defaulty things worked (timezone, endtime)
    event.CheckDisplayedValues("Checking initial setup",
        HeadlineBlock=(True, uw("Birthday Party")),
        EditAllDay=(True, False),
        EditCalendarStartDate=(True, evtDate),
        CalendarStartAtLabel=(True,),
        EditCalendarStartTime=(True, "6:00 PM"),
        EditCalendarEndDate=(True, evtDate),
        CalendarEndAtLabel=(True,),
        EditCalendarEndTime=(True, "7:00 PM"),
        CalendarLocation=(True, uw("Club101")),
        EditTransparency=(True, "FYI"),
        NotesBlock=(True, uw("This is a birthday party invitation")),
        EditTimeZone=(False, "Floating")) # Not visible with timezones off

    # Toggle allday, then make sure the right changes happened.
    event.SetAttr("Setting allDay", allDay=True)
    event.CheckDisplayedValues("Checking allday",
        HeadlineBlock=(True, uw("Birthday Party")),
        EditAllDay=(True, True),
        EditCalendarStartDate=(True, evtDate),
        CalendarStartAtLabel=(False,),
        EditCalendarStartTime=(False,),
        EditCalendarEndDate=(True, evtDate),
        CalendarEndAtLabel=(False,),
        EditCalendarEndTime=(False,),
        )

    # Turn on timezones, turn off alldayness, and make sure the popup appears
    tzPrefs.showUI = True
    event.SetAttr("Setting explicit timezone", 
              allDay=False,
              timeZone="US/Mountain")
    event.CheckDisplayedValues("Changed Timezone",
        HeadlineBlock=(True, uw("Birthday Party")),
        EditTimeZone=(True, "US/Mountain"),
        EditCalendarStartDate=(True, evtDate),
        EditCalendarEndDate=(True, evtDate),
        EditCalendarStartTime=(True,), # could check the time here if I knew the local tz
        EditCalendarEndTime=(True,),
        CalendarStartAtLabel=(True,),
        CalendarEndAtLabel=(True,)
        )

    # Make it recur
    event.SetAttr("Making it recur",
                  recurrence="Daily", 
                  recurrenceEnd=evtRecurrenceEnd)
    event.CheckDisplayedValues("Checking recurrence",
        EditRecurrence=(True, "Daily"),
        EditRecurrenceEnd=(True, evtRecurrenceEnd))

    # Select the second occurrence and delete it
    masterEvent = event.item
    secondEvent = QAUITestAppLib.UITestItem(masterEvent.getNextOccurrence())
    secondEvent.SelectItem()
    secondEvent.CheckDisplayedValues("Checking 2nd occurrence",
        EditCalendarStartDate=(True, evtSecondDate),
        )
    secondEvent.FocusInDetailView()
    QAUITestAppLib.App_ns.root.Delete()
    User.idle()

    # Answer the recurrence question with "just this item"
    recurrenceDialog = wx.FindWindowByName(u'RecurrenceDialog')
    if recurrenceDialog is None:
        logger.ReportFailure("Didn't see the recurrence dialog when deleting a recurrence instance")
    else:
        User.emulate_click(recurrenceDialog.thisButton)
        User.idle()

    # Make sure the new second occurrence starts on the right date
    thirdEvent = QAUITestAppLib.UITestItem(masterEvent.getNextOccurrence())
    thirdEvent.SelectItem()
    thirdEvent.CheckDisplayedValues("After deleting second occurrence",
        HeadlineBlock=(True, uw("Birthday Party")),
        EditCalendarStartDate=(True, evtThirdDate),
        )

finally:
    tzPrefs.showUI = oldTZPref
    logger.Close()
