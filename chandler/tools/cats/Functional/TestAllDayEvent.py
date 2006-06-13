import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestAllDayEvent(ChandlerTestCase):

    def startTest(self):
        
        filename = "TestAllDayEvent.log"
        #print 'test3'
        #logger = QAUITestAppLib.QALogger(fileName,"TestAllDayEvent")
        #logger = TestLogger.TestOutput(logname=filename)
        #logger.startSuite('TestAllDayEvent')
        #logger.startTest('TestAllDayEvent')
        
        # creation
        event = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        event.SetAllDay(True)
        
        # verification
        event.Check_DetailView({"allDay":True})
        event.Check_Object({"allDay":True})
        
        #finally:
        #cleaning
