__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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
