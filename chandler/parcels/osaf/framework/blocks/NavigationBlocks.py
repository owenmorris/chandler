__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from ControlBlocks import *
from repository.util.UUID import UUID
from wxPython.wx import *


class Sidebar(Tree):
    def GetTreeData (self, node):
        item = node.GetData()
        if item:
            for child in item.children:
                node.AddChildNode (child,
                                   [self.GetTreeDataName (child)],
                                   len(child.children) != 0)
        else:
            node.AddRootNode (self.rootPath, [""], len(self.rootPath.children) != 0)
            
    def GetTreeDataName (self, item):
        return item.getItemDisplayName()

    def OnSelectionChangedEvent (self, notification):
        try:
            path = notification.GetData()['item'].GetPath()
        except AttributeError:
            return
        wxTreeWindow = Globals.association[self.getUUID()]
        wxTreeWindow.GoToPath (path)


class NavigationBar(Toolbar):
    def renderOneBlock(self, parent, parentWindow):
        self.history = []
        self.future = []
        toolbar = wxToolBar(Globals.wxApplication.mainFrame, -1)
        Globals.wxApplication.mainFrame.SetToolBar(toolbar)
        return toolbar, None, None
                
    def toolPressed(self, event):
        tool = Block.wxIDToObject(event.GetId())
        if tool.getItemName() == 'BackButton':
            self.GoBack()
        elif tool.getItemName() == 'ForwardButton':
            self.GoForward()

    def tooEnterPressed(self, event):
        tool = Block.wxIDToObject(event.GetId())
        
    def GoBack(self):
        if len(self.history) > 1:
            currentLocation = self.history.pop()
            self.future.append(currentLocation)
            self.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                       {'item':self.history[-1]})
    
    def GoForward(self):
        if len(self.future) > 0:
            newLocation = self.future.pop()
            self.history.append(newLocation)
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
        wxURLBox = Globals.association[urlBox.getUUID()]
        wxURLBox.SetValue(path)
        
        
class BookmarksBar(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):        
        return None, None, None

    def bookmarkPressed(self, event):
        pass
