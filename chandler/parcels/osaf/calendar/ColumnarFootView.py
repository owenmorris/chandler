""" Columnar Foot View (the bottom section of the columnar view)
    With typical calendar data, this part of the view is meant to display
    tasks associated with a day.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *
from mx import DateTime

from application.Application import app
from application.SimpleCanvas import wxSimpleCanvas

from persistence import Persistent
from persistence.dict import PersistentDict

from ColumnarSubView import ColumnarSubView, wxColumnarSubView

class ColumnarFootView (ColumnarSubView):
    def __init__(self, columnarView):
        ColumnarSubView.__init__(self, columnarView)
        self.xrcName = "ColumnarFootView"
        # @@@ Height may be determined differently
        self.viewHeight = 50
        
class wxColumnarFootView(wxColumnarSubView):

    def OnInit(self, model):
        # @@@ For now, don't accept drag and drop data objects
        dropTargetDataObject = wxCustomDataObject()
        wxColumnarSubView.OnInit(self, model, dropTargetDataObject)
        
