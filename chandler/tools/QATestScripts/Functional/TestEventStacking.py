"""
Tests for errors when numerious events try to occupy the same time/ date space
"""
import tools.QAUITestAppLib as QAUITestAppLib
from time import localtime
from time import strftime

today = strftime('%m/%d/%y',localtime())

#initialization
fileName = "TestEventStacking.log"
logger = QAUITestAppLib.QALogger(fileName, "TestEventStacking")

try:
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