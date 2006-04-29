"""
Tests for errors when numerious events try to occupy the same time/ date space
"""
import tools.QAUITestAppLib as QAUITestAppLib
from time import localtime
from time import strftime

App_ns = app_ns()
today = strftime('%m/%d/%y',localtime())

#initialization
fileName = "TestEventStacking.log"
logger = QAUITestAppLib.QALogger(fileName, "TestEventStacking")

try:
    #Make sure we are in calendar view
    view = QAUITestAppLib.UITestView(logger)
    view.SwitchToCalView()
    
    #Create a collection and select it
    collection = QAUITestAppLib.UITestItem("Collection", logger)
    collection.SetDisplayName("stacked")
    sidebar = App_ns.sidebar
    QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, "stacked")
    
    #make sure we are on current week
    view.GoToDate(strftime('%Y-%m-%d',localtime()))
    
    # creation
    for i in range(16):
        eventName = 'Stacked Event %d' % i
        event = QAUITestAppLib.UITestItem("Event", logger)
        
        #action
        event.SetAttr(displayName=eventName, startDate=today, startTime="12:00 PM", body="Stacked event test")
        
        #verification
        event.Check_DetailView({"displayName":eventName,"startDate":today,"endDate":today,"startTime":"12:00 PM","body":"Stacked event test"})

finally:
    #cleaning
    logger.Close()