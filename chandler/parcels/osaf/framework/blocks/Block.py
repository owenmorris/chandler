__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from osaf.framework.notifications.schema.Event import Event
import wx
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
        instantiateWidget on a tree of Blocks.
        """
        pass

    def instantiateWidget(self, parent, parentWindow):
        """
          You should usually override instantiateWidget in your Block subclass
        to create a platform specific widget for the block. The three
        objects returned are:
         - The platform specific widget created, e.g. wx.Panel
         - The platform specific widget for the Block's parent block
         - The platform specific parent of the widget created, e.g.
           wx.Panel's platform specific parent.
          We need to occasionally return all these arguments because our
        blocks containers are included in our hierarchy of Blocks, where as
        wxWindows sizers are not included in their hiearchy of windows.
        """
        return None, None, None

    IdToUUID = []               # A list mapping Ids to UUIDS
    UUIDtoIds = {}              # A dictionary mapping UUIDS to Ids

    MINIMUM_WX_ID = 2500
    MAXIMUM_WX_ID = 4999

    def widgetIDToBlock (theClass, wxID):
        """
          Given a wxWindows Id, returns the corresponding Chandler block
        """
        return Globals.repository.find (theClass.IdToUUID [wxID - theClass.MINIMUM_WX_ID])
 
    widgetIDToBlock = classmethod (widgetIDToBlock)

    def getWidgetID (theClass, object):
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
        UUID = object.itsUUID
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
    getWidgetID = classmethod (getWidgetID)

    def update (self):
        try:
            theWindow = Globals.association[self.itsUUID]
        except KeyError:
            pass
        else:
            if hasattr(theWindow, "scheduleUpdate"):
                theWindow.scheduleUpdate = True

    def OnShowHide(self, notification):
        self.open = not self.open
        self.synchronizeWidget()
        self.parentBlock.synchronizeWidget()


    def OnShowHideUpdateUI(self, notification):
        notification.data['Check'] = self.open


    def synchronizeWidget (self):
        """
          synchronizeWidget's job is to make the wxWidget match the state of
        the data persisted in the block. There's a tricky problem that occurs: Often
        we add a handler to the wxWidget of a block to, for example, get called
        when the user changes the selection, which we use to update the block's selection
        and post a selection changed notification. It turns out that while we are in
        synchronizeWidget, changes to the wxWidget cause these handlers to be
        called, and in this case we don't want to post a notification. So we wrap calls
        to synchronizeWidget and set a flag indicating that we're inside
        synchronizeWidget so the handlers can tell when not to post selection
        changed events. We use this flag in other similar situations, for example,
        during shutdown to ignore events caused by the framework tearing down wxWidgets.
        """
        try:
            theWindow = Globals.association[self.itsUUID]
            method = getattr (theWindow, 'wxSynchronizeWidget')
        except AttributeError:
            pass
        else:
            if not Globals.wxApplication.ignoreSynchronizeWidget:
                oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
                Globals.wxApplication.ignoreSynchronizeWidget = True
                try:
                    method()
                finally:
                    Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget


class ContainerChild(Block):
    def render (self, parent, parentWindow):
        oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
        Globals.wxApplication.ignoreSynchronizeWidget = True
        try:
            (widget, parent, parentWindow) = self.instantiateWidget (parent, parentWindow)
        finally:
            Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget
        """
          Store the wxWindows version of the object in the association, so
        given the block we can find the associated wxWindows object.
        """
        if widget:
            UUID = self.itsUUID
            """
              Currently not all wxWidget objects have a __del__
            funcation to removed themselves from the association when they
            are deleted. However, they should. Bug #1177. For now I'll comment
            out the assert and log the bugs

            assert not Globals.association.has_key(UUID)
            """
            if __debug__ and Globals.association.has_key(UUID):
                Globals.repository.find (UUID).itsPath
                logging.warn("Bug #1177: item %s doesn't remove it's widget from the association",
                             str (Globals.repository.find (UUID).itsPath))
            Globals.association[UUID] = widget
            widget.blockUUID = UUID
            """
              After the blocks are wired up, give the window a chance
            to synchronize itself to any persistent state.
            """
            parent = widget
            parentWindow = widget
            for child in self.childrenBlocks:
                child.render (parent, parentWindow)
            self.synchronizeWidget()
        return widget
                
    def addToContainer(self, parent, child, id, flag, border):
        pass
    
    def removeFromContainer(self, parent, child):
        pass

    
class wxRectangularChild (wx.Panel):
    def __init__(self, *arguments, **keywords):
        super (wxRectangularChild, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def wxSynchronizeWidget(self):
        block = Globals.repository.find (self.blockUUID)
        if block.open != self.IsShown():
            self.Show (block.open)
            parentWidget = Globals.association [block.parentBlock.itsUUID]
            parentSizer = parentWidget.GetSizer()
            if parentSizer:
                if self.IsShown():
                    parentSizer.Show (self)
                else:
                    parentSizer.Hide (self)
        if block.open:
            self.SetSize ((block.size.width, block.size.height))
            self.Layout()

    def OnSize(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, 
        which will cause the parent class to get a crack at the event.
        """
        event.Skip()
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            block = Globals.repository.find (self.blockUUID)
            block.size.width = event.GetSize().x
            block.size.height = event.GetSize().y
            block.setDirty()   # Temporary repository hack -- DJA


class RectangularChild(ContainerChild):
    def Calculate_wxFlag (self):
        if self.alignmentEnum == 'grow':
            flag = wx.GROW
        elif self.alignmentEnum == 'growConstrainAspectRatio':
            flag = wx.SHAPED
        elif self.alignmentEnum == 'alignCenter':
            flag = wx.ALIGN_CENTER
        elif self.alignmentEnum == 'alignTopCenter':
            flag = wx.ALIGN_TOP
        elif self.alignmentEnum == 'alignMiddleLeft':
            flag = wx.ALIGN_LEFT
        elif self.alignmentEnum == 'alignBottomCenter':
            flag = wx.ALIGN_BOTTOM
        elif self.alignmentEnum == 'alignMiddleRight':
            flag = wx.ALIGN_RIGHT
        elif self.alignmentEnum == 'alignTopLeft':
            flag = wx.ALIGN_TOP | wx.ALIGN_LEFT
        elif self.alignmentEnum == 'alignTopRight':
            flag = wx.ALIGN_TOP | wx.ALIGN_RIGHT
        elif self.alignmentEnum == 'alignBottomLeft':
            flag = wx.ALIGN_BOTTOM | wx.ALIGN_LEFT
        elif self.alignmentEnum == 'alignBottomRight':
            flag = wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT
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

