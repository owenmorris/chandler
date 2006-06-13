import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestRecurringEvent(ChandlerTestCase):

    def startTest(self):
        # creation
        dailyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        # action
        dailyEvent.SetAttr(displayName="Daily Exercise",
                           startDate="01/01/2006", 
                           startTime="6:00 AM", 
                           location="Gym", 
                           status="FYI",
                           body="Resolution: exercise daily for optimal health",
                           timeZone="US/Central", 
                           recurrence="Daily", 
                           recurrenceEnd="03/01/2006")
        
        # verification
        dailyEvent.Check_DetailView({"displayName":"Daily Exercise",
                                     "startDate":"1/1/06",
                                     "endDate":"1/1/06",
                                     "startTime":"6:00 AM",
                                     "endTime":"7:00 AM",
                                     "location":"Gym",
                                     "status":"FYI",
                                     "body":"Resolution: exercise daily for optimal health",
                                     "timeZone":"US/Central",
                                     "recurrence":"Daily", 
                                     "recurrenceEnd":"3/1/06"})
    
        dailyEvent.Check_Object({"displayName":"Daily Exercise",
                                 "startDate":"1/1/2006",
                                 "endDate":"1/1/2006",
                                 "startTime":"6:00 AM",
                                 "endTime":"7:00 AM",
                                 "location":"Gym",
                                 "status":"FYI",
                                 "body":"Resolution: exercise daily for optimal health",
                                 "timeZone":"US/Central"})
    
        # Weekly Event Test
                                
        # creation
        weeklyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        # action
        weeklyEvent.SetAttr(displayName="Weekly call home",
                            startDate="01/07/2006",
                            startTime="5:00 PM",
                            location="Phone",
                            status="FYI",
                            body="Resolution: call home weekly for good family relations",
                            timeZone="US/Central",
                            recurrence="Weekly",
                            recurrenceEnd="03/25/2006")
    
        # verification
          
        weeklyEvent.Check_DetailView({"displayName":"Weekly call home",
                                      "startDate":"1/7/06",
                                      "endDate":"1/7/06",
                                      "startTime":"5:00 PM",
                                      "endTime":"6:00 PM",
                                      "location":"Phone",
                                      "status":"FYI",
                                      "body":"Resolution: call home weekly for good family relations",
                                      "timeZone":"US/Central",
                                      "recurrence":"Weekly",
                                      "recurrenceEnd":"3/25/06"})
    
        weeklyEvent.Check_Object({"displayName":"Weekly call home",
                                  "startDate":"1/7/2006",
                                  "endDate":"1/7/2006",
                                  "startTime":"5:00 PM",
                                  "endTime":"6:00 PM",
                                  "location":"Phone",
                                  "status":"FYI",
                                  "body":"Resolution: call home weekly for good family relations",
                                  "timeZone":"US/Central"})
                                  
        # Monthly Event Test
                                
        # creation
        monthlyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        monthlyEvent.SetAttr(displayName="Monthly book club",
                            startDate="01/01/2006",
                            startTime="7:00 PM",
                            endTime="9:00 PM",
                            location="My house",
                            status="CONFIRMED",
                            body="Resolution: host book club once a month",
                            timeZone="US/Central",
                            recurrence="Monthly",
                            recurrenceEnd="12/31/2006")
                            
        # verification
          
        monthlyEvent.Check_DetailView({"displayName":"Monthly book club",
                                      "startDate":"1/1/06",
                                      "endDate":"1/1/06",
                                      "startTime":"7:00 PM",
                                      "endTime":"9:00 PM",
                                      "location":"My house",
                                      "status":"Confirmed",
                                      "body":"Resolution: host book club once a month",
                                      "timeZone":"US/Central",
                                      "recurrence":"Monthly",
                                      "recurrenceEnd":"12/31/06"})
    
        monthlyEvent.Check_Object({"displayName":"Monthly book club",
                                  "startDate":"1/1/2006",
                                  "endDate":"1/1/2006",
                                  "startTime":"7:00 PM",
                                  "endTime":"9:00 PM",
                                  "location":"My house",
                                  "status":"CONFIRMED",
                                  "body":"Resolution: host book club once a month",
                                  "timeZone":"US/Central"})
                                  
       # Yearly Event Test
                                
        # creation
        yearlyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        yearlyEvent.SetAttr(displayName="Yearly dentist appointment",
                            startDate="02/06/2006",
                            startTime="10:00 AM",
                            location="Downtown",
                            status="CONFIRMED",
                            body="Resolution: get teeth cleaned once a year",
                            timeZone="US/Pacific",
                            recurrence="Yearly",
                            recurrenceEnd="02/07/2010")
                            
        # verification
          
        yearlyEvent.Check_DetailView({"displayName":"Yearly dentist appointment",
                                      "startDate":"2/6/06",
                                      "endDate":"2/6/06",
                                      "startTime":"10:00 AM",
                                      "endTime":"11:00 AM",
                                      "location":"Downtown",
                                      "status":"Confirmed",
                                      "body":"Resolution: get teeth cleaned once a year",
                                      "timeZone":"US/Pacific",
                                      "recurrence":"Yearly",
                                      "recurrenceEnd":"2/7/10"})
    
        yearlyEvent.Check_Object({"displayName":"Yearly dentist appointment",
                                  "startDate":"2/6/2006",
                                  "endDate":"2/6/2006",
                                  "startTime":"10:00 AM",
                                  "endTime":"11:00 AM",
                                  "location":"Downtown",
                                  "status":"CONFIRMED",
                                  "body":"Resolution: get teeth cleaned once a year",
                                  "timeZone":"US/Pacific"})

                              


