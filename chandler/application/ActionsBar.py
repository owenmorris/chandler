#!bin/env python

"""Second toolbar for Chandler.  Contains action buttons that
may either trigger an action directly, or display a dropdown of
possible actions to choose from."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"


from wxPython.wx import *
from wxPython.xrc import *
     
class ActionsBar(wxPanel):
    # Even though this acts as a toolbar, due to limitations in wxPython
    # which do not allow for multiple toolbars (at least reliably), it is
    # created as a panel which is inserted into the very top of the frame.
    def __init__(self, parent, id=-1, size=(1000,30)):
        wxPanel.__init__(self, parent, id, size=size)
        self.parent = parent
        self.resources = wxXmlResource ("application/resources/actions.xrc")
        self.actionsBar = self.resources.LoadToolBar(self, "ActionsBar")