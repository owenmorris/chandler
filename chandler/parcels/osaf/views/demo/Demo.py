__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks

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
