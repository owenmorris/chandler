#!bin/env python

"""The parent class for modules that help aid in the discovery
of new components to add on to Chandler.  In order to add a
component to Chandler, a package must be added to the components
directory and must contain a class which is a subclass of 
ComponentLoader.  That subclass will help tell the application
certain things about the new component, the most important of
which is locating the main class of the component."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"


from wxPython.wx import *
from wxPython.xrc import *

class ComponentLoader:
    def __init__(self, parent, frame):
        pass
    
    def GetName(self):
        return None
    
    def GetCurrentView(self):
        """Must be overridden by a subclass so that the
        application can locate the default view that should
        be shown when this component is loaded."""
        return None
    
    def GetViewNamed(self, viewName):
        return None

    def GetViewMenu(self):
        return None

    def GetMenu(self):
        return None
    
    def GetNavTree(self):
        return None

