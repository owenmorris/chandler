
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
 

    def Post (self, event, args):
        args['sender'] = self
        event.Post (args)


    def render (self, parent, parentWindow):
        pass


    def renderOneBlock(self, parent, parentWindow):
        return None, None, None


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
    def __init__(self, *arguments, **keywords):
        super (BlockEvent, self).__init__ (*arguments, **keywords)
        self.dispatchToBlock = None


class ChoiceEvent(BlockEvent):
    pass

