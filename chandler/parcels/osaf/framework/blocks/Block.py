
import application.Globals as Globals
from repository.item.Item import Item
from OSAF.framework.notifications.schema.Event import Event
from wxPython.wx import *


class Block(Item):

    def __init__(self, *arguments, **keywords):
        super (Block, self).__init__ (*arguments, **keywords)
        self.childrenBlocks = []
        self.parentBlock = None
        self.styles = []
 

    def render (self, parent, parentWindow):
        pass


    def findController (self):
        from OSAF.framework.blocks.Controller import Controller
        block = self

        while (block):
            for child in block.childrenBlocks:
                if isinstance (child, Controller):
                    return child
            block = block.parentBlock
            
        return None


    def dispatchEvent (self, notification):
        
        def broadcast (block, methodName, event):
            """
              Call method named methodName on every block and it's children
            who implements it
            """
            if hasattr (block, methodName):
                member = getattr (block, methodName)
                member (event)
            for child in block.childrenBlocks:
                broadcast (child, methodName, event)
            
        event = notification.data['event']
        """
          Find the controller for the window with the focus
        """
        controller = self.getFocusBlock().findController()
        """
          Construct method name based upon the name of the event.
        """
        methodName = 'on_' + event.name.replace ('/', '_')
        if notification.data['type'] == 'UpdateUI':
            methodName += '_UpdateUI'
        
        if event.dispatchEnum == 'Broadcast':
            broadcast (controller.parentBlock, methodName, event)
        elif event.dispatchEnum == 'Controller':
            """
              Bubble the event up through all the containing controllers
            """
            while (controller):
                if hasattr (controller, methodName):
                    member = getattr (controller, methodName)
                    member (notification)
                    break
                else:
                    controller = controller.GetParent().GetParent()
        elif __debug__:
            assert (False)


    def getFocusBlock (self):
        focusWindow = wxWindow_FindFocus()
        try:
            UUID = focusWindow.counterpartUUID
        except AttributeError:
            return Globals.topController
        return (Globals.repository.find (UUID))

    
    def rebuildMenus (self):
        
        def buildMenuList (block, data):
            parent = block.parentBlock
            if (parent):
                buildMenuList (parent, data)

            """
              Initialize data if it's empty
            """
            if len (data) == 0:
                data['menuList'] = []
                data['firstMenu'] = True
                data['nameIndex'] = {}
                
            nameIndex = data['nameIndex']
            firstMenu = data['firstMenu']
            list = []
            for child in block.childrenBlocks:
                if isinstance (child, Menu) or isinstance (child, MenuItem):
                    name = child.getItemName()
                    nameIndex[name] = child
                    list.append (name)
            if len(list) != 0:
                data['menuList'].append (list)
            
            data = {}
            buildMenuList (self.getFocusBlock(), data)
        


    def onSetFocus (self):
        """
          Cruise up the parent hierarchy looking for the parent of the first
        menu or menuItem. If it's not the same as the last time the focus
        changed then we need to rebuild all the menus.
        """
        from OSAF.framework.blocks.ContainerBlocks import Menu
        from OSAF.framework.blocks.ContainerBlocks import MenuItem

        block = self.getFocusBlock()
        while (block):
            for child in block.childrenBlocks:
                if isinstance (child, Menu) or isinstance (child, MenuItem):
                    parent = child.parentBlock
                    if parent != Globals.wxApplication.menuParent:
                        Globals.wxApplication.menuParent = parent
                        self.rebuildMenus(parent)
                        return
            block = block.parentBlock


class BlockEvent(Event):

    commandIDs = []
    MINIMUM_WX_ID = 2500
    MAXIMUM_WX_ID = 4999


    def wxIDToEvent (theClass, wxID):
        """
          Given a wxWindows commandID, returns the corresponding
        Chandler event object
        """
        return Globals.repository.find (theClass.commandIDs [wxID - theClass.MINIMUM_WX_ID])
 
    wxIDToEvent = classmethod (wxIDToEvent)
    

    def getwxID (self):
        """
          wxWindows needs a integer for a command id. Commands between
        wxID_LOWEST and wxID_HIGHEST are reserved. wxPython doesn't export
        wxID_LOWEST and wxID_HIGHEST, which are 4999 and 5999 respectively.
        Passing -1 for an ID will allocate a new ID starting with 0. So
        I will use the range starting at 2500 for our events.
          I'll store the ID for an event in the association and the
        wxApplication keeps a list, named commandIDs with allows us to
        look up the UUID of an event given it's ID
        """
        UUID = self.getUUID()
        try:
            id = Globals.association [UUID]
        except KeyError:
            length = len (BlockEvent.commandIDs)
            BlockEvent.commandIDs.append (UUID)
            id = length + BlockEvent.MINIMUM_WX_ID
            assert (id <= BlockEvent.MAXIMUM_WX_ID)
            assert not Globals.association.has_key (UUID)
            Globals.association [UUID] = id
        return id
