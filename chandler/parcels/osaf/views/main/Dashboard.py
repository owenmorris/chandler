#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


"""
Stuff related to the dashboard
"""

from application import schema
from osaf.framework import Preferences
from osaf.framework.blocks import (Block, debugName, Table, 
                                   wxTable, GridCellAttributeEditor, 
                                   GridCellAttributeRenderer)
from osaf.framework.attributeEditors import AttributeEditors
import wx
import logging

logger = logging.getLogger(__name__)

if __debug__:
    evtNames = {
        wx.wxEVT_ENTER_WINDOW: 'ENTER_WINDOW',
        wx.wxEVT_LEAVE_WINDOW: 'LEAVE_WINDOW',
        wx.wxEVT_LEFT_DOWN: 'LEFT_DOWN',
        wx.wxEVT_LEFT_UP: 'LEFT_UP',
        wx.wxEVT_LEFT_DCLICK: 'LEFT_DCLICK',
        wx.wxEVT_MIDDLE_DOWN: 'MIDDLE_DOWN',
        wx.wxEVT_MIDDLE_UP: 'MIDDLE_UP',
        wx.wxEVT_MIDDLE_DCLICK: 'MIDDLE_DCLICK',
        wx.wxEVT_RIGHT_DOWN: 'RIGHT_DOWN',
        wx.wxEVT_RIGHT_UP: 'RIGHT_UP',
        wx.wxEVT_RIGHT_DCLICK: 'RIGHT_DCLICK',
        wx.wxEVT_MOTION: 'MOTION',
        wx.wxEVT_MOUSEWHEEL: 'MOUSEWHEEL',
        }

class DashboardPrefs(Preferences):

    showSections = schema.One(schema.Boolean, defaultValue = True)
    
class wxDashboard(wxTable):
    def __init__(self, *arguments, **keywords):
        super (wxDashboard, self).__init__ (*arguments, **keywords)
        gridWindow = self.GetGridWindow()
        gridWindow.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
        gridWindow.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnMouseCaptureLost)
        
    def Destroy(self):
        # Release the mouse capture, if we had it
        if getattr(self.blockItem, 'mouseCaptured', False):
            delattr(self.blockItem, 'mouseCaptured')
            gridWindow = self.GetGridWindow()
            if gridWindow.HasCapture():
                #logger.debug("wxDashboard.Destroy: ReleaseMouse")
                gridWindow.ReleaseMouse()
            #else:
                #logger.debug("wxDashboard.Destroy: would ReleaseMouse, but not HasCapture.")

        return super(wxDashboard, self).Destroy()

    def CalculateCellRect(self, cell):
        cellRect = self.CellToRect(cell[1], cell[0])
        cellRect.OffsetXY (self.GetRowLabelSize(), self.GetColLabelSize())
        left, top = self.CalcScrolledPosition (cellRect.GetLeft(), cellRect.GetTop())
        cellRect.SetLeft (left)
        cellRect.SetTop (top)
        return cellRect

    def __eventToCell(self, event):
        """ return the cell coordinates for the X & Y in this event """
        x = event.GetX()
        y = event.GetY()
        unscrolledX, unscrolledY = self.CalcUnscrolledPosition(x, y)
        row = self.YToRow(unscrolledY)
        col = self.XToCol(unscrolledX)
        return (col, row)
        
    def RebuildSections(self):
        # If sections change, forget that we were over a cell.
        if hasattr(self, 'overCell'):
            del self.overCell
    
    def OnMouseEvents (self, event):
        """ 
        Handle the variety of raw mouse events cells get, passing them to 
        the rendering delegate if it wants them.
        """
        # If the handlers we call (if any) want to eat the event, they'll
        # call event.Skip(False)
        event.Skip()
        
        # Bug #7320: Don't process mouse events when the gridWindows data has
        # changed but hasn't been synchronized to the widget.
        wx.GetApp().fireAsynchronousNotifications()
        if not self.blockItem.isDirty():
            gridWindow = self.GetGridWindow()

            def callHandler(cell, isInCell, oldnew):
                if cell is None or -1 in cell:
                    return False
                
                renderer = self.GetCellRenderer(cell[1], cell[0])
                try:
                    # See if it's renderer with an attribute editor that wants
                    # mouse events
                    handler = renderer.delegate.OnMouseChange
                except AttributeError:
                    # See if it's a section renderer that wants mouse events
                    handler = getattr(renderer, 'OnMouseChange', None)
                
                if handler is None:
                    return False
                
                # Add information to the event
                event.cell = cell
                event.isInCell = isInCell
                event.getCellValue = lambda: self.GetTable().GetValue(cell[1], cell[0])
                event.getCellRect = lambda: self.CalculateCellRect(cell)
                
                # Call the handler
                wantsCapture = handler(event)                                   
                return wantsCapture
                
            # Figure out which cell we're over, and the previous one if any
            cell = self.__eventToCell(event)
            oldCell = getattr(self.blockItem, "overCell", None)

            # Summarize the state on each call
            if False:
                evtType = event.GetEventType()
                evtType = evtNames.get(evtType, evtType)
                logger.debug("wxDashboard.OnMouseEvents: %s, %s (was %s)", 
                             evtType, cell, oldCell)

            # If we were over a cell previously that wanted us to capture
            # the mouse, notify it and see whether it still wants it.
            wantsCapture = False
            if oldCell is not None:
                wantsCapture = callHandler(oldCell, oldCell == cell, "old")
                if not wantsCapture:
                    del self.blockItem.overCell

            if not wantsCapture:
                # If the old cell didn't want it, give the current 
                # cell a chance
                if oldCell != cell:
                    wantsCapture = callHandler(cell, True, "new")
                    if wantsCapture:
                        self.blockItem.overCell = cell

            # Change mouse capture if necessary. Apparently window.HasCapture
            # isn't reliable, so we track our own capturedness
            hasCapture = getattr(self.blockItem, 'mouseCaptured', False)
            if wantsCapture:
                if not hasCapture:
                    #logger.debug("OnMouseEvents: CaptureMouse")
                    gridWindow.CaptureMouse()
                    self.blockItem.mouseCaptured = True
            elif hasCapture:
                if gridWindow.HasCapture():
                    #logger.debug("OnMouseEvents: ReleaseMouse")
                    gridWindow.ReleaseMouse()
                #else:
                    #logger.debug("OnMouseEvents: would ReleaseMouse, but not HasCapture")
                del self.blockItem.mouseCaptured

    def OnMouseCaptureLost(self, event):
        if hasattr(self.blockItem, 'mouseCaptured'):
            del self.blockItem.mouseCaptured


class DashboardBlock(Table):
    """
    A block class for the Chandler Dashboard.

    This class works with the expectation that the delegate is the
    SectionedGridDelegate from the Sections module.
    """
    def instantiateWidget (self):
        widget = wxDashboard(self.parentBlock.widget, 
                             Block.Block.getWidgetID(self),
                             characterStyle=getattr(self, "characterStyle", None),
                             headerCharacterStyle=getattr(self, "headerCharacterStyle", None))
        self.registerAttributeEditors(widget)
        return widget
    
    def render(self, *args, **kwds):
        super(DashboardBlock, self).render(*args, **kwds)

        if __debug__:
            from Sections import SectionedGridDelegate
            assert isinstance(self.widget, SectionedGridDelegate)

        view = self.itsView
        prefs = schema.ns('osaf.views.main', view).dashboardPrefs
        view.watchItem(self, prefs, 'onEnableSectionsPref')
        
    def onDestroyWidget(self, *args, **kwds):
        view = self.itsView
        prefs = schema.ns('osaf.views.main', view).dashboardPrefs
        view.unwatchItem(self, prefs, 'onEnableSectionsPref')
        
        super(DashboardBlock, self).onDestroyWidget(*args, **kwds)

    def onEnableSectionsPref(self, op, item, names):
        if 'showSections' in names:
            self.synchronizeWidget()

    def onTriageEvent(self, event):
        for key in self.contents.iterkeys():
            if self.itsView.findValue(key, '_unpurgedTriageStatus', 
                                      default=None) is not None:
                item = self.itsView[key]
                item.applyUnpurgedTriageStatus()

