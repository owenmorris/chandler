__version__ = "$Revision: 5791 $"
__date__ = "$Date: 2005-06-28 18:36:01Z $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks"

import sys
import wx
import wx.colheader
from osaf.framework.blocks import Block
from application import schema
from Block import *
from ContainerBlocks import *

class ColumnHeader (RectangularChild):
    """This class defines a generic ColumnHeader kind."""

    # -- Attributes for ColumnHeader -- #

    columnHeadings       = schema.Sequence(schema.String, required = True) 
    columnWidths         = schema.Sequence(schema.Integer)
    proportionalResizing = schema.One(schema.Boolean)
    visibleSelection     = schema.One(schema.Boolean)
    unicode              = schema.One(schema.Boolean)
    genericRenderer      = schema.One(schema.Boolean)
    # add selection attribute?
    
    def ResizeHeader(self):
        for (i,width) in enumerate(self.columnWidths):
            if hasattr(self, "widget"):
                self.widget.SetUIExtent(i, (0,width))

    def defaultOnSize(self, event):
        self.ResizeHeader()
        event.Skip()
        
        
    def instantiateWidget(self):

        # create widget instance as a child of the parent block's widget.
        wxColHeaderInstance = wx.colheader.ColumnHeader(self.parentBlock.widget) 
        
        # FYI: currently, calendar needs proportional resizing off (false), because sizing needs to be exact
        wxColHeaderInstance.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing, self.proportionalResizing) 

        # set attributes
        if hasattr(self, "visibleSelection"): wxColHeaderInstance.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,          self.visibleSelection)
        if hasattr(self, "proportionalResizing "): wxColHeaderInstance.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing, self.proportionalResizing )
        if hasattr(self, "unicode"): wxColHeaderInstance.SetAttribute(wx.colheader.CH_ATTR_Unicode,                            self.unicode)
        if hasattr(self, "genericRenderer"): wxColHeaderInstance.SetAttribute(wx.colheader.CH_ATTR_GenericRenderer, self.genericRenderer)

        # add columns.
        for header in self.columnHeadings:
            wxColHeaderInstance.AppendItem(header, wx.colheader.CH_JUST_Center, 20, bSortEnabled=False)

        # set a default size-event handler  (this may need to be removed)
        wxColHeaderInstance.Bind(wx.EVT_SIZE, self.defaultOnSize)

        wxColHeaderInstance.Layout()
        
        return wxColHeaderInstance 
