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
            panel = wx.Panel(parentWindow, -1)
            panel.SetSizer(sizer)
            self.parentBlock.addToContainer(parent, panel, 
                                                             self.stretchFactor, 
                                                             self.Calculate_wxFlag(), 
                                                             self.Calculate_wxBorder())
            return panel, sizer, panel
        else:
            parent.SetSizer(sizer)
            return parent, sizer, parent
                
    def addToContainer(self, parent, child, weight, flag, border, append=True):
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
                self.RegisterEvents(newChild)
                newChild.render (embeddedSizer, embeddedPanel)
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
        if not Globals.wxApplication.insideSynchronizeFramework:
            counterpart = Globals.repository.find (self.counterpartUUID)
            width, height = self.GetSizeTuple()
            position = float (event.GetSashPosition())
            splitMode = self.GetSplitMode()
            if splitMode == wx.SPLIT_HORIZONTAL:
                counterpart.splitPercentage = position / height
            elif splitMode == wx.SPLIT_VERTICAL:
                counterpart.splitPercentage = position / width

    def OnSize(self, event):
        if not Globals.wxApplication.insideSynchronizeFramework:
            """
              Calling Skip causes wxWindows to continue processing the event, 
            which will cause the parent class to get a crack at the event.
            """
            event.Skip()
            counterpart = Globals.repository.find (self.counterpartUUID)
            counterpart.size.width = self.GetSize().x
            counterpart.size.height = self.GetSize().y
            counterpart.setDirty()   # Temporary repository hack -- DJA

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
        """
          Wire up onSize after __init__ has been called, otherwise it will
        call onSize
        """
        splitWindow.Bind(wx.EVT_SIZE, splitWindow.OnSize)
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

    def addToContainer(self, parent, child, weight, flag, border, append=True):
        if not hasattr(self, 'childrenToAdd'):
            self.childrenToAdd = []
        self.childrenToAdd.append(child)

    def removeFromContainer(self, parent, child, doDestroy=True):
        try:
            self.childrenToAdd.remove(child)
        except ValueError:
            parent.Unsplit(child)
            if doDestroy:
                child.Destroy()
                    
    def handleChildren(self, window):
        numChildrenToAdd = len(self.childrenToAdd)
        if numChildrenToAdd == 1:
            window1 = window.GetWindow1()
            if not window1:
                window.Initialize(self.childrenToAdd[0])
            else:
                self.doSplitWindow(window, self.childrenToAdd[0], window1)
        elif numChildrenToAdd == 2:
            self.doSplitWindow(window, self.childrenToAdd[0], self.childrenToAdd[1])
        self.childrenToAdd = []
        return window

    def doSplitWindow(self, window, window1, window2):
        width, height = window.GetSizeTuple()
        assert self.splitPercentage >= 0.0 and self.splitPercentage < 1.0
        if self.orientationEnum == "Horizontal":
            window.SplitHorizontally(window1,
                                     window2,
                                     int (round (height * self.splitPercentage)))
        else:
            window.SplitVertically(window1,
                                   window2,
                                   int (round (width * self.splitPercentage)))
    

class TabbedContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        try:
            id = Block.getwxID(self.selectionChanged)
        except AttributeError:
            id = 0
            
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

        tabbedContainer = wx.Notebook(parentWindow, id, 
                                    wx.DefaultPosition,
                                    (self.minimumSize.width, self.minimumSize.height),
                                     style = style)
        self.parentBlock.addToContainer(parent, tabbedContainer, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return tabbedContainer, tabbedContainer, tabbedContainer

    def addToContainer(self, parent, child, weight, flag, border, append=True):
        if not hasattr(self, 'childrenToAdd'):
            self.childrenToAdd = []
        self.childrenToAdd.append(child)

    def removeFromContainer(self, parent, child, doDestroy=True):
        # @@@ Must be implemented
        pass

    def handleChildren(self, window):
        if len (self.childrenToAdd) > 0:
            childNameIndex = 0
            for child in self.childrenToAdd:
                window.AddPage(child, self.tabNames[childNameIndex])
                childNameIndex = childNameIndex + 1
        self.childrenToAdd = []

    def OnChooseTabEvent (self, notification):
        tabbedContainer = Globals.association[self.itsUUID]
        choice = notification.event.choice
        for index in xrange (tabbedContainer.GetPageCount()):
            if tabbedContainer.GetPageText(index) == choice:
                tabbedContainer.SetSelection (index)
                break


class Toolbar(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        toolbar = Globals.wxApplication.mainFrame.CreateToolBar(wx.TB_HORIZONTAL)
        toolbar.SetToolBitmapSize((self.toolSize.width, self.toolSize.height))
        return toolbar, None, None

    def toolPressed(self, event):
        pass
    
    def toolEnterPressed(self, event):
        pass


