__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
import osaf.framework.blocks.DynamicContainerBlocks as DynamicContainerBlocks

class DemoTabs(ContainerBlocks.TabbedContainer):
    def onChoiceEventUpdateUI(self, notification):
        selectedText = self.widget.GetPageText (self.widget.GetSelection())
        notification.data['Check'] = (selectedText == notification.event.choice)

    def onAddTextEvent(self, notification):
        textBox = Globals.repository.findPath('//parcels/osaf/views/demo/ButtonText')
        textBox.widget.AppendText('Here is some text')
    
    def onReloadTextEvent(self, notification):
        textBox = Globals.repository.findPath('//parcels/osaf/views/demo/ButtonText')
        textBox.widget.SetValue('')

class DemoToolbarItem (DynamicContainerBlocks.ToolbarItem):
    """
      Demo for a ToolbarItem that handles its own clicks.
    """
    def onCycleTabsEvent (self, notification):
        # just move the tab selection to the next tab
        tabset = Globals.repository.findPath ('//parcels/osaf/views/demo/Tabs')
        tabWidget = tabset.widget
        selection = tabWidget.GetSelection ()
        selection += 1
        if selection == tabWidget.GetPageCount():
            selection = 0
        tabWidget.SetSelection (selection)
