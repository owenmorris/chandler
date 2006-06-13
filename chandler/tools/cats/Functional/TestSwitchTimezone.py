import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

from PyICU import ICUtzinfo

class TestSwitchTimezone(ChandlerTestCase):

    def startTest(self):
        
        originalTz = ICUtzinfo.default.tzid
        switchTz = "US/Hawaii"
    
        calendarBlock = getattr(self.app_ns, "MainCalendarControl")
    
        # Enable timezones so that we can switch from the UI
        self.app_ns.root.EnableTimezones()
    
        # Create a new event, which should inherit the default tz 
        timezoneEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        # Test that the new event has indeed inherited the default tz
        timezoneEvent.CheckDisplayedValues(EditTimeZone=(True, originalTz))
    
        # Change the timezone to US/Hawaii
        QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, switchTz)
    
        # Test that the event timezone hasn't changed
        timezoneEvent.CheckDisplayedValues(EditTimeZone=(True, originalTz))
    
        # Test that the default timezone has switched
        self.logger.startAction("Verify timezone switched")
        if ICUtzinfo.default == ICUtzinfo.getInstance(switchTz):
            self.logger.endAction(True, "Timezone switched")
        else:
            self.logger.endAction(False, "Timezone failed to switch")
    
        # @@@ More interesting tests could be added here
    
        # Switch back to original timezone
        QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, originalTz)
        

