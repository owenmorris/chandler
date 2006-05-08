import tools.QAUITestAppLib as QAUITestAppLib
from application import schema

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
    event.SetAttr(displayName="Birthday Party", 
                  startDate="09/12/2004", 
                  startTime="6:00 PM", 
                  location="Club101", 
                  status="FYI",
                  body="This is a birthday party invitation")

    # Check a few things: that those attributes got set right, plus
    # a few defaulty things worked (timezone, endtime)
    event.CheckDisplayedValues(
        HeadlineBlock=(True, "Birthday Party"),
        EditAllDay=(True, False),
        EditCalendarStartDate=(True, "9/12/04"),
        CalendarStartAtLabel=(True,),
        EditCalendarStartTime=(True, "6:00 PM"),
        EditCalendarEndDate=(True, "9/12/04"),
        CalendarEndAtLabel=(True,),
        EditCalendarEndTime=(True, "7:00 PM"),
        CalendarLocation=(True, "Club101"),
        EditTransparency=(True, "FYI"),
        NotesBlock=(True, "This is a birthday party invitation"),
        EditTimeZone=(False, "Floating")) # Not visible with timezones off

    # Toggle allday, then make sure the right changes happened.
    event.SetAttr("Setting allDay", allDay=True)    
    event.CheckDisplayedValues(
        HeadlineBlock=(True, "Birthday Party"),
        EditAllDay=(True, True),
        EditCalendarStartDate=(True, "9/12/04"),
        CalendarStartAtLabel=(False,),
        EditCalendarStartTime=(False,),
        EditCalendarEndDate=(True, "9/12/04"),
        CalendarEndAtLabel=(False,),
        EditCalendarEndTime=(False,),
        )

    # Turn on timezones, turn off alldayness, and make sure the popup appears
    tzPrefs.showUI = True
    event.SetAttr("Setting explicit timezone", 
              allDay=False,
              timeZone="US/Mountain")
    event.CheckDisplayedValues(
        HeadlineBlock=(True, "Birthday Party"),
        EditTimeZone=(True, "US/Mountain"),
        EditCalendarStartDate=(True, "9/12/04"),
        EditCalendarEndDate=(True, "9/12/04"),
        EditCalendarStartTime=(True,), # could check the time here if I knew the local tz
        EditCalendarEndTime=(True,),
        CalendarStartAtLabel=(True,),
        CalendarEndAtLabel=(True,)
        )
    
finally:
    tzPrefs.showUI = oldTZPref
    logger.Close()
