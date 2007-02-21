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

import osaf.pim as pim

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
                           timeZone="America/Chicago",
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
                                     "timeZone":"America/Chicago",
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
                                 "timeZone":"America/Chicago"})
    
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
                            timeZone="America/Chicago",
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
                                      "timeZone":"America/Chicago",
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
                                  "timeZone":"America/Chicago"})
                                  
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
                            timeZone="America/Chicago",
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
                                      "timeZone":"America/Chicago",
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
                                  "timeZone":"America/Chicago"})
        
            
       # Yearly Event Test
                                
        # creation
        yearlyEvent = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        yearlyEvent.SetAttr(displayName=uw("Yearly dentist appointment"),
                         startDate="02/06/2004",
                            startTime="10:00 AM",
                            location=uw("Downtown"),
                            status="CONFIRMED",
                            body=uw("Resolution: get teeth cleaned once a year"),
                            timeZone="America/Los_Angeles",
                            recurrence="Yearly",
                            recurrenceEnd="02/07/2050")
                            
        # verification
          
        yearlyEvent.Check_DetailView({"displayName":uw("Yearly dentist appointment"),
                                      "startDate":"2/6/2004",
                                      "endDate":"2/6/2004",
                                      "startTime":"10:00 AM",
                                      "endTime":"11:00 AM",
                                      "location":uw("Downtown"),
                                      "status":"Confirmed",
                                      "body":uw("Resolution: get teeth cleaned once a year"),
                                      "timeZone":"America/Los_Angeles",
                                      "recurrence":"Yearly",
                                      "recurrenceEnd":"2/7/2050"})
    
        yearlyEvent.Check_Object({"displayName":uw("Yearly dentist appointment"),
                                  "startDate":"2/6/2004",
                                  "endDate":"2/6/2004",
                                  "startTime":"10:00 AM",
                                  "endTime":"11:00 AM",
                                  "location":uw("Downtown"),
                                  "status":"CONFIRMED",
                                  "body":uw("Resolution: get teeth cleaned once a year"),
                                  "timeZone":"America/Los_Angeles"})

        # Test stamping of recurring events        
        # @@@ unstamping eventness on recurring events is hard to define
        
        # Test that the communication stamp applies to all
        
        yearlyEvent.StampAsMailMessage(True)
        self.logger.startAction("Check communication stamp applies to all occurrences")
        firstOccurrence = pim.EventStamp(yearlyEvent.item).getFirstOccurrence()
        secondOccurrence = firstOccurrence.getNextOccurrence()
        if not pim.has_stamp(secondOccurrence, pim.MailStamp):
            self.logger.endAction(False,
                            "The second occurrence didn't get the MailStamp")

        yearlyEvent.StampAsMailMessage(False)
        if pim.has_stamp(secondOccurrence, pim.MailStamp):
            self.logger.endAction(False,
                            "The second occurrence didn't lose the MailStamp")


        # switch to the table view, make sure there are appropriate triageStatus
        # modifications.  These tests will fail if run before Feb. 2006 or after
        # Feb. 2050.
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToAllView()
        dashboardBlock = self.app_ns.DashboardSummaryView
        
        def getTriageStatusDict(title):
            """
            Get a dictionary mapping triage status to lists of items with the
            given title.
            """
            dictionary=dict()
            for status in pim.TriageEnum.constants:
                dictionary[status] = []

            for item in dashboardBlock.contents:
                if item.displayName == title:
                    dictionary[item.triageStatus].append(item)

            return dictionary

        def checkDictNumbers(done, later, now):
            statuses = getTriageStatusDict(uw("Yearly dentist appointment"))
            if len(statuses[pim.TriageEnum.done]) != done:
                self.logger.endAction(False,
                                'Wrong number of Done items, %s instead of %s'
                                % (len(statuses[pim.TriageEnum.done]), done))
            elif len(statuses[pim.TriageEnum.later]) != later:
                self.logger.endAction(False,
                                'Wrong number of Later items, %s instead of %s'
                                % (len(statuses[pim.TriageEnum.later]), later))
            elif len(statuses[pim.TriageEnum.now]) != now:
                self.logger.endAction(False,
                                'Wrong number of Now items, %s instead of %s'
                                % (len(statuses[pim.TriageEnum.now]), now))
                

        self.logger.startAction("Check initial modification states.")
        checkDictNumbers(1, 1, 1)
        self.logger.endAction(True)

        statuses = getTriageStatusDict(uw("Yearly dentist appointment"))
        changing_item = statuses[pim.TriageEnum.done][0]        
        
        self.logger.startAction("Change a Done to Now.")
        # This isn't going through the UI, so changes don't need to be purged
        # moved the Done to Now, created a new Done
        changing_item.triageStatus = pim.TriageEnum.now
        checkDictNumbers(1, 1, 2)
        self.logger.endAction(True)

        self.logger.startAction("Change the now back to Done.")
        changing_item.triageStatus = pim.TriageEnum.done
        checkDictNumbers(1, 1, 1)
        self.logger.endAction(True)
