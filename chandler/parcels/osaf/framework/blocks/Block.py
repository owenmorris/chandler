
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

    def dispatchEvent (self, event):
        window = wxWindow_FindFocus()
        while not hasattr (window, "counterpartUUID"):
            window = window.GetParent()
        focusWindow = Globals.repository.find (window.counterpartUUID)
        controller = focusWindow.findController()
        assert (controller)

        methodName = 'on' + event.getItemName()
        while (controller):
            if hasattr (controller, methodName):
                member = getattr (controller, methodName)
                member (event)
                break
            else:
                controller = controller.GetParent().GetParent()
        

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
