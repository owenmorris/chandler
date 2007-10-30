#   Copyright (c) 2004-2007 Open Source Applications Foundation
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


__parcel__ = "osaf.framework.blocks"

import wx, os
from application import schema
from i18n import ChandlerMessageFactory as _
import Block as Block
from Styles import ColorStyle
from osaf.pim.structs import SizeType
from osaf.pim.types import LocalizableString

theApp = wx.GetApp()

overrides = []

def rebuildMenusAndToolBars (block):
    global overrides

    while not block.eventBoundary:
        block = block.parentBlock

    # blocksToSynchronize is the set of blocks that need are affected by changes to
    # overrides. It includes blocks that used to be overridden but now aren't
    blocksToSynchronize = set()
    for override in overrides:
        blocksToSynchronize.add (override.location)

    overrides = []
    for child in block.childBlocks:
        if (isinstance (child, BaseItem) and
            getattr (child, "operation", None) is not None):
            overrides.append (child)
            blocksToSynchronize.add (child.location)
    
    for blockName in blocksToSynchronize:
        blockToSynchronize = block.findBlockByName (blockName)
        if blockToSynchronize is not None:
            blockToSynchronize.widget.wxSynchronizeWidget()

class operationEnumType(schema.Enumeration):
    values = "None", "InsertAfter", "InsertBefore", "Replace", "Delete"

class BaseItem(Block.Block):
    title = schema.One(LocalizableString)
    helpString = schema.One(LocalizableString, defaultValue = u'')
    operation = schema.One(operationEnumType, defaultValue = 'None')
    location = schema.One(schema.Text, defaultValue = u'')
    itemLocation = schema.One(schema.Text, defaultValue = u'')
    event = schema.One(Block.BlockEvent, inverse = Block.BlockEvent.menuOrToolForEvent)

    schema.addClouds(
        copying = schema.Cloud(byRef = [event])
    )

class menuItemKindEnumType(schema.Enumeration):
      values = "Normal", "Separator", "Check", "Radio"

class MenuItem (BaseItem):
    menuItemKind = schema.One(menuItemKindEnumType, defaultValue = 'Normal')
    accel = schema.One(LocalizableString)
    icon = schema.One(schema.Text)
    toggleTitle = schema.One(LocalizableString)

    def instantiateWidget (self):
        kind = {"Normal": wx.ITEM_NORMAL,
                "Separator": wx.ID_SEPARATOR,
                "Check": wx.ITEM_CHECK,
                "Radio": wx.ITEM_RADIO} [self.menuItemKind]

        if kind == wx.ID_SEPARATOR:
            id = wx.ID_SEPARATOR
        else:
            id = self.getWidgetID()
        
        # if we don't give the MenuItem a label, i.e. test = " " widgets will use
        # the assume the id is for a stock menuItem and will fail
        return wxMenuItem (None, id = id,  text = " ", kind = kind)

class wxMenuItem (wx.MenuItem):
    def Destroy(self):
        Block.Block.wxOnDestroyWidget (self)
        # Remove the menu item from it's menu if it's in the menu
        menu = self.GetMenu()
        if menu is not None:
            # Items returned by wxPython say they take an extra argument, so
            # we'll just call the correct method directly
            wx.Menu.RemoveItem (menu, self)
        elif self.IsSubMenu():
            subMenu = self.GetSubMenu()
            # Remove the menu item from it's MenuBar if it's in the MenuBar
            menuBar = subMenu.GetMenuBar()
            if menuBar is not None:
                # Items returned by wxPython say they take an extra argument, so
                # we'll just call the correct method directly
                wx.MenuBar.RemoveItem (menuBar, subMenu)

        del self # Menus aren't wxWindows so they don't have Destroy

    def wxSynchronizeWidget(self):
        blockItem = self.blockItem
        subMenu = self.GetSubMenu()
        if subMenu is not None:
            subMenu.wxSynchronizeWidget()

        icon = getattr (blockItem, "icon", None)
        if icon != None:
            unCheckedBitmap = theApp.GetImage(icon)
            assert unCheckedBitmap is not None
            checkedBitmap = None
    
            # Mac already shows checkmarks next to menu
            if wx.Platform != '__WXMAC__':
                root, extension = os.path.splitext (icon)
                checkedBitmap = theApp.GetImage(root + "Checked" + extension)

            if checkedBitmap is None:
                checkedBitmap = unCheckedBitmap

            self.SetBitmaps(checkedBitmap, unCheckedBitmap)

        title = getattr (blockItem, "title", None)
        if title is not None:
            accel = getattr (blockItem, "accel", None)
            if accel != None:
                title = title + '\t' + accel
                
            self.SetText (title)
        self.SetHelp(blockItem.helpString)
        theApp.needsUpdateUI = True

class Menu (MenuItem):
    setAsMenuBarOnFrame = schema.One(schema.Boolean, defaultValue = False)

    def instantiateWidget (self):
        if self.setAsMenuBarOnFrame:
            return wxMenuBar()
        else:
            subMenu = wxMenu()
            subMenu.blockItem = self
            # if we don't give the MenuItem a label, i.e. test = " " widgets will use
            # the assume the id is for a stock menuItem and will fail
            return wxMenuItem (None, id = self.getWidgetID(), text = " ", subMenu = subMenu)

class wxBaseContainer(object):
    def GetNewItems (self):
        blockItem = self.blockItem
        newItems = []
        for childBlock in blockItem.childBlocks:
            widget = getattr (childBlock, "widget", None)
            if widget is None:
                childBlock.render()
                widget = childBlock.widget
            newItems.append (widget)
        
        for override in overrides:
            if override.location == blockItem.blockName:
                itemToOverride = blockItem.findBlockByName (override.itemLocation)
                assert itemToOverride is not None
                try:
                    index = newItems.index (itemToOverride.widget)
                except IndexError:
                    pass
                else:
                    operation = override.operation

                    if operation == "InsertAfter":
                        newItems.insert (index + 1, override.widget)

                    elif operation == "InsertBefore":
                        newItems.insert (index, override.widget)

                    elif operation == "Replace":
                        newItems.remove (index)
                        newItems.insert (index, override.widget)

                    elif operation == "Delete":
                        newItems.remove (index)
        return newItems

    def ItemsAreSame (self, old, new):
        if hasattr (old, "this"):
            old = long (old.this)
        if hasattr (new, "this"):
            new = long (new.this)

        return  old == new
    
    def wxSynchronizeWidget (self):
        def getNext (iterator):
            try:
                return iterator.next()
            except StopIteration:
                return None

        # update the sequence of items in the container. Handles
        # sequences of inserts or sequences of deletes optimally
        oldItems = self.GetOldItems()
        newItems = self.GetNewItems()
        insert = len(newItems) > len(oldItems)
        
        oldIterator = iter (oldItems)
        newIterator = iter (newItems)
        
        old = getNext (oldIterator)
        new = getNext (newIterator)
        
        position = 0
        changed = False
        while True:
            if self.ItemsAreSame (old, new):
                if old is None:
                    break
                old = getNext (oldIterator)
                new = getNext (newIterator)
                position += 1
            else:
                changed = True
                if insert:
                    self.InsertItem (position, new)
                    position += 1
                    new = getNext (newIterator)
                    if new is None:
                        insert = False
                else:
                    self.RemoveItem (position, old)
                    old = getNext (oldIterator)
                    if old is None:
                        insert = True

        return changed

class wxMenu (wxBaseContainer, wx.Menu):
    def wxSynchronizeWidget(self):
        changed = super (wxMenu, self).wxSynchronizeWidget()
        if changed:
            theApp.needsUpdateUI = True

    def GetOldItems (self):
        return self.GetMenuItems()

    def RemoveItem (self, position, menuItem):
        super (wxMenu, self).RemoveItem (menuItem)
    
    def InsertItem (self, position, item):
        super (wxMenu, self).InsertItem (position, item)

    def TextItemsAreSame(self, old, new):
        if new is None or isinstance(new, wx.MenuItem):
            return super(wxMenu, self).ItemsAreSame(old, new)
  
        if new == '__separator__':
            return old is not None and old.IsSeparator()
        else:
            return old is not None and old.GetText() == new
  

class wxMenuBar (wxBaseContainer, wx.MenuBar):
    def wxSynchronizeWidget(self):
        changed = super (wxMenuBar, self).wxSynchronizeWidget()
        if self.blockItem.setAsMenuBarOnFrame:
            self.blockItem.getFrame().SetMenuBar(self)

        if changed:
            theApp.needsUpdateUI = True

    def GetOldItems (self):
        items = []
        for index in xrange (self.GetMenuCount()):
            items.append (self.GetMenu (index).blockItem)
        return items

    def RemoveItem (self, position, menuItem):
        self.Remove (position)
    
    def InsertItem (self, position, menuItem):
        subMenu = menuItem.GetSubMenu()
        self.Insert (position, subMenu, menuItem.blockItem.title)
    
    def Destroy(self):
        """
        We need to override Destroy to remove the MenuBar from mainFrame.

        We don't need to call wxOnDestroyWidget since wxMenuBar is a
        subclass of wxWindow, which sends a EVT_WINDOW_DESTROY which
        ends up calling wxOnDestroyWidget for us.

        Overriding __del__ doesn't work here since calling SetMenuBar (None)
        when the menuBar is being destroyed causes the application to crash --
        probably because wxWidgets tries to access the MenuBar when it's
        almost already deleted. Overriding Destroy catches the menuBar
        before it's deleted instead of just before it's disposed.
        """
        self.blockItem.getFrame().SetMenuBar(None)
        super (wxMenuBar, self).Destroy()

class toolBarItemKindEnumType(schema.Enumeration):
    values = "Button", "Separator", "Radio", "QuickEntry"

class ToolBarItem(BaseItem):
    selected = schema.One(schema.Boolean, defaultValue = False)
    size = schema.One(SizeType, defaultValue = SizeType(0, 0))
    toggle = schema.One(schema.Boolean, defaultValue = False)
    bitmap = schema.One(schema.Text, defaultValue = "")
    disabledBitmap = schema.One(schema.Text, defaultValue = "")
    toolBarItemKind = schema.One(toolBarItemKindEnumType, defaultValue = "Button")

    text = schema.One(schema.Text) # optional text for the ToolBarItem, e.g. QuickEntry text
    lastText = schema.One(schema.Text) # optional lastText for the ToolBarItem, e.g. QuickEntry last command
    lastSearch = schema.One(schema.Text) # optional lastSearch for the ToolBarItem, e.g. QuickEntry last search

    def instantiateWidget (self):
        if self.toolBarItemKind == 'QuickEntry':
            control = wxQuickEntry (self.parentBlock.widget,
                                    self.getWidgetID(),
                                    style = wx.TE_PROCESS_ENTER)
            # Apparently on Macintosh the selection starts out random, which causes it to crash
            # when setting text because it trys to delete characters that don't exist
            control.SetSelection (0, 0)
            control.blockItem = self
            widget = wx.ToolBarToolWithControl (None, control)
            widget.__class__ = wxToolBarTool
        else:
            kind = wx.ITEM_NORMAL
            if self.toolBarItemKind == 'Separator':
                id = wx.ID_SEPARATOR
            else:
                id = self.getWidgetID()
                if self.toggle:
                    kind = wx.ITEM_CHECK
                elif self.toolBarItemKind == 'Radio':
                    kind = wx.ITEM_RADIO
    
            widget = wxToolBarTool(None, id = id, kind = kind)
        return widget

class wxToolBarTool (wx.ToolBarTool):
    def Destroy(self):
        Block.Block.wxOnDestroyWidget (self)

        # If we've got a control that also has a blockItem attribute we need
        # to delete it here otherwise wxOnDestroyWidget will get called
        # again,
        if self.IsControl():
            del self.GetControl().blockItem

        toolBar = self.GetToolBar()
        if toolBar is not None:
            toolBar.RemoveTool (self.GetId())

        del self

    def wxSynchronizeWidget(self):
        blockItem = self.blockItem

        title = getattr (blockItem, "title", None)
        if title is not None:
            self.SetLabel (title)
        self.SetShortHelp (blockItem.helpString)
        self.SetLongHelp (blockItem.helpString)
    
        if blockItem.toolBarItemKind == 'Radio':
            self.Toggle (blockItem.selected)
                
        bitmap = blockItem.bitmap
        if bitmap != "":
            self.SetNormalBitmap (theApp.GetImage (bitmap))

        bitmap = blockItem.disabledBitmap
        if bitmap != "":
            self.SetDisabledBitmap (theApp.GetImage (bitmap) )
        
        if self.IsControl():
            self.GetControl().wxSynchronizeWidget()

    def IsShown (self):
        # Since wx.ToolBarTools are not real widgets, they don't support IsShown,
        #  so we'll provide a stub for CPIA.
        return True

    def OnSetTextEvent (self, event):
        """
        wxToolBarItems don't properly handle setting the text of buttons, on
        updateUIEvents, so we'll handle it here.
        """
        blockItem = self.blockItem
        
        title = event.GetText()
        if title != blockItem.title:
            blockItem.title = title
            self.wxSynchronizeWidget()

    def SetToolBarItemBitmap(self, bitmapName):
        # Setting the bitmap of the block then calling wxSynchronizeWidget doesn't
        # work. This is because of a bug in wxWidgets where Realize doesn't update
        # the modified toolbar tool. So in the mean time we'll try use an alternate
        # approach -- DJA
        blockItem = self.blockItem

        if bitmapName != blockItem.bitmap:
            blockItem.bitmap = bitmapName

            toolBar = self.GetToolBar()
            id = self.GetId()
            toolBar.SetToolNormalBitmap (id, theApp.GetImage (bitmapName))
            self.wxSynchronizeWidget()

    def selectTool(self):
        """
        Persist state of ToolBarItems. Currently limited to radio buttons.
        """
        if self.GetKind() == wx.ITEM_RADIO:
            toolBar = self.GetToolBar()
            id = self.GetId()
            toolIndex = toolBar.GetToolPos (id)

            # Unselect all the items in the radio group before this ToolBarItem.
            index = toolIndex - 1
            while index >= 0 :
                tool = toolBar.GetTool (index)
                if not tool.IsButton() or tool.GetKind() != wx.ITEM_RADIO:
                    break
                # The tool returned by GetTool isn't our Python object with the blockItem attribute
                # so we'll have to look it up by it's Id.
                Block.Block.idToBlock[tool.GetId()].selected = False
                index -= 1

            #Select this ToolBarItem
            self.blockItem.selected = True
            toolBar.ToggleTool (id, True) # Untoggles other buttons in the radio group

            #Unselect all the items in the radio group after this ToolBarItem.
            index = toolIndex + 1
            toolsCount = toolBar.GetToolsCount()
            while index < toolsCount:
                tool = toolBar.GetTool (index)
                if not tool.IsButton() or tool.GetKind() != wx.ITEM_RADIO:
                    break
                # The tool returned by GetTool isn't our Python object with the blockItem attribute.
                Block.Block.idToBlock[tool.GetId()].selected = False
                index += 1
                
    def OnToolEvent (self, event):
        self.selectTool()
        event.Skip()

class wxQuickEntry (wx.SearchCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxQuickEntry, self).__init__ (*arguments, **keywords)
        self.ShowSearchButton(False)
        self.SetDescriptiveText(_(u'Create new items or type /Find to search'))
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelButton)
        self.Bind(wx.EVT_TEXT_ENTER, theApp.OnCommand)
        self.Bind(wx.EVT_TEXT, self.OnTextChange)

        # on some platforms the search widget is a composite control which
        # doesn't pass along key events to the parent, find the text widget
        text = self
        if text.GetChildren():
            text = text.GetChildren()[0]
        text.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnCancelButton (self, event):
        block = self.blockItem
        block.post (block.event, {"cancelClicked": True}, sender = block)

    def wxSynchronizeWidget(self):
        blockItem = self.blockItem
        self.SetSize ((blockItem.size.width, blockItem.size.height))
        value = blockItem.text
        self.ShowCancelButton (value != "")
        self.SetValue (value)

    def OnTextChange(self, event):
        text = self.GetValue()
        self.blockItem.text = text

        showCancelButton = text != ""        
        if self.IsCancelButtonVisible() and not showCancelButton:
            self.ShowCancelButton (False)
            # propagating a cancel causes status messages to disappear,
            # which makes it seem like they never appeared, so instead of
            # propagating a cancel event, just stop showing search.

            self.blockItem.findBlockByName("Sidebar").setShowSearch(False)
            self.SetFocus()
            
        self.ShowCancelButton(showCancelButton)
        

    def OnKeyDown(self, event):
        """Treat ESC as Cancel."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancelButton(event)
        else:
            event.Skip()
        
class ToolBar(Block.RectangularChild):

    colorStyle = schema.One(ColorStyle, defaultValue = None)
    toolSize = schema.One(SizeType)
    separatorWidth = schema.One(schema.Integer, defaultValue = 5)
    buttons3D = schema.One(schema.Boolean, defaultValue = False)
    buttonsLabeled = schema.One(schema.Boolean, defaultValue = False)
    schema.addClouds(
        copying = schema.Cloud(byRef=[colorStyle])
    )

    def instantiateWidget (self):
        style = wx.TB_HORIZONTAL | wx.TB_MAC_NATIVE_SELECT
        if self.buttons3D:
            style |= wx.TB_3DBUTTONS
        else:
            style |= wx.TB_FLAT
        if self.buttonsLabeled:
            style |= wx.TB_TEXT

        return wxToolBar(self.parentBlock.widget,
                         self.getWidgetID(),
                         style=style)

    def pressed (self, itemName):
        toolBarItem = self.findBlockByName (itemName).widget
        return self.widget.GetToolState (toolBarItem.GetId())

    def press (self, itemName):
        toolBarItem = self.findBlockByName (itemName)
        return self.post(toolBarItem.event, {}, toolBarItem)

class wxToolBar (wxBaseContainer, Block.BaseWidget, wx.ToolBar):

    def wxSynchronizeWidget(self):
        # A bug in windows wxWidgets causes the toolbar synchronizeWidget to incorrectly
        # layout a the toolbar controls when it's called before the top level size is
        # layed out, so we'll ignore calls to wxSynchronizeLayout until the top level
        # sizer is installed
        if wx.GetApp().mainFrame.GetSizer() is not None:
            blockItem = self.blockItem
    
            self.SetToolBitmapSize((blockItem.toolSize.width, blockItem.toolSize.height))
            self.SetToolSeparation(blockItem.separatorWidth)
    
            heightGutter = blockItem.buttonsLabeled and 23 or 6
            self.SetSize ((-1, blockItem.toolSize.height + heightGutter))
    
            colorStyle = blockItem.colorStyle
            if colorStyle is not None:
                self.SetBackgroundColour(colorStyle.backgroundColor.wxColor())
                self.SetForegroundColour(colorStyle.foregroundColor.wxColor())
    
            # Call BaseWidget's wxSynchronizeWidget since not all wxBaseContainers
            # have BaseWidget as a superclass.
            Block.BaseWidget.wxSynchronizeWidget(self)
            changed = super (wxToolBar, self).wxSynchronizeWidget()
    
            self.Realize()

    def GetOldItems (self):
        return self.GetTools()

    def RemoveItem (self, position, toolBarTool):
        id = toolBarTool.GetId()
        self.UnBind (wx.EVT_TOOL, id=id)
        self.RemoveTool (id)
    
    def InsertItem (self, position, toolBarTool):
        self.InsertToolItem (position, toolBarTool)
        self.Bind (wx.EVT_TOOL, toolBarTool.OnToolEvent, id=toolBarTool.GetId())

