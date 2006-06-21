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

import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, sys
import osaf.pim as pim
from datetime import date
import osaf.framework.scripting as scripting

class TestRecurrenceImporting(ChandlerTestCase):

    def startTest(self):        

        path = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/DataFiles")
        # Upcast path to unicode since Sharing requires a unicode path
        path = unicode(path, sys.getfilesystemencoding())
        share = Sharing.OneTimeFileSystemShare(path, u'TestRecurrence.ics', ICalendar.ICalendarFormat, itsView=self.app_ns.itsView)
        
        self.logger.startAction('Importing TestRecurrence.ics')
        collection = share.get()
        self.app_ns.sidebarCollection.add(collection)
        scripting.User.idle()
        self.logger.endAction(True, "Importing calendar")
        
        def VerifyEventCreation(title):
            self.logger.startAction("Verify event titled %s exists" % title)
            testEvent = self.app_ns.item_named(pim.CalendarEvent, title)
            if testEvent is not None:
                self.logger.endAction(True, " '%s' exists" % title)
            else:
                self.logger.endAction(False, "'%s' not created" % title)
        
        scripting.User.idle()
        VerifyEventCreation("Yearly Never End")
        VerifyEventCreation("Monthly Meeting")
        VerifyEventCreation("Multi-All Day")
        VerifyEventCreation("All-day never end")
        
        # bug 5593, set an end date for the "Weekly Never End" event
        sidebar = self.app_ns.sidebar
        scripting.User.emulate_sidebarClick(sidebar, 'TestRecurrence')    
        
        view = QAUITestAppLib.UITestView(self.logger)
        view.GoToDate('05/01/2006')
        
        event = QAUITestAppLib.GetOccurrence('Weekly Never End', date(2006, 5, 1))    
        QAUITestAppLib.UITestItem(event, self.logger).SetAttr(recurrenceEnd="05/01/2006")
        
        # event has been deleted by changing recurrence, get a new one
        event = QAUITestAppLib.GetOccurrence('Weekly Never End', date(2006, 5, 1))    
        testItem = QAUITestAppLib.UITestItem(event, self.logger)
        testItem.SelectItem(catchException=True)
        
        # Make sure this occurrence exists and was able to be selected
        testItem.Check_ItemSelected()
        
