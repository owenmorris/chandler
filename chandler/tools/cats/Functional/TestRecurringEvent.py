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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from i18n.tests import uw

class TestRecurringEvent(ChandlerTestCase):

    def startTest(self):
        # make user collection, since only user
        # collections can be displayed as a calendar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)

        # creation
        dailyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        # action
        dailyEvent.SetAttr(displayName=uw("Daily Exercise"),
                           startDate="01/01/2006",
                           startTime="6:00 AM",
                           location=uw("Gym"),
                           status="FYI",
                           body=uw("Resolution: exercise daily for optimal health"),
                           timeZone="US/Central",
                           recurrence="Daily",
                           recurrenceEnd="03/01/2006")
        
        # verification
        dailyEvent.Check_DetailView({"displayName":uw("Daily Exercise"),
                                     "startDate":"1/1/2006",
                                     "endDate":"1/1/2006",
                                     "startTime":"6:00 AM",
                                     "endTime":"7:00 AM",
                                     "location":uw("Gym"),
                                     "status":"FYI",
                                     "body":uw("Resolution: exercise daily for optimal health"),
                                     "timeZone":"US/Central",
                                     "recurrence":"Daily", 
                                     "recurrenceEnd":"3/1/2006"})
    
        dailyEvent.Check_Object({"displayName":uw("Daily Exercise"),
                                 "startDate":"1/1/2006",
                                 "endDate":"1/1/2006",
                                 "startTime":"6:00 AM",
                                 "endTime":"7:00 AM",
                                 "location":uw("Gym"),
                                 "status":"FYI",
                                 "body":uw("Resolution: exercise daily for optimal health"),
                                 "timeZone":"US/Central"})
    
        # Weekly Event Test
                                
        # creation
        weeklyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        # action
        weeklyEvent.SetAttr(displayName=uw("Weekly call home"),
                            startDate="01/07/2006",
                            startTime="5:00 PM",
                            location=uw("Phone"),
                            status="FYI",
                            body=uw("Resolution: call home weekly for good family relations"),
                            timeZone="US/Central",
                            recurrence="Weekly",
                            recurrenceEnd="03/25/2006")
    
        # verification
          
        weeklyEvent.Check_DetailView({"displayName":uw("Weekly call home"),
                                      "startDate":"1/7/2006",
                                      "endDate":"1/7/2006",
                                      "startTime":"5:00 PM",
                                      "endTime":"6:00 PM",
                                      "location":uw("Phone"),
                                      "status":"FYI",
                                      "body":uw("Resolution: call home weekly for good family relations"),
                                      "timeZone":"US/Central",
                                      "recurrence":"Weekly",
                                      "recurrenceEnd":"3/25/2006"})
    
        weeklyEvent.Check_Object({"displayName":uw("Weekly call home"),
                                  "startDate":"1/7/2006",
                                  "endDate":"1/7/2006",
                                  "startTime":"5:00 PM",
                                  "endTime":"6:00 PM",
                                  "location":uw("Phone"),
                                  "status":"FYI",
                                  "body":uw("Resolution: call home weekly for good family relations"),
                                  "timeZone":"US/Central"})
                                  
        # Monthly Event Test
                                
        # creation
        monthlyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        monthlyEvent.SetAttr(displayName=uw("Monthly book club"),
                            startDate="01/01/2006",
                            startTime="7:00 PM",
                            endTime="9:00 PM",
                            location=uw("My house"),
                            status="CONFIRMED",
                            body=uw("Resolution: host book club once a month"),
                            timeZone="US/Central",
                            recurrence="Monthly",
                            recurrenceEnd="12/31/2006")
                            
        # verification
         
        monthlyEvent.Check_DetailView({"displayName":uw("Monthly book club"),
                                     "startDate":"1/1/2006",
                                      "endDate":"1/1/2006",
                                      "startTime":"7:00 PM",
                                      "endTime":"9:00 PM",
                                      "location":uw("My house"),
                                      "status":"Confirmed",
                                      "body":uw("Resolution: host book club once a month"),
                                      "timeZone":"US/Central",
                                      "recurrence":"Monthly",
                                      "recurrenceEnd":"12/31/2006"})
    
        monthlyEvent.Check_Object({"displayName":uw("Monthly book club"),
                                  "startDate":"1/1/2006",
                                  "endDate":"1/1/2006",
                                  "startTime":"7:00 PM",
                                  "endTime":"9:00 PM",
                                  "location":uw("My house"),
                                  "status":"CONFIRMED",
                                  "body":uw("Resolution: host book club once a month"),
                                  "timeZone":"US/Central"})
                                  
       # Yearly Event Test
                                
        # creation
        yearlyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        yearlyEvent.SetAttr(displayName=uw("Yearly dentist appointment"),
                         startDate="02/06/2006",
                            startTime="10:00 AM",
                            location=uw("Downtown"),
                            status="CONFIRMED",
                            body=uw("Resolution: get teeth cleaned once a year"),
                            timeZone="US/Pacific",
                            recurrence="Yearly",
                            recurrenceEnd="02/07/2010")
                            
        # verification
          
        yearlyEvent.Check_DetailView({"displayName":uw("Yearly dentist appointment"),
                                      "startDate":"2/6/2006",
                                      "endDate":"2/6/2006",
                                      "startTime":"10:00 AM",
                                      "endTime":"11:00 AM",
                                      "location":uw("Downtown"),
                                      "status":"Confirmed",
                                      "body":uw("Resolution: get teeth cleaned once a year"),
                                      "timeZone":"US/Pacific",
                                      "recurrence":"Yearly",
                                      "recurrenceEnd":"2/7/2010"})
    
        yearlyEvent.Check_Object({"displayName":uw("Yearly dentist appointment"),
                                  "startDate":"2/6/2006",
                                  "endDate":"2/6/2006",
                                  "startTime":"10:00 AM",
                                  "endTime":"11:00 AM",
                                  "location":uw("Downtown"),
                                  "status":"CONFIRMED",
                                  "body":uw("Resolution: get teeth cleaned once a year"),
                                  "timeZone":"US/Pacific"})

                              


