__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from wxPython.wx import *
from wx import py

class DebuggerWindow(wxFrame):
    """
      This class implements a simple python debugger window
    """

    def __init__(self, parentApp, parent=None, id=-1, title="Debugger"):
        wxFrame.__init__(self, parent, id, title)
        self.shell = py.shell.Shell(parent=self)
        self.shell.interp.locals['chandler'] = parentApp
        EVT_CLOSE(self, self.OnCloseWindow)
        
    def OnCloseWindow(self, event):
        self.Destroy()
        
