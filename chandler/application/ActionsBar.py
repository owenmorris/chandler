#!bin/env python

"""Second toolbar for Chandler.  Contains action buttons that
may either trigger an action directly, or display a dropdown of
possible actions to choose from."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *

ACTIONS_BAR_WIDTH = 1000
ACTIONS_BAR_HEIGHT = 30
RESOURCE_FILE_LOCATION = "application/resources/actions.xrc"
ACTIONS_BAR_NAME = "ActionsBar"
     
class ActionsBar(wxPanel):
    # Even though this acts as a toolbar, due to limitations in wxPython
    # which do not allow for multiple toolbars (at least reliably), it is
    # created as a panel which is inserted into the very top of the frame.
    def __init__(self, parent, id = -1, 
                 size = (ACTIONS_BAR_WIDTH, ACTIONS_BAR_HEIGHT)):
        """The information for the actions bar is stored in a resource
        file.  To create the actions bar we must just load it from the 
        resource."""
        wxPanel.__init__(self, parent, id, size = size)
        self._parent = parent
        self._resources = wxXmlResource(RESOURCE_FILE_LOCATION)
        self.actionsBar = self._resources.LoadToolBar(self, ACTIONS_BAR_NAME)
