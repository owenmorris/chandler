__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

import OSAF.framework.blocks.ContainerBlocks as ContainerBlocks

class DemoTabs(ContainerBlocks.TabbedContainer):
    def OnChooseTabEventUpdateUI(self, notification):
        notebook = Globals.association[self.itsUUID]
        selectedText = notebook.GetPageText(notebook.GetSelection())
        notification.data['Check'] = (selectedText == notification.event.choice)

    def OnAddTextEvent(self, notification):
        textBox = Globals.repository.find('//parcels/OSAF/views/demo/ButtonText')
        wxTextBox = Globals.association[textBox.itsUUID]
        wxTextBox.AppendText('Here is some text')
    
    def OnReloadTextEvent(self, notification):
        textBox = Globals.repository.find('//parcels/OSAF/views/demo/ButtonText')
        wxTextBox = Globals.association[textBox.itsUUID]
        wxTextBox.SetValue('')
