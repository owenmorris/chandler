import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from datetime import datetime
from PyICU import ICUtzinfo
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfLargeDataSwitchTimezone(ChandlerTestCase):

    def startTest(self):

    
        calendarBlock = getattr(self.app_ns, "MainCalendarControl")
    
        # Enable timezones so that we can switch from the UI
        self.app_ns.root.EnableTimezones()
        
        # Start at the same date every time
        testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        # Load a large calendar
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
        self.app_ns.sidebar.select(testView.collection)
        self.scripting.User.idle()
    
        # Switch the timezone (this is the action we are measuring)
        self.logger.startAction("Switch timezone to US/Hawaii")
        QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, "US/Hawaii")
        self.scripting.User.idle()
        self.logger.endAction()
    
        # Verification
    
        # @@@ KCP this test could be improved
        # Currently tests that the default tz is now US/Hawaii
        self.logger.start("verify Timezone switched")
        if ICUtzinfo.default == ICUtzinfo.getInstance("US/Hawaii"):
            self.logger.endAction(True, "Timezone switched")
        else:
            self.logger.endAction(False, "Timezone failed to switch")
        
#import tools.cats.framework.ChandlerTestLib as QAUITestAppLib

#from datetime import datetime
#from PyICU import ICUtzinfo

#try:
    #self.app_ns = self.self.app_ns()
    #calendarBlock = getattr(self.app_ns, "MainCalendarControl")

    ## Enable timezones so that we can switch from the UI
    #self.app_ns.root.EnableTimezones()
    
    ## Start at the same date every time
    #testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    #self.app_ns.root.SelectedDateChanged(start=testdate)

    ## Load a large calendar
    #testView = QAUITestAppLib.UITestView(self.logger, "office.ics")#, u'Generated3000.ics')
    #self.app_ns.sidebar.select(testView.collection)
    #self.scripting.User.idle()

    ## Switch the timezone (this is the action we are measuring)
    #self.logger.startAction("Switch timezone to US/Hawaii")
    #QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, "US/Hawaii")
    #self.scripting.User.idle()
    #self.logger.endAction()

    ## Verification

    ## @@@ KCP this test could be improved
    ## Currently tests that the default tz is now US/Hawaii
    #self.logger.startAction("verify timezone changed to US/Hawaii")
    #if ICUtzinfo.default == ICUtzinfo.getInstance("US/Hawaii"):
        #self.logger.endAction(True, "Timezone switched")
    #else:
        #self.logger.endAction(False, "Timezone failed to switch")
    
    
