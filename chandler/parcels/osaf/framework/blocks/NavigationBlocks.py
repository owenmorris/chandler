__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from ControlBlocks import *
from Node import *
import wx


class wxBookmark(wx.StaticText):
    """
      Under construction
    """
    def __init__(self, parent, text, onClickMethod, userData, id=-1):
        super (wxBookmark, self).__init__ (parent, id, text)
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

    def instantiateWidget(self):
        panelWidget = wxRectangularChild (self.parentBlock.widget, -1)
        sizer = wx.BoxSizer (wx.HORIZONTAL)
        sizer.SetMinSize ((self.minimumSize.width, self.minimumSize.height))
        self.addBookmarks (panelWidget, sizer)
        panelWidget.SetSizerAndFit (sizer)
        return panelWidget
    
    def addBookmarks(self, parent, sizer):
        for child in self.bookmarksPath.children:
            self.addBookmark(parent, sizer, child.getItemDisplayName(), child.GetPath())
        
    def addBookmark(self, parent, sizer, title, path):
        sizer.Add((10, 0), 0, wx.EXPAND)
        bookmark = wxBookmark(parent, title, self.bookmarkPressed, path)
        sizer.Add(bookmark, 0)
        sizer.Add((10, 0), 0, wx.EXPAND)
        
    def bookmarkPressed(self, text):
        item = Node.GetItemFromPath(text, '//parcels/osaf/views/main/URLRoot')
        """
          If a parcel takes the focus upon a SelectionChanged event, we must take the focus back
        temporarily so that the sidebar gets the event.  This is a temporary solution for Bug#1249.
        """
        Globals.wxApplication.mainFrame.SetFocus()
        self.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                   {'item':item})
        

class NavigationBar(Toolbar):
    """
      Under construction
    """
    def instantiateWidget(self):
        self.history = []
        self.future = []

        navigationBar = Toolbar.instantiateWidget(self)
        self.showOrHideNavigationBar()
        return navigationBar
    
    def toolPressed(self, event):
        tool = Block.widgetIDToBlock(event.GetId())
        if tool.itsName == 'BackButton':
            self.GoBack()
        elif tool.itsName == 'ForwardButton':
            self.GoForward()

    def toolEnterPressed(self, event):
        tool = Globals.wxApplication.mainFrame.FindWindowById(event.GetId())
        url = tool.GetValue()
        try:
            item = Node.GetItemFromPath(url, '//parcels/osaf/views/main/URLRoot')
        except BadURL:
            dialog = wx.MessageDialog(None, 'The url "' + str(url) + '" does not exist', 
                                     'Chandler',
                                     style=wx.OK|wx.CENTRE)
            dialog.ShowModal()
        else:
            self.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
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
            self.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
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
            self.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                       {'item':newLocation})

    def OnSelectionChangedEvent (self, notification):
        item = notification.data['item']
        try:
            path = item.GetPath()
        except AttributeError:
            return

        if len(self.history) == 0 or self.history[-1] != item:
            self.history.append(item)
        urlBox = Globals.repository.findPath('//parcels/osaf/views/main/URLBox')
        urlBox.widget.SetValue(path)
        
