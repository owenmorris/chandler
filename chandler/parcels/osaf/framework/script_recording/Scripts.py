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

import wx, logging, sys
from osaf.framework.blocks import Menu
from osaf.framework.blocks.MenusAndToolbars import wxMenu, wxMenuItem
from application import schema
import run_recorded
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

#determines whether to display a final prompt when running a script
displayTestResults = True
        
def runScript (name):
    if (not run_recorded.run_test_by_name (name, test_modules=run_recorded.get_test_modules ()) and
        schema.ns('osaf.framework.script_recording', wx.GetApp().UIRepositoryView).RecordingController.verifyScripts):
    
        #display the results of the script just ran to the user if "Check Results" is On
        testResults = unicode("".join(run_recorded.last_format_exception), "utf8", "ignore")
        wx.MessageBox(_(u"The script did not complete because a error was found during verification.\n\n%(testResults)s") % {'testResults': testResults},
                      _(u"Script Error"), wx.OK)


class wxScriptsMenu(wxMenu):
    
    def ItemsAreSame(self, old, new):
        return self.TextItemsAreSame(old, new)

    def GetNewItems(self):
                
        #create the newItems item
        newItems = super(wxMenu, self).GetNewItems()
        
        dynamicItems = sorted (run_recorded.get_test_modules())
        if dynamicItems: 
            newItems.append('__separator__')
            newItems.extend(dynamicItems)
  
        return newItems
  
    def InsertItem(self, position, item):
  
        if not isinstance(item, wx.MenuItem):
            if item == '__separator__':
                item = wx.MenuItem(self, id=wx.ID_SEPARATOR, kind=wx.ID_SEPARATOR)
            else:
                item = wx.MenuItem(self, id=self.blockItem.getWidgetID(), text=item, kind=wx.ITEM_NORMAL)
  
        super(wxMenu, self).InsertItem(position, item)
        
class ScriptsMenu(Menu):

    def instantiateWidget(self):

        menu = wxScriptsMenu()
        menu.blockItem = self
        
        # if we don't give the MenuItem a label, i.e. test = " " widgets
        # will use the assume the id is for a stock menuItem and will fail
        return wxMenuItem(None, id=self.getWidgetID(), text=" ", subMenu=menu)
    
    def onPlayableSriptsEvent(self, event):
        
        #retrieve the selected item's name so script can be ran
        subMenu = self.widget.GetSubMenu()
        menuItem = subMenu.FindItemById(event.arguments["wxEvent"].GetId())
        runScript (menuItem.GetText())

    def onPlayableSriptsEventUpdateUI(self, event):	
        
        self.synchronizeWidget()
        arguments = event.arguments
        menuItem = self.widget.GetSubMenu().FindItemById(arguments["wxEvent"].GetId())

        if isinstance(menuItem, wx.MenuItem):
            # Delete default text otherwise the incorrect menu text will be displayed
            del arguments['Text']

