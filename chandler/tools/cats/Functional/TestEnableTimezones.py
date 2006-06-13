import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestEnableTimezones(ChandlerTestCase):
 
    def startTest(self):
         
        def testEnabled(event, calendarBlock):
            # Test that the detail view does display the timezone
            event.CheckDisplayedValues(EditTimeZone=(True, 'Floating'))
        
            # Test that the calendar view does display the timezone widget
            self.logger.startAction("Test that the calendar view does display the timezone widget")
            if calendarBlock.widget.tzChoice.IsShown():
                self.logger.endAction(True, "Timezone widget found when timezones enabled")
            else:
                self.logger.endAction(False, "Timezone widget not found even though timezones are enabled")
        
        def testDisabled(event, calendarBlock):
            # Test that the detail view does not display the timezone
            self.logger.startAction("Test that the detail view does not display the timezone")
            event.CheckDisplayedValues(EditTimeZone=(False, 'Floating'))
        
            # Test that the calendar view does not displays the timezone widget
            if calendarBlock.widget.tzChoice.IsShown():
                self.logger.endAction(False, "Timezone widget shown incorrectly when timezones not enabled")
            else:
                self.logger.endAction(True, "Timezone widget correctly not shown when timezones not enabled")
        
        
        
        calendarBlock = getattr(self.app_ns, "MainCalendarControl")

        # Before timezones are enabled, create an event
        floatingEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        testDisabled(floatingEvent, calendarBlock)
            
        # Enable timezones
        self.app_ns.root.EnableTimezones()
    
        testEnabled(floatingEvent, calendarBlock)
    
        # Disable timezones again
        self.app_ns.root.EnableTimezones()
    
        testDisabled(floatingEvent, calendarBlock)
    

