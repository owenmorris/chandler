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
import osaf.framework.scripting as scripting
from i18n.tests import uw
import wx

from time import strftime, localtime

class TestMoveToTrash(ChandlerTestCase):
    
    def startTest(self):
    
        # creation
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        # actions
        note.SetAttr(displayName=uw("A note to move to Trash"), body=uw("TO MOVE TO TRASH"))
        
        # Work around nasty bug in QAUITestAppLib caused by not propagating notificatons correctly
        wx.GetApp().propagateAsynchronousNotifications()
        wx.SafeYield(None, True)

        note.MoveToTrash()
        # verification
        note.Check_ItemInCollection("Trash")
        note.Check_ItemInCollection("Dashboard", expectedResult=False)
        
        today = strftime('%m/%d/%Y',localtime())
    
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToCalView()
        view.GoToToday()
    
        sidebar = QAUITestAppLib.App_ns.sidebar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        col.SetDisplayName(uw("Trash testing"))
        scripting.User.emulate_sidebarClick(sidebar, uw('Trash testing'))
    
    
        event = QAUITestAppLib.UITestItem("Event", self.logger)
    
        event.SetAttr(startDate=today, startTime="12:00 PM",
                      displayName=uw("Ephemeral event"))
        
        event.SelectItem()
        event.Check_ItemInCollection("Dashboard", expectedResult=True)
        event.Check_ItemSelected()
        
        event.MoveToTrash()
        
        # This is perhaps not necessary for the test, but it used to
        # be here. It cannot be enabled until bug XXX is fixed.
        #scripting.User.emulate_sidebarClick(sidebar, 'Dashboard')
    
        event.SelectItem(catchException=True)
        event.Check_ItemInCollection("Trash")
        event.Check_ItemInCollection("Dashboard", expectedResult=False)
        event.Check_ItemSelected(expectedResult=False)
        
