""" Columnar Item, representation of an Item in a columnar view. 
    Implemented as a wxSimpleDrawableObject in a wxSimpleCanvas.

    @@@ Note: in-place editing is currently rough scaffolding. Also,
    uses EventItems specifically when it should use Items more 
    generally.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cPickle

from wxPython.wx import *
from wxPython.xrc import *
from mx import DateTime

from persistence import Persistent
from persistence.dict import PersistentDict

from application.Application import app
from application.SimpleCanvas import wxSimpleDrawableObject

class ColumnarItem(wxSimpleDrawableObject):
    def __init__(self, canvas, item):
        wxSimpleDrawableObject.__init__(self, canvas)
        self.item = item
        self.model = canvas.model
        
    def OnMouseEvent(self, event):
        x, y = event.GetPositionTuple()
        if event.ButtonDown() and self.SelectedHitTest (x, y) :
            self.canvas.editor.ClearItem()
            self.canvas.DeSelectAll()
            self.SetSelected()
            self.canvas.Update()
        
        if event.ButtonDown():

            if self.item.IsRemote():
                message = _("Sorry, but you don't have permission to edit a remote item.  Would you like to copy it to your local repository?")
                result = wxMessageBox(message, _("Can't Edit Remote Item"), wxYES_NO | wxICON_QUESTION)
        
                # turn the item into a local item by zeroing the remote address and adding it
                # to the repository
                if result == wxID_YES:
                    self.item.remoteAddress = None
                    # @@@ fix me, how to deal with this case
                    #repository = Repository()
                    #repository.AddThing(self.item)   
                return true
            
            if event.ButtonDown() and self.ReSizeHitTest(x, y):
                self.canvas.dragStart = wxPoint (self.bounds.x, self.bounds.y)
                self.canvas.CaptureMouse()
                self.canvas.dragCreateDrawableObject = self
                return true
            
            if event.ButtonDown() and self.DragHitTest(x, y):
                self.DoDrag(x, y)
                return true
        
            if event.ButtonDown() and self.EditHitTest(x, y):
                self.canvas.editor.SetItem(self)
                return true
        
        event.Skip()
        return false
            
    def Draw(self, dc):
        # @@@ move to an update routine?
        self.SetEditorBounds()
        
        if self.item.IsRemote():
            dc.SetBrush(wxBrush(wxColor(180, 192, 121)))
        else:
            dc.SetBrush(wxBrush(wxColor(160, 192, 159)))

        if self.selected:
            dc.SetPen(wxBLACK_PEN)
        else:
            dc.SetPen(wxTRANSPARENT_PEN)

        dc.DrawRoundedRectangle(1, 1, 
                                self.bounds.width - 1, 
                                self.bounds.height - 1,
                                radius=10)
        
        # @@@ Scaffolding, draw the time and headline for show
        dc.SetTextForeground(wxBLACK)
        dc.SetFont(wxSWISS_FONT)
        time = self.item.CalendarStartTime
        dc.DrawText(time.Format('%I:%M %p'), 10, 0)
        self.DrawWrappedText(dc, self.item.CalendarHeadline, self.bounds.width - 1)
        
    def DrawWrappedText(self, dc, text, wrapLength):
        # @@@ hack hack hack 
        # Simple wordwrap to display the text, until we can
        # get the native text widgets to do it for us.
        if (self.model.showFreeBusy):
            offset = self.model.freebusy
        else:
            offset = 5
         
        lines = text.splitlines()
        y = 14
        for line in lines:
            x = offset
            wrap = 0
            words = line.split(' ')
            for word in words:
                width, height = dc.GetTextExtent(word)
                if (x + width > wrapLength):
                    y += height
                    x = offset
                dc.DrawText(word, x, y)
                x += width
                width, height = dc.GetTextExtent(' ')
                dc.DrawText(' ', x, y)
                x += width
            y += height

    def DrawMask(self, dc):
        dc.SetBrush(wxWHITE_BRUSH)
        dc.SetPen(wxWHITE_PEN)

        dc.DrawRoundedRectangle(1, 1,
                                self.bounds.width - 1,
                                self.bounds.height - 1,
                                radius=10)
        
    def DragHitTest(self, x, y):
        return (self.visible and not self.EditHitTest(x, y))
        
    def SelectedHitTest(self, x, y):
        return self.visible
    
    def EditHitTest(self, x, y):
        return (self.visible and self.editorBounds.Inside((x, y)))
    
    def ReSizeHitTest(self, x, y):
        reSizeBounds = wxRect(self.editorBounds.x,
                            self.editorBounds.y + self.editorBounds.height,
                            self.editorBounds.width, 24)
        return (self.visible and reSizeBounds.Inside((x,y)))
        
    def SizeDrag(self, dragRect, startDrag, endDrag):
        self.item.CalendarStartTime = self.model.getDateTimeFromPos(dragRect.GetPosition())
 
        endHour, endMin = self.model.getTimeFromPos(dragRect.GetBottom())
        self.item.CalendarEndTime = DateTime.DateTime(self.item.CalendarStartTime.year,
                                                      self.item.CalendarStartTime.month,
                                                      self.item.CalendarStartTime.day,
                                                      endHour, endMin)
        
        if (self.item.CalendarDuration.hours < self.model.minHours):
            self.item.CalendarDuration = DateTime.TimeDelta(self.model.minHours)
        
        self.PlaceItemOnCalendar()
    
    def ConvertDrawableObjectToDataObject(self, x, y):
        dataFormat = wxCustomDataFormat("ChandlerItem")
        dragDropData = wxCustomDataObject(dataFormat)
        data = cPickle.dumps((str(self.item.getPath()), x, y), true)
        dragDropData.SetData(data)
        return dragDropData
    
    def MoveTo(self, x, y):
        newTime = self.model.getDateTimeFromPos(wxPoint(x, y))
        self.item.ChangeStart(newTime)
        wxSimpleDrawableObject.MoveTo(self, x, y)
        
    def PlaceItemOnCalendar(self):
        width = self.model.dayWidth
        height = int(self.item.CalendarDuration.hours * self.model.hourHeight)
        position = self.model.getPosFromDateTime(self.item.CalendarStartTime)
        bounds = wxRect(position.x, position.y, width, height)
        self.SetBounds(bounds)
        self.SetEditorBounds()
    
    def SetEditorBounds(self):
        if (self.model.showFreeBusy):
            offset = self.model.freebusy
        else:
            offset = 3
        width = self.bounds.width - (offset + 2)
        height = self.bounds.height - 24
        self.editorBounds = wxRect(offset, 14, width, height)

