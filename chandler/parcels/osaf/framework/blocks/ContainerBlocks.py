#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


__parcel__ = "osaf.framework.blocks"

from Block import (
    Block, RectangularChild, wxRectangularChild,
    WithoutSynchronizeWidget, IgnoreSynchronizeWidget
)
from osaf.pim.structs import PositionType, SizeType
import MenusAndToolbars
from application import schema
import wx
#import util.autolog

class orientationEnumType(schema.Enumeration):
    values = "Horizontal", "Vertical"

class wxBoxContainer (wxRectangularChild):
    #import util.autolog; __metaclass__ = util.autolog.LogTheMethods; logMatch = "^On.*"
    def wxSynchronizeWidget(self):
        super (wxBoxContainer, self).wxSynchronizeWidget ()

        colorStyle = getattr (self, 'colorStyle', None)
        if colorStyle is not None:
            self.SetBackgroundColour(colorStyle.backgroundColor.wxColor())
            self.SetForegroundColour(colorStyle.foregroundColor.wxColor())

        sizer = self.GetSizer()
        if not sizer:
            sizer = wx.BoxSizer ({'Horizontal': wx.HORIZONTAL,
                                'Vertical': wx.VERTICAL} [self.blockItem.orientationEnum])
            self.SetSizer (sizer)
        sizer.Clear()
        for childBlock in self.blockItem.childBlocks:
            if isinstance (childBlock, RectangularChild):
                widget = getattr (childBlock, "widget", None)
                if widget is not None:
                    sizer.Add (childBlock.widget,
                               childBlock.stretchFactor, 
                               wxRectangularChild.CalculateWXFlag(childBlock), 
                               wxRectangularChild.CalculateWXBorder(childBlock))
        sizer.Layout()
        IgnoreSynchronizeWidget(False, self.Layout)

    @classmethod
    def CalculateWXStyle(theClass, block):
        style = wx.TAB_TRAVERSAL
        if Block.showBorders:
            style |= wx.SIMPLE_BORDER
        else:
            style |= wx.NO_BORDER
        return style


class BoxContainer(RectangularChild):

    orientationEnum = schema.One(
        orientationEnumType, initialValue = 'Horizontal',
    )
    bufferedDraw = schema.One(schema.Boolean, defaultValue=False)

    def instantiateWidget (self):
        widget = wxBoxContainer (self.parentBlock.widget,
                                 self.getWidgetID(),
                                 wx.DefaultPosition,
                                 wx.DefaultSize,
                                 style=wxBoxContainer.CalculateWXStyle(self))
        if self.bufferedDraw:
            widget.SetExtraStyle (wx.WS_EX_BUFFERED_DRAW)
        return widget

    
class wxScrolledContainer (wx.ScrolledWindow):
    def wxSynchronizeWidget(self):
        if self.blockItem.isShown:
            sizer = self.GetSizer()
            sizer.Clear()
            for childBlock in self.blockItem.childBlocks:
                if childBlock.isShown and isinstance (childBlock, RectangularChild):
                    sizer.Add (childBlock.widget,
                               childBlock.stretchFactor, 
                               wxRectangularChild.CalculateWXFlag(childBlock), 
                               wxRectangularChild.CalculateWXBorder(childBlock))
            self.Layout()
            self.SetScrollRate(0,1)

        
class ScrolledContainer(BoxContainer):
    def instantiateWidget (self):
        return wxScrolledContainer (self.parentBlock.widget, self.getWidgetID())    

#from util.autolog import indentlog
class wxSplitterWindow(wx.SplitterWindow):
    #import util.autolog;  __metaclass__ = util.autolog.LogTheMethods
    def __init__(self, *arguments, **keywords):
        super (wxSplitterWindow, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,
                  self.OnSplitChanged,
                  id=self.GetId())
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING,
                  self.OnSplitChanging,
                  id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Setting minimum pane size prevents unsplitting a window by double-clicking
        self.SetMinimumPaneSize(7) #weird number to help debug the weird sizing bug 3497

    @WithoutSynchronizeWidget
    def OnSize(self, event):
        newSize = self.GetSize()
        blockItem = self.blockItem
        oldSize = blockItem.size
        blockItem.size = SizeType (newSize.width, newSize.height)
        
        if blockItem.orientationEnum == "Horizontal":
            distance = newSize.height
            needsAdjust = oldSize.height != newSize.height
        else:
            distance = newSize.width
            needsAdjust = oldSize.width != newSize.width
            
        if needsAdjust or hasattr (event, "ForceSize"):
            position = int (distance * blockItem.splitPercentage + 0.5)
            self.AdjustAndSetSashPosition (position)
        event.Skip()

    def AdjustAndSetSashPosition (self, position):
        width, windowSize = self.GetSizeTuple()
        if self.GetSplitMode() == wx.SPLIT_VERTICAL:
            windowSize = width

        splitController = self.blockItem.splitController
        if splitController is not None:
            position = splitController.AdjustSplit (self, windowSize, position)

        self.SetSashPosition (position)

    def OnSplitChanging(self, event):
        """
          Called when the user attempts to change the splitter. We need to calculate and store
          the new splitPercentage here. This means that the splitPercentage won't change in
          response to a window size change, which is important if resizing windows small then
          large will get you back to where you started (bug #6164). Also, multiple size events
          come through when sizer Layout is called and we don't want to change the percentage
          in response to these size changes          
        """
        if not self.blockItem.allowResize:
            event.SetSashPosition(-1)
        else:
            width, windowSize = self.GetSizeTuple()
            if self.GetSplitMode() == wx.SPLIT_VERTICAL:
                windowSize = width
            assert windowSize >= 0
            self.blockItem.splitPercentage = float (event.GetSashPosition()) / windowSize
        event.Skip()

    def OnSplitChanged(self, event):
        self.AdjustAndSetSashPosition (event.GetSashPosition())
        
        # Add a hack that forces a sash adjustment of the splitter between the
        # mini calendar and the sidebar when the sash between the sidebar container
        # and summary/detail view changes.
        window1 = self.GetWindow1()
        if window1 is not None:
            method = getattr (type (window1), "OnSize", None)
            if method is not None:
                sizeEvent = wx.SizeEvent (window1.GetSize(), window1.GetId())
                sizeEvent.ForceSize = True
                method (window1, sizeEvent)

    def wxSynchronizeWidget(self):
        blockItem = self.blockItem
        self.SetSize ((blockItem.size.width, blockItem.size.height))

        # Collect information about the splitter
        oldWindow1 = self.GetWindow1()
        oldWindow2 = self.GetWindow2()

        children = [child for child in blockItem.childBlocks if not isinstance (child, MenusAndToolbars.BaseItem)]
        assert (len (children) >= 1 and
                len (children) <= 2), "Splitter windows only support one or two non-DynamicBlocks"

        window1 = None
        child1 = children[0]
        if child1.isShown:
            window1 = child1.widget
        child1.widget.Show (child1.isShown)

        window2 = None
        if len (children) >= 2:
            child2 = children[1]
            if child2.isShown:
                window2 = child2.widget
            child2.widget.Show (child2.isShown)

        shouldSplit = bool (window1) and bool (window2)
        
        # Update any differences between the block and widget
        self.Freeze()
        if not self.IsSplit() and shouldSplit:
            #indentlog("first time splitter creation: 2 win")
            """
            First time SplitterWindow creation with two windows or
            going between a split with one window to a split with
            two windows
            """
            if blockItem.orientationEnum == "Horizontal":
                position = blockItem.size.height * blockItem.splitPercentage
                success = self.SplitHorizontally (window1, window2, position)
            else:
                position = blockItem.size.width * blockItem.splitPercentage
                success = self.SplitVertically (window1, window2, position)
            assert success
        elif not oldWindow1 and not oldWindow2 and not shouldSplit:
            """
            First time splitterWindow creation with one window.
            """
            if window1:
                self.Initialize (window1)
            else:
                self.Initialize (window2)
        else:
            #indentlog("weird else block")
            if self.IsSplit() and not shouldSplit:
                """
                Going from two windows in a split to one window in a split.
                """
                show = oldWindow2.IsShown()
                success = self.Unsplit()
                oldWindow2.Show (show)
                assert success
            """
            Swap window1 and window2 so we can simplify the we can finish
            our work with only two comparisons.
            """            
            if bool (oldWindow1) ^ bool (window1):
                window1, window2 = window2, window1
            if window1:
                success = self.ReplaceWindow (oldWindow1, window1)
                assert success
            if window2:
                success = self.ReplaceWindow (oldWindow2, window2)
                assert success
        parent = self.GetParent()
        if parent:
            parent.Layout()
        self.Thaw()

    @classmethod
    def CalculateWXStyle(theClass, block):
        style = wx.SP_LIVE_UPDATE | wx.NO_BORDER | wx.SP_3DSASH
        return style

 
class SplitterWindow(RectangularChild):
    """
    This block seems to ignore children's stretchFactors.
    """

    splitPercentage = schema.One(schema.Float, defaultValue = 0.5)
    allowResize = schema.One(schema.Boolean, initialValue = True)
    orientationEnum = schema.One(
        orientationEnumType, defaultValue = 'Horizontal',
    )

    splitController = schema.One(inverse=Block.splitters, defaultValue=None)
  
    schema.addClouds(
        copying = schema.Cloud (byCloud = [splitController])
    )

    def instantiateWidget (self):
        return wxSplitterWindow (self.parentBlock.widget,
                                 self.getWidgetID(), 
                                 wx.DefaultPosition,
                                 (self.size.width, self.size.height),
                                 style=wxSplitterWindow.CalculateWXStyle(self))

class wxViewContainer (wxBoxContainer):
    pass


class ViewContainer(BoxContainer):
    selectionIndex = schema.One (schema.Integer, initialValue = 0)
    views = schema.Mapping(Block, initialValue = {})
    theActiveView = schema.One (Block)

    schema.addClouds(
        copying = schema.Cloud(byRef=[views])
    )

    def instantiateWidget (self):
        """
        When the ViewContainer is the root of all the blocks it
        doesn't have a parent block widget, so in that case we use
        the block must have a frame and we'll use it.
        """
        if self.parentBlock is not None:
            parentWidget = self.parentBlock.widget
        else:
            parentWidget = self.frame

        return wxViewContainer (parentWidget)
    
    def onChoiceEventUpdateUI (self, event):
        assert len (self.childBlocks) == 1
        event.arguments ['Check'] = self.theActiveView == self.views [event.choice]

    def onChoiceEvent (self, event):
        view = self.views [event.choice]
        if view != self.activeView:
            self.theActiveView = view
            self.postEventByName ('SelectItemsBroadcast', {'items':[view]})

class wxFrameWindow (wxViewContainer):
    pass

class FrameWindow (ViewContainer):
    """
    Note: @@@ For now a FrameWindow is just a ViewContainer with added
    position attributes, but we will want to move a lot of MainFrame code
    from Application.py into here.

    Right now we special case MainFrame, but we should better work that
    into the block framework.
    """
    position = schema.One(PositionType, initialValue = PositionType(-1, -1))
    windowTitle = schema.One(schema.Text, defaultValue = '')


