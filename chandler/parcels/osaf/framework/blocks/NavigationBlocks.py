__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from ControlBlocks import *
from Node import *
from repository.util.UUID import UUID
import wx


class wxBookmark(wx.StaticText):
    """
      Under construction
    """
    def __init__(self, parent, text, onClickMethod, userData, id=-1):
        wx.StaticText.__init__(self, parent, id, text)
        self.onClickMethod = onClickMethod
        self.userData = userData
        self.Bind(wx.EVT_LEFT_DOWN, self.onClick)
        
    def onClick(self, event):
        self.onClickMethod(self.userData)
        

class BookmarksBar(RectangularChild):
    """
      Under construction
    """
    def __init__(self, *arguments, **keywords):
        super (BookmarksBar, self).__init__ (*arguments, **keywords)
        self.bookmarksPath = None

    def renderOneBlock(self, parent, parentWindow):
        panel = wx.Panel(parentWindow, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))
        self.addBookmarks(panel, sizer)
        panel.SetSizerAndFit(sizer)
        self.parentBlock.addToContainer(parent, panel,
                                        self.stretchFactor,
                                        self.Calculate_wxFlag(),
                                        self.Calculate_wxBorder())
        self.showOrHideBookmarksBar(panel)
        return panel, None, None
    
    def addBookmarks(self, parent, sizer):
        for child in self.bookmarksPath.children:
            self.addBookmark(parent, sizer, child.getItemDisplayName(), child.GetPath())
        
    def addBookmark(self, parent, sizer, title, path):
        sizer.Add((10, 0), 0, wx.EXPAND)
        bookmark = wxBookmark(parent, title, self.bookmarkPressed, path)
        sizer.Add(bookmark, 0)
        sizer.Add((10, 0), 0, wx.EXPAND)
        
    def bookmarkPressed(self, text):
        item = Node.GetItemFromPath(text, '//parcels/OSAF/views/main/URLRoot')
        """
          If a parcel takes the focus upon a SelectionChanged event, we must take the focus back
        temporarily so that the sidebar gets the event.  This is a temporary solution for Bug#1249.
        """
        Globals.wxApplication.mainFrame.SetFocus()
        self.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                   {'item':item})
        
    def OnViewBookmarksBarEvent(self, notification):
        self.open = not self.open
        self.showOrHideBookmarksBar(Globals.association[self.itsUUID])
        
    def showOrHideBookmarksBar(self, bookmarksBar):
        if bookmarksBar.IsShown() != self.open:
            bookmarksBar.Show(self.open)
            parentWindow = Globals.association[self.parentBlock.itsUUID]
            if self.open:
                self.parentBlock.addToContainer(parentWindow.GetSizer(), bookmarksBar, 
                                                self.stretchFactor,
                                                self.Calculate_wxFlag(),
                                                self.Calculate_wxBorder(), 
                                                False)
            else:
                self.parentBlock.removeFromContainer(parentWindow, bookmarksBar, False)
            self.parentBlock.handleChildren(parentWindow)
        
    def OnViewBookmarksBarEventUpdateUI(self, notification):
        notification.data['Check'] = self.open
        

class NavigationBar(Toolbar):
    """
      Under construction
    """
    def renderOneBlock(self, parent, parentWindow):
        self.history = []
        self.future = []

        returnArguments = Toolbar.renderOneBlock(self, parent, parentWindow)
        self.showOrHideNavigationBar()
        return returnArguments
    
    def toolPressed(self, event):
        tool = Block.wxIDToObject(event.GetId())
        if tool.itsName == 'BackButton':
            self.GoBack()
        elif tool.itsName == 'ForwardButton':
            self.GoForward()

    def toolEnterPressed(self, event):
        tool = Globals.wxApplication.mainFrame.FindWindowById(event.GetId())
        url = tool.GetValue()
        try:
            item = Node.GetItemFromPath(url, '//parcels/OSAF/views/main/URLRoot')
        except BadURL:
            dialog = wx.MessageDialog(None, 'The url "' + str(url) + '" does not exist', 
                                     'Chandler',
                                     style=wx.OK|wx.CENTRE)
            dialog.ShowModal()
        else:
            self.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                       {'item':item})
        
    def OnViewNavigationBarEvent(self, notification):
        self.open = not self.open
        self.showOrHideNavigationBar()
        
    def showOrHideNavigationBar(self):
        frame = Globals.wxApplication.mainFrame
        navigationBar = frame.GetToolBar()
        if navigationBar.IsShown() != self.open:
            navigationBar.Show(self.open)
            frame.Layout()
        
    def OnViewNavigationBarEventUpdateUI(self, notification):
        notification.data['Check'] = self.open

    def GoBack(self):
        if len(self.history) > 1:
            currentLocation = self.history.pop()
            self.future.append(currentLocation)
            """
              If a parcel takes the focus upon a SelectionChanged event, we must take the focus back
            temporarily so that the sidebar gets the event.  This is a temporary solution for Bug#1249.
            """
            Globals.wxApplication.mainFrame.SetFocus()
            self.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                       {'item':self.history[-1]})
    
    def GoForward(self):
        if len(self.future) > 0:
            newLocation = self.future.pop()
            self.history.append(newLocation)
            """
              If a parcel takes the focus upon a SelectionChanged event, we must take the focus back
            temporarily so that the sidebar gets the event.  This is a temporary solution for Bug#1249.
            """
            Globals.wxApplication.mainFrame.SetFocus()
            self.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                       {'item':newLocation})

    def OnSelectionChangedEvent (self, notification):
        item = notification.data['item']
        try:
            path = item.GetPath()
        except AttributeError:
            return

        if len(self.history) == 0 or self.history[-1] != item:
            self.history.append(item)
        urlBox = Globals.repository.find ('//parcels/OSAF/views/main/URLBox')
        wxURLBox = Globals.association[urlBox.itsUUID]
        wxURLBox.SetValue(path)
        
        
class ChandlerStatusBar(StatusBar):
    def renderOneBlock(self, parent, parentWindow):
        returnArguments = StatusBar.renderOneBlock(self, parent, parentWindow)
        self.showOrHideStatusBar()
        return returnArguments
    
    def OnViewStatusBarEvent(self, notification):
        self.open = not self.open
        self.showOrHideStatusBar()

    def showOrHideStatusBar(self):
        frame = Globals.wxApplication.mainFrame
        statusBar = frame.GetStatusBar()
        if statusBar.IsShown() != self.open:
            statusBar.Show(self.open)
            frame.Layout()
            
    def OnViewStatusBarEventUpdateUI(self, notification):
        notification.data['Check'] = self.open
        
        
