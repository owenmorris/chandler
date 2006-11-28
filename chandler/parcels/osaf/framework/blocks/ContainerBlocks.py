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


__parcel__ = "osaf.framework.blocks"

from Block import (
    Block, RectangularChild, wxRectangularChild, debugName,
    WithoutSynchronizeWidget, IgnoreSynchronizeWidget
)
from osaf.pim.structs import PositionType, SizeType
import DragAndDrop
from MenusAndToolbars import Toolbar as Toolbar
from repository.item.Item import Item
from application import schema
import wx
import time
import util.autolog

class orientationEnumType(schema.Enumeration):
    values = "Horizontal", "Vertical"

class wxBoxContainer (wxRectangularChild):
    #import util.autolog; __metaclass__ = util.autolog.LogTheMethods; logMatch = "^On.*"
    def wxSynchronizeWidget(self, useHints=False):
        super (wxBoxContainer, self).wxSynchronizeWidget ()

        colorStyle = getattr (self, 'colorStyle', None)
        if colorStyle is not None:
            self.SetBackgroundColour(colorStyle.backgroundColor.wxColor())
            self.SetForegroundColour(colorStyle.foregroundColor.wxColor())

        sizer = self.GetSizer()
        if not sizer:
            sizer = wx.BoxSizer ({'Horizontal': wx.HORIZONTAL,
                                'Vertical': wx.VERTICAL} [self.blockItem.orientationEnum])
            self.SetSizer (sizer)
        sizer.Clear()
        for childBlock in self.blockItem.childrenBlocks:
            if isinstance (childBlock, RectangularChild):
                assert childBlock.widget, "Trying to add an unrendered block of type %s to the current block" % childBlock.blockName
                sizer.Add (childBlock.widget,
                           childBlock.stretchFactor, 
                           wxRectangularChild.CalculateWXFlag(childBlock), 
                           wxRectangularChild.CalculateWXBorder(childBlock))
        sizer.Layout()
        IgnoreSynchronizeWidget(False, self.Layout)

    @classmethod
    def CalculateWXStyle(theClass, block):
        style = wx.TAB_TRAVERSAL
        if Block.showBorders:
            style |= wx.SIMPLE_BORDER
        else:
            style |= wx.NO_BORDER
        return style


class BoxContainer(RectangularChild):

    orientationEnum = schema.One(
        orientationEnumType, initialValue = 'Horizontal',
    )
    bufferedDraw = schema.One(schema.Boolean, defaultValue=False)

    def instantiateWidget (self):
        widget = wxBoxContainer (self.parentBlock.widget,
                                 self.getWidgetID(),
                                 wx.DefaultPosition,
                                 wx.DefaultSize,
                                 style=wxBoxContainer.CalculateWXStyle(self))
        if self.bufferedDraw:
            widget.SetExtraStyle (wx.WS_EX_BUFFERED_DRAW)
        return widget

    
class wxLayoutChooser(wxBoxContainer):
    def __init__(self, *arguments, **keywords):
        super (wxLayoutChooser, self).__init__ (*arguments, **keywords)
            
    def wxSynchronizeWidget(self, useHints=False):
        selectedChoice = self._getSelectedChoice()
        if selectedChoice != self.blockItem.selection:
            for childBlock in self.blockItem.childrenBlocks:
                if not isinstance(childBlock, Toolbar):
                    childBlock.parentBlock = None
                    if hasattr(childBlock, 'widget'):
                        childBlock.widget.Destroy()
            super(wxLayoutChooser, self).wxSynchronizeWidget()

            try: # @@@ Until all the views have the necessary choices
                choice = self.blockItem.choices[selectedChoice]
            except IndexError:
                choice = self.blockItem.choices[0]
            self.blockItem.selection = selectedChoice
            sizer = self.GetSizer()
            choice.parentBlock = self.blockItem
            choice.render()
            sizer.Add(choice.widget,
                      choice.stretchFactor,
                      wxRectangularChild.CalculateWXFlag(choice),
                      wxRectangularChild.CalculateWXBorder(choice))
            self.Layout()    

    def setSelectedChoice(self, selectedIndex):
        index = 0
        for childBlock in self.blockItem.childrenBlocks:
            if isinstance(childBlock, Toolbar):
                for toolbarItem in childBlock.widget.toolItemList:
                    toolbarItemId = toolbarItem.widget.GetId()
                    if index == selectedIndex:
                        if not childBlock.widget.GetToolState(toolbarItemId):                                
                            childBlock.widget.ToggleTool(toolbarItemId, True)                            
                    else:
                        if childBlock.widget.GetToolState(toolbarItemId):
                            childBlock.widget.ToggleTool(toolbarItemId, False)
                    index += 1
                                        
    def _getSelectedChoice(self):
        index = 0
        for childBlock in self.blockItem.childrenBlocks:
            if isinstance(childBlock, Toolbar):
                for toolbarItem in childBlock.widget.toolItemList:
                    if childBlock.widget.GetToolState(toolbarItem.widget.GetId()):
                        return index
                    index += 1
        # @@@ On the Mac, the radio buttons are not given a default selection.
        # This is a bug in wxWidgets that should be fixed.
        return 0
            
    def getIdPos(self, id):
        index = 0
        for childBlock in self.blockItem.childrenBlocks:
            if isinstance(childBlock, Toolbar):
                for toolbarItem in childBlock.widget.toolItemList:
                    if id == toolbarItem.widget.GetId():
                        return index
                    index += 1
        return LayoutChooser.NONE_SELECTED
    

class LayoutChooser(BoxContainer):

    choices = schema.Sequence(Block)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[choices])
    )

    NONE_SELECTED = -1
    
    def instantiateWidget (self):
        self.selection = LayoutChooser.NONE_SELECTED

        parentWidget = self.parentBlock.widget 
        return wxLayoutChooser(parentWidget, self.getWidgetID())

    def changeSelection(self, selectionIndex):
        self.widget.setSelectedChoice(selectionIndex)
        self.synchronizeWidget()

    def onChangeLayoutEvent(self, event):
        # @@@ On the Mac, radio buttons do not work as radio
        # buttons, but rather they behave as individual toggle
        # buttons.  As a workaround, we deselect the other 
        # radio buttons.
        if '__WXMAC__' in wx.PlatformInfo:
            itemId = event.arguments['sender'].widget.GetId()
            pos = self.widget.getIdPos(itemId)
            self.widget.setSelectedChoice(pos)
        self.synchronizeWidget()

        
class wxScrolledContainer (wx.ScrolledWindow):
    def wxSynchronizeWidget(self, useHints=False):
        if self.blockItem.isShown:
            sizer = self.GetSizer()
            sizer.Clear()
            for childBlock in self.blockItem.childrenBlocks:
                if childBlock.isShown and isinstance (childBlock, RectangularChild):
                    sizer.Add (childBlock.widget,
                               childBlock.stretchFactor, 
                               wxRectangularChild.CalculateWXFlag(childBlock), 
                               wxRectangularChild.CalculateWXBorder(childBlock))
            self.Layout()
            self.SetScrollRate(0,1)

        
class ScrolledContainer(BoxContainer):
    def instantiateWidget (self):
        return wxScrolledContainer (self.parentBlock.widget, self.getWidgetID())    

#from util.autolog import indentlog
class wxSplitterWindow(wx.SplitterWindow):
    #import util.autolog;  __metaclass__ = util.autolog.LogTheMethods
    def __init__(self, *arguments, **keywords):
        super (wxSplitterWindow, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,
                  self.OnSplitChanged,
                  id=self.GetId())
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING,
                  self.OnSplitChanging,
                  id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Setting minimum pane size prevents unsplitting a window by double-clicking
        self.SetMinimumPaneSize(7) #weird number to help debug the weird sizing bug 3497

    @WithoutSynchronizeWidget
    def OnSize(self, event):
        newSize = self.GetSize()
        blockItem = self.blockItem
        blockItem.size = SizeType (newSize.width, newSize.height)
        
        if blockItem.orientationEnum == "Horizontal":
            distance = blockItem.size.height
        else:
            distance = blockItem.size.width
        position = int (distance * blockItem.splitPercentage + 0.5)
        self.AdjustAndSetSashPosition (position)
        event.Skip()

    def AdjustAndSetSashPosition (self, position):
        width, windowSize = self.GetSizeTuple()
        if self.GetSplitMode() == wx.SPLIT_VERTICAL:
            windowSize = width

        splitController = self.blockItem.splitController
        if splitController is not None:
            position = splitController.AdjustSplit (windowSize, position)

        self.SetSashPosition (position)

    def OnSplitChanging(self, event):
        """
          Called when the user attempts to change the splitter. We need to calculate and store
          the new splitPercentage here. This means that the splitPercentage won't change in
          response to a window size change, which is important if resizing windows small then
          large will get you back to where you started (bug #6164). Also, multiple size events
          come through when sizer Layout is called and we don't want to change the percentage
          in response to these size changes          
        """
        if not self.blockItem.allowResize:
            event.SetSashPosition(-1)
        else:
            width, windowSize = self.GetSizeTuple()
            if self.GetSplitMode() == wx.SPLIT_VERTICAL:
                windowSize = width
            assert windowSize >= 0
            self.blockItem.splitPercentage = float (event.GetSashPosition()) / windowSize
        event.Skip()

    def OnSplitChanged(self, event):
        self.AdjustAndSetSashPosition (event.GetSashPosition())

    def wxSynchronizeWidget(self, useHints=False):
        blockItem = self.blockItem
        self.SetSize ((blockItem.size.width, blockItem.size.height))

        assert (len (blockItem.childrenBlocks) >= 1 and
                len (blockItem.childrenBlocks) <= 2), "We don't currently allow splitter windows with no contents"

        # Collect information about the splitter
        oldWindow1 = self.GetWindow1()
        oldWindow2 = self.GetWindow2()

        children = iter (blockItem.childrenBlocks)

        window1 = None
        child1 = children.next()
        if child1.isShown:
            window1 = child1.widget
        child1.widget.Show (child1.isShown)

        window2 = None
        if len (blockItem.childrenBlocks) >= 2:
            child2 = children.next()
            if child2.isShown:
                window2 = child2.widget
            child2.widget.Show (child2.isShown)

        shouldSplit = bool (window1) and bool (window2)
        
        # Update any differences between the block and widget
        self.Freeze()
        if not self.IsSplit() and shouldSplit:
            #indentlog("first time splitter creation: 2 win")
            """
            First time SplitterWindow creation with two windows or
            going between a split with one window to a split with
            two windows
            """
            if blockItem.orientationEnum == "Horizontal":
                position = blockItem.size.height * blockItem.splitPercentage
                success = self.SplitHorizontally (window1, window2, position)
            else:
                position = blockItem.size.width * blockItem.splitPercentage
                success = self.SplitVertically (window1, window2, position)
            assert success
        elif not oldWindow1 and not oldWindow2 and not shouldSplit:
            """
            First time splitterWindow creation with one window.
            """
            if window1:
                self.Initialize (window1)
            else:
                self.Initialize (window2)
        else:
            #indentlog("weird else block")
            if self.IsSplit() and not shouldSplit:
                """
                Going from two windows in a split to one window in a split.
                """
                show = oldWindow2.IsShown()
                success = self.Unsplit()
                oldWindow2.Show (show)
                assert success
            """
            Swap window1 and window2 so we can simplify the we can finish
            our work with only two comparisons.
            """            
            if bool (oldWindow1) ^ bool (window1):
                window1, window2 = window2, window1
            if window1:
                success = self.ReplaceWindow (oldWindow1, window1)
                assert success
            if window2:
                success = self.ReplaceWindow (oldWindow2, window2)
                assert success
        parent = self.GetParent()
        if parent:
            parent.Layout()
        self.Thaw()

    @classmethod
    def CalculateWXStyle(theClass, block):
        style = wx.SP_LIVE_UPDATE | wx.NO_BORDER | wx.SP_3DSASH
        return style

 
class SplitterWindow(RectangularChild):
    """
    This block seems to ignore children's stretchFactors.
    """

    splitPercentage = schema.One(schema.Float, initialValue = 0.5)
    allowResize = schema.One(schema.Boolean, initialValue = True)
    orientationEnum = schema.One(
        orientationEnumType, initialValue = 'Horizontal',
    )

    splitController = schema.One(inverse=Block.splitter, defaultValue=None)
  
    schema.addClouds(
        copying = schema.Cloud (byCloud = [splitController])
    )


    def instantiateWidget (self):
        return wxSplitterWindow (self.parentBlock.widget,
                                 self.getWidgetID(), 
                                 wx.DefaultPosition,
                                 (self.size.width, self.size.height),
                                 style=wxSplitterWindow.CalculateWXStyle(self))
                

class wxViewContainer (wxBoxContainer):
    pass


class tabPositionEnumType(schema.Enumeration):
      values = "Top","Bottom","Right","Left"


class ViewContainer(BoxContainer):

    tabPositionEnum = schema.One(
        tabPositionEnumType, initialValue = 'Top',
    )
    selectionIndex = schema.One (schema.Integer, initialValue = 0)
    views = schema.Mapping(Block, initialValue = {})
    activeView = schema.One (Block)

    schema.addClouds(
        copying = schema.Cloud(byRef=[views])
    )

    def instantiateWidget (self):
        """
        When the ViewContainer is the root of all the blocks it
        doesn't have a parent block widget, so in that case we use
        the block must have a frame and we'll use it.
        """
        if self.parentBlock is not None:
            parentWidget = self.parentBlock.widget
        else:
            parentWidget = self.frame

        return wxViewContainer (parentWidget)
    
    def onChoiceEventUpdateUI (self, event):
        assert len (self.childrenBlocks) == 1
        event.arguments ['Check'] = self.activeView == self.views [event.choice]

    def onChoiceEvent (self, event):
        view = self.views [event.choice]
        if view != self.activeView:
            self.activeView = view
            self.postEventByName ('SelectItemsBroadcast', {'items':[view]})

class wxFrameWindow (wxViewContainer):
    pass

class FrameWindow (ViewContainer):
    """
    Note: @@@ For now a FrameWindow is just a ViewContainer with added
    position attributes, but we will want to move a lot of MainFrame code
    from Application.py into here.

    Right now we special case MainFrame, but we should better work that
    into the block framework.
    """
    position = schema.One(PositionType, initialValue = PositionType(-1, -1))
    windowTitle = schema.One(schema.Text, defaultValue = '')


class wxTabbedContainer(DragAndDrop.DropReceiveWidget, 
                        DragAndDrop.ItemClipboardHandler,
                        wx.Notebook):
    def __init__(self, *arguments, **keywords):
        super (wxTabbedContainer, self).__init__ (*arguments, **keywords)
        self.selectedTab = 0
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnWXSelectItem,
                  id=self.GetId())

    def CalculateWXStyle(self, block):
        if block.tabPosEnum == "Top":
            style = 0
        elif block.tabPosEnum == "Bottom":
            style = wx.NB_BOTTOM
        elif block.tabPosEnum == "Left":
            style = wx.NB_LEFT
        elif block.tabPosEnum == "Right":
            style = wx.NB_RIGHT
        elif __debug__:
            assert False
        return style
    CalculateWXStyle = classmethod(CalculateWXStyle)

    @WithoutSynchronizeWidget
    def OnWXSelectItem (self, event):
        selection = event.GetSelection()
        if self.selectedTab != selection:
            self.selectedTab = selection
            page = self.GetPage(self.selectedTab)
            self.blockItem.postEventByName("SelectItemsBroadcast",
                                           {'items':[page.blockItem]})
        event.Skip()
        
    def OnRequestDrop(self, x, y):
        tab = self.HitTest((x, y))[0]
        if tab > -1:
            self.SetSelection(tab)
            return True
        return False

    def AddItems(self, itemList):
        for node in itemList:
            try:
                newItem = node.item
            except AttributeError:
                pass
            else:
                if isinstance(newItem, Block):
                    self.blockItem.ChangeCurrentTab(node)

    def OnEnter(self, x, y, dragResult):
        self.enterTime = time.time()
        return dragResult
        
    def OnHover(self, x, y, dragResult):
        currentTab = self.HitTest((x, y))[0]
        if currentTab < 0:
            return dragResult
        currentTime = time.time()
        if not hasattr(self, "hoverTab") or self.hoverTab != currentTab:
            self.hoverTab = currentTab            
            self.dropTarget.enterTime = currentTime
        elif (currentTime - self.dropTarget.enterTime) > 1:
            self.SetSelection(currentTab)
        return dragResult
            
    def wxSynchronizeWidget(self, useHints=False):
        assert(len(self.blockItem.childrenBlocks) >= 1), "Tabbed containers cannot be empty"
        self.Freeze()
        for pageNum in range (self.GetPageCount()):
            page = self.GetPage(0)
            if not page.blockItem.parentBlock:
                self.DeletePage(0)
            else:
                self.RemovePage(0)
        index = 0
        for child in self.blockItem.childrenBlocks:
            self.AddPage (child.widget, self.blockItem._getBlockName(child))
            index += 1
        self.SetSelection(self.selectedTab)
        page = self.GetPage(self.selectedTab)
        self.Thaw()


class TabbedContainer(RectangularChild):

    tabPosEnum = schema.One(tabPositionEnumType, initialValue = 'Top')
    tabNames = schema.Sequence(schema.Text)

    def instantiateWidget (self):
        return wxTabbedContainer (self.parentBlock.widget, 
                                  self.getWidgetID(),
                                  wx.DefaultPosition,
                                  (self.size.width, self.size.height),
                                  style=wxTabbedContainer.CalculateWXStyle(self))

    
    def onChoiceEvent (self, event):
        choice = event.choice
        for index in xrange (self.widget.GetPageCount()):
            if self.widget.GetPageText(index) == choice:
                self.widget.SetSelection (index)
                break

    def _getBlockName(self, block):
        try:
            item = block.contents
        except AttributeError:
            item = block
            
        try:
            return item.displayName
        except AttributeError:
            return u""


class TabbedView(TabbedContainer):
    def ChangeCurrentTab(self, item):
        if hasattr (self, 'widget'):
            # tabbed container hasn't been rendered yet
            activeTab = self.widget.GetSelection()
            itemName = self._getBlockName(item)
            found = False
            for tabIndex in range(self.widget.GetPageCount()):
                tabName = self.widget.GetPageText(tabIndex)
                if tabName == itemName:
                    found = True
                    self.widget.SetSelection(tabIndex)
            self.parentBlock.widget.Freeze()
            if not found:
                page = self.widget.GetPage(activeTab)
                previousChild = self.childrenBlocks.previous(page.blockItem)
                page.blockItem.parentBlock = None
    
                item.parentBlock = self 
                self.childrenBlocks.placeItem(item, previousChild)
                item.render()                
                item.widget.SetSize (self.widget.GetClientSize())                
            self.synchronizeWidget()
            self.parentBlock.widget.Thaw()

    def onNewEvent (self, event):
        "Create a new tab: under construction"
        pass


    def onCloseEvent (self, event):
        """
        Will either close the current tab (if not data is present
        in the sender) or will close the tab specified by data.
        """
        try:
            item = event.arguments['sender'].data
        except AttributeError:
            pageIndex = self.widget.GetSelection()
        else:
            for tabIndex in range (self.widget.GetPageCount()):
                tabName = self.widget.GetPageText(tabIndex)
                if tabName == self._getBlockName(item):
                    found = True
                    pageIndex = tabIndex
            if not found:
                # Tab isn't actually open
                return
        if pageIndex == self.widget.GetSelection():
            if pageIndex == (self.widget.GetPageCount() - 1):
                self.widget.selectedTab = pageIndex - 1
            else:
                self.widget.selectedTab = pageIndex
        elif pageIndex < self.widget.GetSelection():
            self.widget.selectedTab = self.widget.GetSelection() - 1
        page = self.widget.GetPage(pageIndex)
        page.blockItem.parentBlock = None
        self.parentBlock.widget.Freeze()        
        self.synchronizeWidget()
        self.parentBlock.widget.Thaw()
        self.postEventByName ('SelectItemsBroadcast',
                              {'items':[self.widget.GetPage(self.widget.selectedTab).blockItem]})

    def onOpenEvent (self, event):
        "Opens the chosen item in a new tab"
        item = event.arguments['sender'].arguments
        found = False
        for tabIndex in range (self.widget.GetPageCount()):
            tabName = self.widget.GetPageText (tabIndex)
            if tabName == self._getBlockName(item):
                found = True
                self.widget.SetSelection(tabIndex)
        if not found:
            self.widget.selectedTab = self.widget.GetPageCount()
            item.parentBlock = self
            self.parentBlock.widget.Freeze()
            item.render()
            item.widget.SetSize (self.widget.GetClientSize())
            self.synchronizeWidget()
            self.parentBlock.widget.Thaw()
            self.postEventByName ('SelectItemsBroadcast', {'items':[item]})
        
    def onCloseEventUpdateUI(self, event):
        event.arguments['Enable'] = (self.widget.GetPageCount() > 1)
        
    def _getUniqueName (self, name):
        if not self.hasChild(name):
            return name
        number = 1
        uniqueName = name + u"-" + unicode(number)
        while self.hasChild(uniqueName):
            number += 1
            uniqueName = name + u"-" + unicode(number)
        return uniqueName

        
