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


import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
import osaf.framework.blocks.MenusAndToolbars as MenusAndToolbars

class DemoTabs(ContainerBlocks.TabbedContainer):
    def onChoiceEventUpdateUI(self, event):
        selectedText = self.widget.GetPageText (self.widget.GetSelection())
        event.arguments['Check'] = (selectedText == event.choice)

    def onAddTextEvent(self, event):
        textBox = self.findPath('//parcels/osaf/views/demo/ButtonText')
        textBox.widget.AppendText('Here is some text')
    
    def onReloadTextEvent(self, event):
        textBox = self.findPath('//parcels/osaf/views/demo/ButtonText')
        textBox.widget.SetValue('')

class DemoToolbarItem (MenusAndToolbars.ToolbarItem):
    """
      Demo for a ToolbarItem that handles its own clicks.
    """
    def onCycleTabsEvent (self, event):
        # just move the tab selection to the next tab
        tabset = self.findPath ('//parcels/osaf/views/demo/Tabs')
        tabWidget = tabset.widget
        selection = tabWidget.GetSelection ()
        selection += 1
        if selection == tabWidget.GetPageCount():
            selection = 0
        tabWidget.SetSelection (selection)
