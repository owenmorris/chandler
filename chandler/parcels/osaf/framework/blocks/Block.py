
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


    def renderOneBlock(self, parent, parentWindow):
        return None, None, None


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
                try:
                    member = getattr (controller, methodName)
                    member (notification)
                    break
                except AttributeError:
                    controller = controller.parentBlock.parentBlock
        elif __debug__:
            assert (False)


    def getFocusBlock (self):
        focusWindow = wxWindow_FindFocus()
        try:
            UUID = focusWindow.counterpartUUID
        except AttributeError:
            return Globals.topController
        return (Globals.repository.find (UUID))

    
    def onSetFocus (self):
        """
          Cruise up the parent hierarchy looking for the parent of the first
        menu or menuItem. If it's not the same as the last time the focus
        changed then we need to rebuild the menus.
        """
        from OSAF.framework.blocks.MenuBlocks import Menu, MenuItem

        block = self.getFocusBlock()
        while (block):
            for child in block.childrenBlocks:
                if isinstance (child, Menu) or isinstance (child, MenuItem):
                    parent = child.parentBlock
                    if True or parent != Globals.wxApplication.menuParent:
                        Globals.wxApplication.menuParent = parent
                        Menu.rebuildMenus(parent)
                        return
            block = block.parentBlock

    IdToUUID = []               # A list mapping Ids to UUIDS
    UUIDtoIds = {}              # A dictionary mapping UUIDS to Ids

    MINIMUM_WX_ID = 2500
    MAXIMUM_WX_ID = 4999

    def wxIDToObject (theClass, wxID):
        """
          Given a wxWindows Id, returns the corresponding Chandler block
        """
        return Globals.repository.find (theClass.IdToUUID [wxID - theClass.MINIMUM_WX_ID])
 
    wxIDToObject = classmethod (wxIDToObject)
    

    def getwxID (theClass, object):
        """
          wxWindows needs a integer for a id. Commands between
        wxID_LOWEST and wxID_HIGHEST are reserved. wxPython doesn't export
        wxID_LOWEST and wxID_HIGHEST, which are 4999 and 5999 respectively.
        Passing -1 for an ID will allocate a new ID starting with 0. So
        I will use the range starting at 2500 for our events.
          I'll store the ID for an event in the association and the
        wxApplication keeps a list, named commandIDs with allows us to
        look up the UUID of a block given it's Id
        """
        UUID = object.getUUID()
        try:
            id = Block.UUIDtoIds [UUID]
        except KeyError:
            length = len (Block.IdToUUID)
            Block.IdToUUID.append (UUID)
            id = length + Block.MINIMUM_WX_ID
            assert (id <= Block.MAXIMUM_WX_ID)
            assert not Block.UUIDtoIds.has_key (UUID)
            Block.UUIDtoIds [UUID] = id
        return id
    getwxID = classmethod (getwxID)

    
class BlockEvent(Event):
    pass

