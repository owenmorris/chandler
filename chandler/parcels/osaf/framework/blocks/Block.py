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
        self.styles = []

    def Post (self, event, args):
        """
          Events that are posted by the block pass along the block
        that sent it.
        """
        args['sender'] = self
        event.Post (args)

    def render (self):
        try:
            instantiateWidgetMethod = getattr (self, "instantiateWidget")
        except AttributeError:
            return
        else:
            oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
            Globals.wxApplication.ignoreSynchronizeWidget = True
            try:
                widget = instantiateWidgetMethod()
            finally:
                Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget
            """
              Store a non persistent pointer to the widget in the block and pin the block
            to keep it in memory. Store a pointer to the block in the widget. Undo all this
            when the widget is destroyed.
            """

            if widget:
                self.setPinned()
                self.widget = widget
                widget.blockItem = self
                """
                  For those widgets with contents, we need to subscribe to notice changes
                to items in the contents.
                """
                try:
                    self.contents.subscribeWidgetToChanges (widget)
                except AttributeError:
                    pass
                    
                """
                  After the blocks are wired up, give the window a chance
                to synchronize itself to any persistent state.
                """
                for child in self.childrenBlocks:
                    child.render()
                self.synchronizeWidget()

    IdToUUID = []               # A list mapping Ids to UUIDS
    UUIDtoIds = {}              # A dictionary mapping UUIDS to Ids

    MINIMUM_WX_ID = 2500
    MAXIMUM_WX_ID = 4999

    def onDestroyWidget (self):
        """
          Called just before a widget is destroyed. It is the opposite of
        instantiateWidget.
        """
        try:
            self.contents.unSubscribeWidgetToChanges (self.widget)
        except AttributeError:
            pass
        delattr (self, 'widget')
        self.setPinned (False)
 
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
          Use IdToUUID to lookup the Id for a event's UUID. Use UUIDtoIds to
        lookup the UUID of a block that corresponds to an event id -- DJA
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
            method = getattr (self.widget, 'wxSynchronizeWidget')
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
    pass

    
class wxRectangularChild (wx.Panel):
    def __init__(self, *arguments, **keywords):
        super (wxRectangularChild, self).__init__ (*arguments, **keywords)

    def wxSynchronizeWidget(self):
        if self.blockItem.open != self.IsShown():
            self.Show (block.open)

        
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

