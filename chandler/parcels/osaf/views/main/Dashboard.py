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
        skipIt = True # should we event.Skip() at the end of this?
        try:
            gridWindow = self.GetGridWindow()

            def getHandler(cell):
                if cell is None or -1 in cell:
                    return None
                renderer = self.GetCellRenderer(cell[1], cell[0])
                try:
                    # See if it's renderer with an attribute editor that wants
                    # mouse events
                    handler = renderer.delegate.OnMouseChange
                except AttributeError:
                    # See if it's a section renderer that wants mouse events
                    handler = getattr(renderer, 'OnMouseChange', None)
                return handler
                
            # Figure out what cell we're in, and see whether it 
            # wants raw events
            cell = self.__eventToCell(event)
            handler = getHandler(cell)

            # We keep track of what cell the mouse was over last time
            overCell = getattr(self, "overCell", None)

            # Summarize the state on each call
            if False: # __debug__:
                evtType = event.GetEventType()
                evtType = evtNames.get(evtType, evtType)
                logger.debug("wxDashboard.OnMouseEvents: %s, %s "
                             "(raw=%s, o=%s)",
                             evtType, cell, handler is not None,
                             overCell)

            # Did the cell we're over change?
            if cell != overCell: # yep
                # If the old cell had a handler, dirty it and tell it
                oldHandler = getHandler(overCell)
                if oldHandler is not None:
                    self.RefreshRect(self.CalculateCellRect(overCell))
                    itemAttrPair = self.GetTable().GetValue(overCell[1], overCell[0])
                    #logger.debug("in=False, down=%s to old overCell: %s %s", 
                                 #event.LeftIsDown(), *itemAttrPair)
                    oldHandler(event, overCell, False, event.LeftIsDown(), 
                               itemAttrPair)
                    skipIt = False
                
                # We'll need to notify the new cell too.
                mustTellNewCell = True

                # Update the saved cell
                if handler is not None and not -1 in cell:
                    self.overCell = cell
                elif overCell is not None:
                    del self.overCell
            else:
                # No cell change - did the mouse state change?
                mustTellNewCell = event.LeftUp() or event.LeftDown() or event.LeftDClick()
            
            if mustTellNewCell and handler is not None:
                # Either in-ness or down-ness changed - dirty the new cell and
                # tell it.
                self.RefreshRect(self.CalculateCellRect(cell))
                itemAttrPair = self.GetTable().GetValue(cell[1], cell[0])
                #logger.debug("in=True, down=%s to new cell: %s %s", 
                             #event.LeftIsDown(), *itemAttrPair)
                handler(event, cell, True, event.LeftIsDown(), itemAttrPair)
                skipIt = False
    
        finally:
            if skipIt:
                #logger.debug("Dashboard Calling event.Skip")
                event.Skip()
            #else:
                #logger.debug("Dashboard NOT calling event.Skip")
                

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

    def onPurgeEvent(self, event):
        for key in self.contents.iterkeys():
            triageStatus = self.itsView.findValue(key,
                                                 '_editedTriageStatus',
                                                  default=None)
            if triageStatus is not None:
                item = self.itsView[key]
                item.triageStatus = triageStatus

