__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from ControlBlocks import *
from Node import *
import DynamicContainerBlocks as DynamicContainerBlocks
import wx


class NavigationBar(DynamicContainerBlocks.Toolbar):
    """
      Under construction
    """
    def ensureHistory(self):
        try:
            history = self.history
        except AttributeError:
            self.history = []
            self.future = []

    def onViewNavigationBarEvent(self, notification):
        self.isShown = not self.isShown
        self.showOrHideNavigationBar()
        
    def showOrHideNavigationBar(self):
        frame = Globals.wxApplication.mainFrame
        navigationBar = self.widget
        if navigationBar.IsShown() != self.isShown:
            navigationBar.Show(self.isShown)
            frame.Layout()
        
    def onViewNavigationBarEventUpdateUI(self, notification):
        notification.data['Check'] = self.isShown

    def navbarBack(self, event):
        self.ensureHistory()
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
    
    def navbarForward(self, event):
        self.ensureHistory()
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

    def navbarSync(self, event):
        # Handler for Sync tool bar button
        pass
    
    def navbarNew(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarReply(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarDiscuss(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarForward(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarDelete(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarJunk(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarFonts(self, event):
        # placeholder for a nav bar button
        pass
    
    def navbarSearch(self, event):
        # placeholder for the Search Text Widget in the nav bar
        pass
    
    def onSelectionChangedEvent (self, notification):
        item = notification.data['item']
        try:
            path = item.GetPath()
        except AttributeError:
            return

        self.ensureHistory()
        if len(self.history) == 0 or self.history[-1] != item:
            self.history.append(item)
        urlBox = Globals.repository.findPath('//parcels/osaf/views/main/URLBox')
        # DLDTBD - clean up all this NaviationBar code
        # urlBox.widget.SetValue(path)
        
