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

    def navbarGoBack(self, event):
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
    
    def navbarGoBackUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarGoForward(self, event):
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

    def navbarGoForwardUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarSync(self, notification):
        # Handler for Sync tool bar button
        pass
    
    def navbarSyncUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarReply(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarReplyUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarDiscuss(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarDiscussUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarForward(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarForwardUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarDelete(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarDeleteUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarJunk(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarJunkUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarFonts(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarFontsUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarSearch(self, notification):
        # placeholder for the Search Text Widget in the nav bar
        pass
    
    def navbarSearchUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def navbarPrint(self, notification):
        # placeholder for a nav bar button
        pass
    
    def navbarPrintUpdateUI (self, notification):
        notification.data ['Enable'] = False

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
        
