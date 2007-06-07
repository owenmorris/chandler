import os, pkg_resources, wx, webbrowser, logging

from application import Utility, Globals, Parcel, schema
from osaf.framework.blocks import Menu
from osaf.framework.blocks.MenusAndToolbars import wxMenu, wxMenuItem
from osaf.framework.blocks.Block import Block
from repository.schema.Kind import Kind
from i18n import ChandlerMessageFactory as _
from tools.cats.framework import run_recorded

logger = logging.getLogger(__name__)

class wxScriptsMenu(wxMenu):

    def ItemsAreSame(self, old, new):

        if new is None or isinstance(new, wx.MenuItem):
            return super(wxScriptsMenu, self).ItemsAreSame(old, new)

        if new == '__separator__':
            return old is not None and old.IsSeparator()
        else:
            return old is not None and old.GetText() == new
    
    def GetNewItems(self):
        
        #open up the directory where script files exist
        files = run_recorded.get_test_modules(observe_exclusions=False)
        
        #create the newItems item
        newItems = super(wxScriptsMenu, self).GetNewItems()
        
        if files: 
            newItems.append('__separator__')
            newItems.extend(files)

        return newItems

    def InsertItem(self, position, item):

        if not isinstance(item, wx.MenuItem):
            if item == '__separator__':
                item = wx.MenuItem(self, id=wx.ID_SEPARATOR,
                                   kind=wx.ID_SEPARATOR)
            else:
                block = Block.findBlockByName("ScriptMenu")
                id = block.getWidgetID()
                item = wx.MenuItem(self, id=id, text=item, kind=wx.ITEM_NORMAL)

        super(wxScriptsMenu, self).InsertItem(position, item)
        
class ScriptsMenu(Menu):

    def instantiateWidget(self):

        menu = wxScriptsMenu()
        menu.blockItem = self
        
        # if we don't give the MenuItem a label, i.e. test = " " widgets
        # will use the assume the id is for a stock menuItem and will fail
        return wxMenuItem(None, id=self.getWidgetID(), text=" ", subMenu=menu)
    
    def onScriptaEvent(self, event):
        
        #grab the block representing the statusbar to clear it's text
        msg = ''
        statusBar = Block.findBlockByName('StatusBar')
        statusBar.setStatusMessage(msg)
        
        ##retrieve the selected item's name so script can be ran
        subMenu = self.widget.GetSubMenu()
        menuItem = subMenu.FindItemById(event.arguments["wxEvent"].GetId())
        name = menuItem.GetText()
        
        ##run the recorded script
        run_recorded.run_test_by_name(name, test_modules=run_recorded.get_test_modules(observe_exclusions=False))        
        
    def onScriptaEventUpdateUI(self, event):
        arguments = event.arguments
        widget = self.widget
        subMenu = widget.GetSubMenu()
        menuItem = subMenu.FindItemById(arguments["wxEvent"].GetId())

        if isinstance(menuItem, wx.MenuItem):
            # Delete default text since.
            del arguments['Text']