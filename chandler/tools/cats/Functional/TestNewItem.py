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
    
class TestNewItem(ChandlerTestCase):

    def startTest(self):

        def switchAndCheck(buttonName, expectedClass):
    
            name = "TestNewItem(%s" % (buttonName,))
            self.logger.startAction(name)
        
            # Switch to the requested view...
            QAUITestAppLib.App_ns.appbar.press(name=buttonName)
            
            # ... idle() so the app can handle changes
            QAUITestAppLib.scripting.User.idle()
        
            # ... Create a new item (For some reason, calling
            # scripting.User.emulate_typing() didn't correctly
            # simulate a control/cmd-n here)
            QAUITestAppLib.App_ns.MainView.onNewItemEvent(
               QAUITestAppLib.App_ns.NewItemItem.event)
            
            # ... wait again so the app can refresh
            QAUITestAppLib.scripting.User.idle()
        
            # See what's in the detail view
            newItem = QAUITestAppLib.App_ns.DetailRoot.contents
        
            # Verify we got what we expected
            global START_ITEM
            if newItem is START_ITEM:
                self.logger.endAction(False, "Selection in detail view didn't change!")
            elif newItem.__class__ != expectedClass:
                self.logger.endAction(False, "Expected a %s, got %s" % (expectedClass, newItem))
            else:
                self.logger.endAction(True, "Created a %s" % (expectedClass))
        
        
        START_ITEM = QAUITestAppLib.App_ns.DetailRoot.contents
        
        switchAndCheck("ApplicationBarAllButton",
                       QAUITestAppLib.pim.notes.Note)
    
        switchAndCheck("ApplicationBarEventButton",
                       QAUITestAppLib.pim.calendar.CalendarEvent)
    
        switchAndCheck("ApplicationBarMailButton",
                       QAUITestAppLib.Mail.MailMessage)
    
        switchAndCheck("ApplicationBarTaskButton",
                       QAUITestAppLib.pim.Task)
    
   

