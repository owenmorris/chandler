__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from Node import Node
from Styles import Font
from repository.util.UUID import UUID
import wx


class BoxContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        if self.orientationEnum == 'Horizontal':
            orientation = wx.HORIZONTAL
        else:
            orientation = wx.VERTICAL

        sizer = wx.BoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))

        if self.parentBlock:
            parentWidget = Globals.association [self.parentBlock.itsUUID]
            widget = wxRectangularChild (parentWidget, -1)
            self.parentBlock.addToContainer (parentWidget,
                                             widget, 
                                             self.stretchFactor, 
                                             self.Calculate_wxFlag(), 
                                             self.Calculate_wxBorder())
        else:
            parentWidget = None
            widget = Globals.wxApplication.mainFrame

        widget.SetSizer (sizer)

        return widget, None, parentWidget
                
    def addToContainer(self, parent, child, weight, flag, border, append=True):
        parentSizer = parent.GetSizer()
        if append:
            parentSizer.Add(child, int(weight), flag, border)
        else:
            parentSizer.Prepend(child, int(weight), flag, border)
        
    def removeFromContainer(self, parent, child, doDestroy=True):
        parentSizer = parent.GetSizer()
        parentSizer.Remove(child)
        if doDestroy:
            child.Destroy()
        parentSizer.Layout()


class EmbeddedContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(parentWindow, -1)
        panel.SetSizer(sizer)
        self.parentBlock.addToContainer(parent,
                                        panel,
                                        self.stretchFactor,
                                        self.Calculate_wxFlag(),
                                        self.Calculate_wxBorder())
        try:
            newChild = self.contentSpec.data[0]
        except IndexError:
            return None, None, None
        else:
            newChild.parentBlock = self
            self.RegisterEvents(newChild)
            Globals.mainView.onSetActiveView(newChild)
            return panel, sizer, panel
        

    def addToContainer (self, parent, child, weight, flag, border, append=True):
        if append:
            parent.Add(child, int(weight), flag, border)
        else:
            parent.Prepend(child, int(weight), flag, border)
        parent.Layout()
        
    def removeFromContainer(self, parent, child, doDestroy=True):
        parentSizer = parent.GetSizer()
        parentSizer.Remove(child)
        if doDestroy:
            child.Destroy()
        parentSizer.Layout()
    
    def OnSelectionChangedEvent(self, notification):
        node = notification.data['item']
        if node and isinstance(node, Node):
            newChild = node.item
            if isinstance(newChild, Block):
                try:
                    embeddedPanel = Globals.association [self.itsUUID]
                except KeyError:
                    return  # embedded container hasn't been rendered yet
                embeddedSizer = embeddedPanel.GetSizer ()

                assert self.contentSpec.queryEnum  == "ListOfItems", "EmbeddedContainers must have a ListOfItems Query"
                oldChild = self.contentSpec.data[0]
                wxOldChild = Globals.association [oldChild.itsUUID]
                self.UnregisterEvents(oldChild)
                self.removeFromContainer (embeddedPanel, wxOldChild)
                oldChild.parentBlock = None
            
                self.contentSpec.data = [newChild]
                newChild.parentBlock = self
                newChild.render (embeddedSizer, embeddedPanel)
                self.RegisterEvents(newChild)
                Globals.mainView.onSetActiveView(newChild)
                
                embeddedSizer.Layout()

    def RegisterEvents(self, block):
        try:
            events = block.blockEvents
        except AttributeError:
            return
        self.currentId = UUID()
        Globals.notificationManager.Subscribe(events, 
                                              self.currentId, 
                                              Globals.mainView.dispatchEvent)
 
    def UnregisterEvents(self, oldBlock):
        try:
            events = oldBlock.blockEvents
        except AttributeError:
            return
        try:
            id = self.currentId
        except AttributeError:
            return # If we haven't registered yet
        Globals.notificationManager.Unsubscribe(id)
 
        
class wxSplitWindow(wx.SplitterWindow):

    def __init__(self, *arguments, **keywords):
        wx.SplitterWindow.__init__ (self, *arguments, **keywords)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,
                  self.OnSplitChanged,
                  id=self.GetId())
        """
          Setting minimum pane size prevents unsplitting a window by double-clicking
        """
        self.SetMinimumPaneSize(20)
 
    def OnSplitChanged(self, event):
        if not Globals.wxApplication.ignoreSynchronizeFramework:
            counterpart = Globals.repository.find (self.counterpartUUID)
            width, height = self.GetSizeTuple()
            position = float (event.GetSashPosition())
            splitMode = self.GetSplitMode()
            if splitMode == wx.SPLIT_HORIZONTAL:
                counterpart.splitPercentage = position / height
            elif splitMode == wx.SPLIT_VERTICAL:
                counterpart.splitPercentage = position / width

    def wxSynchronizeFramework(self):
        block = Globals.repository.find (self.counterpartUUID)

        self.SetSize ((block.size.width, block.size.height))

        assert (len (block.childrenBlocks) >= 1 and
                len (block.childrenBlocks) <= 2), "We don't currently allow splitter windows with no contents"

        # Collect information about the splitter
        oldWindow1 = self.GetWindow1()
        oldWindow2 = self.GetWindow2()
 
        children = iter (block.childrenBlocks)

        window1 = None
        child1 = children.next()
        window = Globals.association[child1.itsUUID]
        if child1.open:
            window1 = window
        window.Show (child1.open)

        window2 = None
        if len (block.childrenBlocks) >= 2:
            child2 = children.next()
            window = Globals.association[child2.itsUUID]
            if child2.open:
                window2 = window
            window.Show (child2.open)

        shouldSplit = bool (window1) and bool (window2)
        
        # Update any differences between the block and widget
        self.Freeze()
        if not self.IsSplit() and shouldSplit:
            """
              First time splitWindow creation with two windows or going between
            a split with one window to a split with two windows
            """            
            if block.orientationEnum == "Horizontal":
                position = block.size.height * block.splitPercentage
                success = self.SplitHorizontally (window1, window2, position)
            else:
                position = block.size.width * block.splitPercentage
                success = self.SplitVertically (window1, window2, position)
            assert success
        elif not oldWindow1 and not oldWindow2 and not shouldSplit:
            """
              First time splitWindow creation with one window.
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
        
    def __del__(self):
        del Globals.association [self.counterpartUUID]

 
class SplitWindow(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        splitWindow = wxSplitWindow(parentWindow,
                                    Block.getwxID(self), 
                                    wx.DefaultPosition,
                                    (self.size.width, self.size.height),
                                    style=self.Calculate_wxStyle(parentWindow))
        self.parentBlock.addToContainer(parent, splitWindow, 
                                        self.stretchFactor, 
                                        self.Calculate_wxFlag(), 
                                        self.Calculate_wxBorder())
        return splitWindow, splitWindow, splitWindow
                
    def Calculate_wxStyle (self, parentWindow):
        style = wx.SP_LIVE_UPDATE
        parent = self.parentBlock
        while isinstance (parent, EmbeddedContainer):
            parent = parent.parentBlock
        if isinstance (parent, SplitWindow):
            style |= wx.SP_3DSASH
        else:
            style |= wx.SP_3D
        return style

    
class TabbedContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        self.tabIndex = 0
        try:
            id = Block.getwxID(self.selectionChanged)
        except AttributeError:
            id = 0
            
        tabbedContainer = wx.Notebook(parentWindow, id, 
                                      wx.DefaultPosition,
                                      (self.minimumSize.width, self.minimumSize.height),
                                      style = self.Calculate_wxStyle())
        
        self.parentBlock.addToContainer(parent, tabbedContainer, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())

        tabbedContainer.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnSelectionChanging)
        tabbedContainer.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSelectionChanged)

        return tabbedContainer, tabbedContainer, tabbedContainer

    def Calculate_wxStyle(self):
        if self.tabPosEnum == "Top":
            style = 0
        elif self.tabPosEnum == "Bottom":
            style = wx.NB_BOTTOM
        elif self.tabPosEnum == "Left":
            style = wx.NB_LEFT
        elif self.tabPosEnum == "Right":
            style = wx.NB_RIGHT
        elif __debug__:
            assert (False)
        return style

    def addToContainer(self, parent, child, weight, flag, border, append=True):
        assert self.tabIndex < len(self.tabNames)
        parent.AddPage(child, self.tabNames[self.tabIndex])
        self.tabIndex += 1

    def removeFromContainer(self, parent, child, doDestroy=True):
        # @@@ Must be implemented
        pass
    
    def OnChooseTabEvent (self, notification):
        tabbedContainer = Globals.association[self.itsUUID]
        choice = notification.event.choice
        for index in xrange (tabbedContainer.GetPageCount()):
            if tabbedContainer.GetPageText(index) == choice:
                tabbedContainer.SetSelection (index)
                break

    def OnSelectionChanging (self, event):
        event.Skip()

    def OnSelectionChanged (self, event):
        event.Skip()

        
class Toolbar(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        toolbar = Globals.wxApplication.mainFrame.CreateToolBar(wx.TB_HORIZONTAL)
        toolbar.SetToolBitmapSize((self.toolSize.width, self.toolSize.height))
        return toolbar, None, None

    def toolPressed(self, event):
        pass
    
    def toolEnterPressed(self, event):
        pass


