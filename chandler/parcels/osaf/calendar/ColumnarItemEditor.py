""" Editor used to edit columnar items

    @@@ Currently scaffolding, in place editing will get more interesting
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cPickle

from wxPython.wx import *
from mx import DateTime

class ColumnarItemEditor(wxTextCtrl):
    def __init__(self, parent):
        wxTextCtrl.__init__(self, parent, -1, '', 
                            style=wxTE_MULTILINE | wxTE_RICH | wxNO_BORDER)
        
        self.drawableItem = None

        EVT_TEXT(self, self.GetId(), self.OnText)
        EVT_KILL_FOCUS(self, self.OnKillFocus)
        
    def SetItem(self, drawableItem):
        self.drawableItem = drawableItem
        self.SetValue(drawableItem.item.headline)

        self.OnSize()

        self.SetFocus()
        self.SetSelection(-1, -1)
        self.Show()
        
    def OnSize(self):
        """ Position the editor, ask the drawable object for the editor bounds
        """
        if (self.drawableItem):
            size = (self.drawableItem.editorBounds.width, 
                    self.drawableItem.editorBounds.height)
            self.SetSize(size)
            position = (self.drawableItem.editorBounds.x + self.drawableItem.bounds.x,
                        self.drawableItem.editorBounds.y + self.drawableItem.bounds.y)
            position = self.drawableItem.canvas.CalcScrolledPosition(position)
            self.Move(position)     
        
    def ClearItem(self):
        self.drawableItem = None
        self.Hide()
        
    def OnText(self, event):
        if (self.drawableItem):
            self.drawableItem.item.headline = self.GetValue()
                    
    def OnKillFocus(self, event):
        self.ClearItem()
        event.Skip()
        
        