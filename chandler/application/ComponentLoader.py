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
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *

class ComponentLoader:
    def __init__(self, parent, frame):
        pass
    
    def GetComponentName(self):
        """The name of the component"""
        return None
    
    def GetDefaultUri(self):
        return None
    
    def GetViewFromUri(self, uri):
        return None

    def GetViewsMenu(self):
        return None
    
    def GetComponentMenu(self):
        return None
    
    def GetNavTree(self):
        return None

