__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import time
import application.Globals as Globals
from Block import *
from Node import Node
from Styles import Font
from repository.util.UUID import UUID
from wxPython.wx import *
from wxPython.gizmos import *
from wxPython.html import *


class BoxContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        if self.orientationEnum == 'Horizontal':
            orientation = wxHORIZONTAL
        else:
            orientation = wxVERTICAL

        sizer = wxBoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))

        if self.parentBlock: 
            panel = wxPanel(parentWindow, -1)
            panel.SetSizer(sizer)
            self.getParentBlock(parentWindow).addToContainer(parent, panel, 
                                                             self.stretchFactor, 
                                                             self.Calculate_wxFlag(), 
                                                             self.Calculate_wxBorder())
            return panel, sizer, panel
        else:
            parent.SetSizer(sizer)
            return parent, sizer, parent
                
    def addToContainer(self, parent, child, weight, flag, border):
        parent.Add(child, int(weight), flag, border)
        
    def removeFromContainer(self, parent, child):
        parent.Remove(child)
        child.Destroy()
        parent.Layout()


class EmbeddedContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        sizer = wxBoxSizer(wxHORIZONTAL)
        panel = wxPanel(parentWindow, -1)
        panel.SetSizer(sizer)
        self.getParentBlock(parentWindow).addToContainer(parent, panel, self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        newChild = Globals.repository.find (self.contentSpec.data)
        if newChild:
            newChild.parentBlock = self
            self.RegisterEvents(newChild)
            return panel, sizer, panel
        return None, None, None

    def addToContainer (self, parent, child, weight, flag, border):
        parent.Add(child, int(weight), flag, border)
        
    def removeFromContainer(self, parent, child):
        parent.Remove (child)
        child.Destroy ()
        parent.Layout ()
    
    def OnSelectionChangedEvent(self, notification):
        node = notification.data['item']
        if node and isinstance(node, Node):
            newChild = node.item
            if isinstance(newChild, Block):
                try:
                    embeddedPanel = Globals.association [self.getUUID()]
                except KeyError:
                    return  # embedded container hasn't been rendered yet
                embeddedSizer = embeddedPanel.GetSizer ()

                oldChild = Globals.repository.find (self.contentSpec.data)
                wxOldChild = Globals.association [oldChild.getUUID()]
                self.UnregisterEvents(oldChild)
                self.removeFromContainer (embeddedSizer, wxOldChild)
                oldChild.parentBlock = None
            
                newChild = node.item
                self.contentSpec.data = str (newChild.getItemPath())
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
 
        
class wxSplitWindow(wxSplitterWindow):

    def __init__(self, *arguments, **keywords):
        wxSplitterWindow.__init__ (self, *arguments, **keywords)
        EVT_SPLITTER_SASH_POS_CHANGED(self, self.GetId(), self.OnSplitChanged)
        # Setting minimum pane size prevents unsplitting a window via
        # double-clicking:
        self.SetMinimumPaneSize(20)
 
    def OnSplitChanged(self, event):
        counterpart = Globals.repository.find (self.counterpartUUID)
        width, height = self.GetSizeTuple()
        position = float (event.GetSashPosition())
        splitMode = self.GetSplitMode()
        if splitMode == wxSPLIT_HORIZONTAL:
            counterpart.splitPercentage = position / height
        elif splitMode == wxSPLIT_VERTICAL:
            counterpart.splitPercentage = position / width

    def OnSize(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, which
        will cause the parent class to get a crack at the event.
        """
        event.Skip()
        counterpart = Globals.repository.find (self.counterpartUUID)
        counterpart.size.width = self.GetSize().x
        counterpart.size.height = self.GetSize().y
        counterpart.setDirty()   # Temporary repository hack -- DJA


class SplitWindow(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        splitWindow = wxSplitWindow(parentWindow,
                                    Block.getwxID(self), 
                                    wxDefaultPosition,
                                    (self.size.width, self.size.height),
                                    style=self.Calculate_wxStyle(parentWindow))
        self.getParentBlock(parentWindow).addToContainer(parent, splitWindow, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        """
          Wire up onSize after __init__ has been called, otherwise it will
        call onSize
        """
        EVT_SIZE(splitWindow, splitWindow.OnSize)
        return splitWindow, splitWindow, splitWindow
                
    def Calculate_wxStyle (self, parentWindow):
        style = wxSP_LIVE_UPDATE|wxNO_FULL_REPAINT_ON_RESIZE
        parent = self.getParentBlock(parentWindow)
        while isinstance (parent, EmbeddedContainer):
            parent = parent.getParentBlock(Globals.association[parent.getUUID()])
        if isinstance (parent, SplitWindow):
            style |= wxSP_3DSASH
        else:
            style |= wxSP_3D
        return style

    def addToContainer(self, parent, child, weight, flag, border):
        if not hasattr(self, 'childrenToAdd'):
            self.childrenToAdd = []
        self.childrenToAdd.append(child)
        
    def removeFromContainer(self, parent, child):
        # @@@ Must be implemented
        pass
        
    def handleChildren(self, window):
        assert (len (self.childrenToAdd) == 2)
        width, height = window.GetSizeTuple()
        assert self.splitPercentage >= 0.0 and self.splitPercentage < 1.0
        if self.orientationEnum == "Horizontal":
            window.SplitHorizontally(self.childrenToAdd[0],
                                     self.childrenToAdd[1],
                                     int (round (height * self.splitPercentage)))
        else:
            window.SplitVertically(self.childrenToAdd[0],
                                   self.childrenToAdd[1],
                                   int (round (width * self.splitPercentage)))
        self.childrenToAdd = []
        return window
   
    
class TabbedContainer(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        try:
            id = Block.getwxID(self.selectionChanged)
        except AttributeError:
            id = 0
            
        if self.tabPosEnum == "Top":
            style = 0
        elif self.tabPosEnum == "Bottom":
            style = wxNB_BOTTOM
        elif self.tabPosEnum == "Left":
            style = wxNB_LEFT
        elif self.tabPosEnum == "Right":
            style = wxNB_RIGHT
        elif __debug__:
            assert (False)
            
        tabbedContainer = wxNotebook(parentWindow, id, 
                                    wxDefaultPosition,
                                    (self.minimumSize.width, self.minimumSize.height),
                                     style = style)
        self.getParentBlock(parentWindow).addToContainer(parent, tabbedContainer, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return tabbedContainer, tabbedContainer, tabbedContainer
                
    def addToContainer(self, parent, child, weight, flag, border):
        if not hasattr(self, 'childrenToAdd'):
            self.childrenToAdd = []
        self.childrenToAdd.append(child)
        
    def removeFromContainer(self, parent, child):
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
        tabbedContainer = Globals.association[self.getUUID()]
        choice = notification.event.choice
        for index in xrange (tabbedContainer.GetPageCount()):
            if tabbedContainer.GetPageText(index) == choice:
                tabbedContainer.SetSelection (index)
                break


class Toolbar(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        toolbar = wxToolBar(Globals.wxApplication.mainFrame, -1)
        toolbar.SetToolBitmapSize((self.toolSize.width, self.toolSize.height))
        Globals.wxApplication.mainFrame.SetToolBar(toolbar)
        return toolbar, None, None

    def toolPressed(self, event):
        pass
    
    def toolEnterPressed(self, event):
        pass


