__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from wxPython.wx import *
from wxPython.xrc import *
from application.Application import app
from repository.item.Item import Item

class ActionsBar(Item):
    def __init__(self):
        pass
        
    def SynchronizeView(self):
        if not app.association.has_key(id(self)):
            wxWindow = wxActionsBar()
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]
                
class wxActionsBar(wxToolBar):
    def __init__(self):
        value = wxPreToolBar()
        self.this = value.this
        self._setOORInfo (self)
        
        if not app.model.mainFrame.__dict__.has_key('ActionsBar'):
            self.model = ActionsBar()
            app.model.mainFrame.ActionsBar = self.model
        else:
            self.model = app.model.mainFrame.ActionsBar
        app.association[id(self.model)] = self
        EVT_WINDOW_DESTROY (self, self.OnDestroy)
            
    def OnDestroy(self, event):
        del app.association[id(self.model)]
    
    