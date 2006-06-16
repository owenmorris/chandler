"""
Tests for errors when numerious events try to occupy the same time/ date space
"""
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from time import localtime
from time import strftime
from i18n.tests import uw

class TestEventStacking(ChandlerTestCase):

    def startTest(self):
        
        today = strftime('%m/%d/%y',localtime())
    
        #Make sure we are in calendar view
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToCalView()
        
        #Create a collection and select it
        collection = QAUITestAppLib.UITestItem("Collection", self.logger)
        collection.SetDisplayName(uw("stacked"))
        sidebar = self.app_ns.sidebar
        QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, uw("stacked"))
        
        #make sure we are on current week
        view.GoToToday()
        
        # creation
        for i in range(10):
            eventName = uw('Stacked Event %d' % i)
            event = QAUITestAppLib.UITestItem("Event", self.logger)
            
            #action
            event.SetAttr(displayName=eventName, startDate=today, startTime="12:00 PM", body=uw("Stacked event test"))
            
            #verification
            event.Check_DetailView({"displayName":eventName,"startDate":today,"endDate":today,"startTime":"12:00 PM","body":uw("Stacked event test")})
        
