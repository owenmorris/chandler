__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import Block, RectangularChild, wxRectangularChild, ContainerChild
from DragAndDrop import DropReceiveWidget as DropReceiveWidget
from Node import Node
from Styles import Font
from repository.util.UUID import UUID
import wx
import time


class wxBoxContainer (wxRectangularChild):

    def wxSynchronizeWidget(self, *arguments, **keywords):
        super (wxBoxContainer, self).wxSynchronizeWidget (*arguments, **keywords)
        
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


class BoxContainer (RectangularChild):
    def instantiateWidget (self):
        if self.orientationEnum == 'Horizontal':
            orientation = wx.HORIZONTAL
        else:
            orientation = wx.VERTICAL

        sizer = wx.BoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))

        if self.parentBlock:
            parentWidget = self.parentBlock.widget
        else:
            parentWidget = Globals.wxApplication.mainFrame
 
        widget = wxBoxContainer (parentWidget, Block.getWidgetID(self))
        widget.SetSizer (sizer)

        return widget


class wxChoiceContainer(wxBoxContainer):
    def __init__(self, *arguments, **keywords):
        super (wxChoiceContainer, self).__init__ (*arguments, **keywords)
            
    def wxSynchronizeWidget(self, *arguments, **keywords):
        from DynamicContainerBlocks import Toolbar as Toolbar
        selectedChoice = self._getSelectedChoice()
        if selectedChoice != self.blockItem.selection:
            for childBlock in self.blockItem.childrenBlocks:
                if not isinstance(childBlock, Toolbar):
                    childBlock.parentBlock = None
                    if hasattr(childBlock, 'widget'):
                        childBlock.widget.Destroy()
            super(wxChoiceContainer, self).wxSynchronizeWidget(*arguments, **keywords)

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

    def _getSelectedChoice(self):
        from DynamicContainerBlocks import Toolbar as Toolbar
        index = 0
        for childBlock in self.blockItem.childrenBlocks:
            if isinstance(childBlock, Toolbar):
                for toolbarItem in childBlock.widget.toolItemList:
                    if childBlock.widget.GetToolState(toolbarItem.widget.GetId()):
                        return index
                    index += 1
        assert True, "There should always be something selected"
        return 0
            

class ChoiceContainer(BoxContainer):
    def instantiateWidget (self):
        self.selection = -1
        if self.orientationEnum == 'Horizontal':
            orientation = wx.HORIZONTAL
        else:
            orientation = wx.VERTICAL

        sizer = wx.BoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))
        parentWidget = self.parentBlock.widget 
        widget = wxChoiceContainer(parentWidget, Block.getWidgetID(self))
        widget.SetSizer (sizer)

        return widget

    def onButtonPressed(self, notification):
        try:
            self.widget.wxSynchronizeWidget()    
        except AttributeError:
            pass


class EmbeddedContainer(RectangularChild):
    def instantiateWidget (self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(self.parentBlock.widget, -1)
        panel.SetSizer(sizer)
        try:
            newChild = self.contents.data[0]
        except IndexError:
            return None
        else:
            newChild.parentBlock = self
            self.RegisterEvents(newChild)
            Globals.mainView.onSetActiveView(newChild)
            return panel
    
    def onSelectionChangedEvent(self, notification):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            node = notification.data['item']
            if node and isinstance(node, Node):
                newChild = node.item
                if isinstance(newChild, Block):
                    embeddedSizer = self.widget.GetSizer ()
                    assert self.contents.queryEnum  == "ListOfItems", "EmbeddedContainers must have a ListOfItems Query"
                    oldChild = self.contents.data[0]
                    self.UnregisterEvents(oldChild)
                    oldChild.parentBlock = None
                
                    self.contents.data = [newChild]
                    newChild.parentBlock = self
                    newChild.render()
                    self.RegisterEvents(newChild)
                    Globals.mainView.onSetActiveView(newChild)
                    
                    embeddedSizer.Layout()

        
class wxSplitterWindow(wx.SplitterWindow):

    def __init__(self, *arguments, **keywords):
        super (wxSplitterWindow, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,
                  self.OnSplitChanged,
                  id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        """
          Setting minimum pane size prevents unsplitting a window by double-clicking
        """
        self.SetMinimumPaneSize(20)
 
    def OnSize(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            newSize = self.GetSize()
            self.blockItem.size.width = newSize.width
            self.blockItem.size.height = newSize.height
            if self.blockItem.orientationEnum == "Horizontal":
                distance = self.blockItem.size.height
            else:
                distance = self.blockItem.size.width
            self.SetSashPosition (int (distance * self.blockItem.splitPercentage + 0.5))
        event.Skip()

    def OnSplitChanged(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            width, height = self.GetSizeTuple()
            position = float (event.GetSashPosition())
            splitMode = self.GetSplitMode()
            if splitMode == wx.SPLIT_HORIZONTAL:
                self.blockItem.splitPercentage = position / height
            else:
                self.blockItem.splitPercentage = position / width

    def wxSynchronizeWidget(self):
        self.SetSize ((self.blockItem.size.width, self.blockItem.size.height))

        assert (len (self.blockItem.childrenBlocks) >= 1 and
                len (self.blockItem.childrenBlocks) <= 2), "We don't currently allow splitter windows with no contents"

        # Collect information about the splitter
        oldWindow1 = self.GetWindow1()
        oldWindow2 = self.GetWindow2()
 
        children = iter (self.blockItem.childrenBlocks)

        window1 = None
        child1 = children.next()
        if child1.isShown:
            window1 = child1.widget
        child1.widget.Show (child1.isShown)

        window2 = None
        if len (self.blockItem.childrenBlocks) >= 2:
            child2 = children.next()
            if child2.isShown:
                window2 = child2.widget
            child2.widget.Show (child2.isShown)

        shouldSplit = bool (window1) and bool (window2)
        
        # Update any differences between the block and widget
        self.Freeze()
        if not self.IsSplit() and shouldSplit:
            """
              First time SplitterWindow creation with two windows or going between
            a split with one window to a split with two windows
            """            
            if self.blockItem.orientationEnum == "Horizontal":
                position = self.blockItem.size.height * self.blockItem.splitPercentage
                success = self.SplitHorizontally (window1, window2, position)
            else:
                position = self.blockItem.size.width * self.blockItem.splitPercentage
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

    def CalculateWXStyle(self, block):
        style = wx.SP_LIVE_UPDATE
        parent = block.parentBlock
        while isinstance (parent, EmbeddedContainer):
            parent = parent.parentBlock
        if isinstance (parent, SplitterWindow):
            style |= wx.SP_3DSASH
        else:
            style |= wx.SP_3D
        return style
    CalculateWXStyle = classmethod(CalculateWXStyle)
 
class SplitterWindow(RectangularChild):
    def instantiateWidget (self):
        return wxSplitterWindow (self.parentBlock.widget,
                                 Block.getWidgetID(self), 
                                 wx.DefaultPosition,
                                 (self.size.width, self.size.height),
                                 style=wxSplitterWindow.CalculateWXStyle(self))
                
    
class wxTabbedContainer(DropReceiveWidget, wx.Notebook):
    def __init__(self, *arguments, **keywords):
        super (wxTabbedContainer, self).__init__ (*arguments, **keywords)
        self.selectedTab = 0
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnWXSelectionChanged,
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
            assert (False)
        return style
    CalculateWXStyle = classmethod(CalculateWXStyle)

    def OnWXSelectionChanged (self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            self.selectedTab = event.GetSelection()
            page = self.GetPage(self.selectedTab)
            Globals.mainView.onSetActiveView(page.blockItem)
        event.Skip()
        
    def OnRequestDrop(self, x, y):
        tab = self.HitTest((x, y))[0]
        if tab > -1:
            self.SetSelection(tab)
            return True
        return False

    def AddItem(self, itemUUID):
        node = Globals.repository.findUUID(itemUUID)
        try:
            newItem = node.item
        except AttributeError:
            pass
        else:
            if isinstance(newItem, Block):
                self.blockItem.ChangeCurrentTab(node)

    def OnHover(self, x, y):
        currentTab = self.HitTest((x, y))[0]
        if currentTab < 0:
            return
        currentTime = time.time()
        if not hasattr(self, "hoverTab") or self.hoverTab != currentTab:
            self.hoverTab = currentTab            
            self.dropTarget.enterTime = currentTime
        elif (currentTime - self.dropTarget.enterTime) > 1:
            self.SetSelection(currentTab)
            
    def wxSynchronizeWidget(self):
        from osaf.framework.notifications.NotificationManager import NotSubscribed as NotSubscribed
        assert(len(self.blockItem.childrenBlocks) >= 1), "Tabbed containers cannot be empty"
        assert(len(self.blockItem.childrenBlocks) == len(self.blockItem.tabNames)), "Improper number of tabs"
        self.Freeze()
        for pageNum in range (self.GetPageCount()):
            page = self.GetPage(0)
            if not page.blockItem.parentBlock:
                self.DeletePage(0)
            else:
                self.RemovePage(0)
        index = 0
        for child in self.blockItem.childrenBlocks:
            self.AddPage (child.widget, self.blockItem.tabNames[index])
            index += 1
        self.SetSelection(self.selectedTab)
        self.Thaw()
        

class TabbedContainer(RectangularChild):
    def instantiateWidget (self):
        return wxTabbedContainer (self.parentBlock.widget, 
                                  Block.getWidgetID(self),
                                  wx.DefaultPosition,
                                  (self.size.width, self.size.height),
                                  style=wxTabbedContainer.CalculateWXStyle(self))

    
    def onChoiceEvent (self, notification):
        choice = notification.event.choice
        for index in xrange (self.widget.GetPageCount()):
            if self.widget.GetPageText(index) == choice:
                self.widget.SetSelection (index)
                break
