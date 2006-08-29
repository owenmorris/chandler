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
    
            name = "TestNewItem(%s)" % (buttonName,)
            self.logger.startAction(name)
        
            # Switch to the requested view...
            self.app_ns.appbar.press(name=buttonName)
            
            # ... idle() so the app can handle changes
            self.scripting.User.idle()
        
            # ... Create a new item, by simulating cmd-n
            self.scripting.User.emulate_menu_accelerator("n")
            
            # ... wait again so the app can refresh
            self.scripting.User.idle()
        
            # See what's in the detail view
            newItem = self.app_ns.DetailRoot.contents
        
            # Verify we got what we expected
            if newItem is self.selectedItem:
                self.logger.endAction(False, "Selection in detail view didn't change!")
            elif newItem.__class__ != expectedClass:
                self.logger.endAction(False, "Expected a %s, got %s" % (expectedClass, newItem))
            else:
                self.logger.endAction(True, "Created a %s" % (expectedClass))
        
        
        self.selectedItem = self.app_ns.DetailRoot.contents
        
        switchAndCheck("ApplicationBarAllButton",
                       QAUITestAppLib.pim.notes.Note)        
        self.selectedItem = self.app_ns.DetailRoot.contents
    
        switchAndCheck("ApplicationBarEventButton",
                       QAUITestAppLib.pim.calendar.CalendarEvent)        
        self.selectedItem = self.app_ns.DetailRoot.contents
    
        switchAndCheck("ApplicationBarMailButton",
                       QAUITestAppLib.Mail.MailMessage)        
        self.selectedItem = self.app_ns.DetailRoot.contents
    
        switchAndCheck("ApplicationBarTaskButton",
                       QAUITestAppLib.pim.Task) 
    
   

