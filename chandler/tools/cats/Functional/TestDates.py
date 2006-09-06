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

class TestDates(ChandlerTestCase):

    def startTest(self):

        START_DATE = 0
        START_TIME = 1
        END_DATE   = 2
        END_TIME   = 3
        TIMEZONE   = 4
        
            # tests that need to be added:
            #     week to week transistions
            #     non-pacific time zones
            #     other locales
        
        dateValues = { 'us': [  # year end transistion
                              ('12/31/04', '11:30 PM', '1/1/05',   '12:30 AM', 'US/Central'),
                                # leap year (feb has 29 days)
                              ('2/28/04',  '11:30 PM', '2/29/04',  '12:30 AM', 'US/Central'),
                                # leap year (feb has 29 days)
                              ('2/29/04',  '11:30 PM', '3/1/04',   '12:30 AM', 'US/Central'),
                                # Daylight savings time start
                              ('4/2/06',   '1:00 AM',  '4/2/06',   '3:00 AM',  'US/Central'),
                                # Daylight savings time end
                              ('10/29/06', '2:00 AM',  '10/29/06', '1:00 AM',  'US/Central'),
                             ],
                     }
    
        # make user collection, since only user
        # collections can be displayed as a calendar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)

        # creation
        event = QAUITestAppLib.UITestItem("Event", self.logger)
    
        for locale in dateValues:
            testItems = dateValues[locale]
    
            for test in testItems:
                s = uw('%s %s :: %s %s :: %s' % test)
    
                event.SetAttr(displayName=uw("Test"),
                              startDate=test[START_DATE],
                              startTime=test[START_TIME],
                              body=s,
                              timeZone=test[TIMEZONE]
                             )
    
                event.Check_DetailView({"displayName": uw("Test"),
                                        "startDate":   test[START_DATE],
                                        "endDate":     test[END_DATE],
                                        "startTime":   test[START_TIME],
                                        "endTime":     test[END_TIME],
                                        "body":        s,
                                       })
    
