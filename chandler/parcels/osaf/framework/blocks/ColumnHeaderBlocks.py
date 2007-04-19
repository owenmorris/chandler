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

import wx
from wx import colheader
from application import schema
from Block import RectangularChild

class ColumnHeader (RectangularChild):
    """This class defines a generic ColumnHeader kind."""

    # -- Attributes for ColumnHeader -- #

    columnHeadings       = schema.Sequence(schema.Text, required = True) 
    columnWidths         = schema.Sequence(schema.Integer)
    proportionalResizing = schema.One(schema.Boolean)
    visibleSelection     = schema.One(schema.Boolean)
    genericRenderer      = schema.One(schema.Boolean)
    # add selection attribute?
    
    def ResizeHeader(self):
        for (i,width) in enumerate(self.columnWidths):
            if hasattr(self, "widget"):
                self.widget.SetItemSize(i, (width, 0))

    def defaultOnSize(self, event):
        self.ResizeHeader()
        event.Skip()
        
        
    def instantiateWidget(self):

        # create widget instance as a child of the parent block's widget.
        wxColHeaderInstance = colheader.ColumnHeader(self.parentBlock.widget) 
        
        # FYI: currently, calendar needs proportional resizing off (false), because sizing needs to be exact
        wxColHeaderInstance.SetAttribute(colheader.CH_ATTR_ProportionalResizing, self.proportionalResizing) 

        # set attributes
        if hasattr(self, "visibleSelection"): wxColHeaderInstance.SetAttribute(colheader.CH_ATTR_VisibleSelection,          self.visibleSelection)
        if hasattr(self, "proportionalResizing "): wxColHeaderInstance.SetAttribute(colheader.CH_ATTR_ProportionalResizing, self.proportionalResizing )
        if hasattr(self, "genericRenderer"): wxColHeaderInstance.SetAttribute(colheader.CH_ATTR_GenericRenderer, self.genericRenderer)

        # add columns.
        for header in self.columnHeadings:
            wxColHeaderInstance.AppendItem(header, wx.ALIGN_CENTER, 20, bSortEnabled=False)

        # set a default size-event handler  (this may need to be removed)
        wxColHeaderInstance.Bind(wx.EVT_SIZE, self.defaultOnSize)

        wxColHeaderInstance.Layout()
        
        return wxColHeaderInstance 
