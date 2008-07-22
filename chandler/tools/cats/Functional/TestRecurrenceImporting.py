#   Copyright (c) 2003-2008 Open Source Applications Foundation
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
import os, sys
import wx
from osaf import pim, sharing
import datetime
import osaf.framework.scripting as scripting
import application.Globals as Globals

class TestRecurrenceImporting(ChandlerTestCase):

    def startTest(self):
        
        QAUITestAppLib.startTestInCalView(self.logger)
        path = os.path.join(Globals.chandlerDirectory, "tools/cats/DataFiles",
            "TestRecurrence.ics")
        # Upcast path to unicode since Sharing requires a unicode path
        path = unicode(path, sys.getfilesystemencoding())
        self.logger.startAction('Importing TestRecurrence.ics')
        collection = sharing.importFile(self.app_ns.itsView, path)
        self.app_ns.sidebarCollection.add(collection)
        
        # select the collection
        sidebar = self.app_ns.sidebar
        QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, collection.displayName)
        scripting.User.idle()
        
        self.logger.endAction(True, "Importing calendar")
        
        def VerifyEventCreation(title):
            self.logger.startAction("Verify event titled %s exists" % title)
            testEvent = self.app_ns.item_named(pim.EventStamp, title)
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

        # Need to format date the same way the detail view does
        uiView = wx.GetApp().UIRepositoryView        
        goto = datetime.date(2006, 5, 1)
        value = datetime.datetime.combine(goto, datetime.time(0, tzinfo=uiView.tzinfo.default))
        dateStr = pim.shortDateFormat.format(uiView, value)
        
        view.GoToDate(dateStr)
        
        event = QAUITestAppLib.GetOccurrence('Weekly Never End', goto)    
        QAUITestAppLib.UITestItem(event, self.logger).SetAttr(recurrenceEnd=dateStr)
        
        # event has been deleted by changing recurrence, get a new one
        event = QAUITestAppLib.GetOccurrence('Weekly Never End', goto)    
        testItem = QAUITestAppLib.UITestItem(event, self.logger)
        testItem.SelectItem(catchException=True)
        
        # Make sure this occurrence exists and was able to be selected
        testItem.Check_ItemSelected()
        
