import application.Globals as Globals
from repository.item.Item import Item
from OSAF.framework.notifications.schema.Event import Event
from wxPython.wx import *
import logging


class Block(Item):
    def __init__(self, *arguments, **keywords):
        super (Block, self).__init__ (*arguments, **keywords)
        """
          We currently have to initialize this data here because of
        limitations of our repository/XML parcel. We should fix
        these limitations so we can initialize them in the parcel
        XML -- DJA
        """
        self.childrenBlocks = []
        self.parentBlock = None
        self.styles = []

    def Post (self, event, args):
        """
          Events that are posted by the block pass along the block
        that sent it.
        """
        args['sender'] = self
        event.Post (args)

    def render (self, parent, parentWindow):
        """
          ContainerChild overrides render to recursively call
        renderOneBlock on a tree of Blocks.
        """
        pass

    def renderOneBlock(self, parent, parentWindow):
        """
          You should usually override renderOneBlock in your Block subclass
        to create a platform specific counterpart for the block. The three
        objects returned are:
         - The platform specific counterpart created, e.g. wxPanel
         - The platform specific counterpart for the Block's parent block
         - The platform specific parent of the counterpart created, e.g.
           wxPanel's platform specific parent.
          We need to occasionally return all these arguments because our
        blocks containers are included in our hierarchy of Blocks, where as
        wxWindows sizers are not included in their hiearchy of windows.
        """
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
        look up the UUID of a block given it's Id -- DJA
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


class ContainerChild(Block):
    def render (self, parent, parentWindow):
        (window, parent, parentWindow) = self.renderOneBlock (parent, parentWindow)
        """
          Store the wxWindows version of the object in the association, so
        given the block we can find the associated wxWindows object.
        """
        if window:
            UUID = self.getUUID()
            """
              Currently not all wxWindows counterpart objects have a __del__
            funcation to removed themselves from the association when they
            are deleted. However, they should. Bug #1177. For now I'll comment
            out the assert and log the bugs

            assert not Globals.association.has_key(UUID)
            """
            if __debug__ and Globals.association.has_key(UUID):
                Globals.repository.find (UUID).getItemPath()
                logging.warn("Bug #1177: item %s doesn't remove it's counterpart from the association",
                             str (Globals.repository.find (UUID).getItemPath()))
            Globals.association[UUID] = window
            window.counterpartUUID = UUID
            """
              After the blocks are wired up, give the window a chance
            to synchronize itself to any persistent state.
            """
            try:
                window.SynchronizeFramework()
            except AttributeError:
                pass
            for child in self.childrenBlocks:
                child.render (parent, parentWindow)
            self.handleChildren(window)
        return window, parent, parentWindow
                
    def getParentBlock(self, parentWindow):
        if self.parentBlock:
            return self.parentBlock
        return Globals.repository.find (parentWindow.counterpartUUID)

    def addToContainer(self, parent, child, id, flag, border):
        pass
    
    def removeFromContainer(self, parent, child):
        pass
    
    def handleChildren(self, window):
        pass

    
class RectangularChild(ContainerChild):
    def Calculate_wxFlag (self):
        if self.alignmentEnum == 'grow':
            flag = wxGROW
        elif self.alignmentEnum == 'growConstrainAspectRatio':
            flag = wxSHAPED
        elif self.alignmentEnum == 'alignCenter':
            flag = wxALIGN_CENTER
        elif self.alignmentEnum == 'alignTopCenter':
            flag = wxALIGN_TOP
        elif self.alignmentEnum == 'alignMiddleLeft':
            flag = wxALIGN_LEFT
        elif self.alignmentEnum == 'alignBottomCenter':
            flag = wxALIGN_BOTTOM
        elif self.alignmentEnum == 'alignMiddleRight':
            flag = wxALIGN_RIGHT
        elif self.alignmentEnum == 'alignTopLeft':
            flag = wxALIGN_TOP | wxALIGN_LEFT
        elif self.alignmentEnum == 'alignTopRight':
            flag = wxALIGN_TOP | wxALIGN_RIGHT
        elif self.alignmentEnum == 'alignBottomLeft':
            flag = wxALIGN_BOTTOM | wxALIGN_LEFT
        elif self.alignmentEnum == 'alignBottomRight':
            flag = wxALIGN_BOTTOM | wxALIGN_RIGHT
        return flag

    def Calculate_wxBorder (self):
        border = 0
        spacerRequired = False
        for edge in (self.border.top, self.border.left, self.border.bottom, self.border.right):
            if edge != 0:
                if border == 0:
                    border = edge
                elif border != edge:
                    spacerRequired = False
                    break
        """
          wxWindows sizers only allow borders with the same width, or no width, however
        blocks allow borders of different sizes for each of the 4 edges, so we need to
        simulate this by adding spacers. I'm postponing this case for Jed to finish, and
        until then an assert will catch this case. DJA
        """
        assert not spacerRequired
        
        return int (border)


class BlockEvent(Event):
    def __init__(self, *arguments, **keywords):
        super (BlockEvent, self).__init__ (*arguments, **keywords)
        self.dispatchToBlock = None


class ChoiceEvent(BlockEvent):
    pass

