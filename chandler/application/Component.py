#!bin/env python

"""The parent class that must be subclassed to create a Chandler
component.  In order to add a component to Chandler, a package
must be added to the components directory and must contain a class
which subclasses Component.  That subclass will help communicate
necessary information to the Chandler application.  Where possible
the default behavior for a component has been included in the
Component class, but certain methods will need to be overridden to
get the proper behavior.

Steps for creating a component:
    1)  Subclass Component
    2)  Create a data.xrc file that contains the necessary xml
        for your component.  (see components/cal/resources/data.xrc
        as an example)
    3)  Create one or more views to represent your component
        and add them to self.data["View"]

The application should directly access the Component's data dictionary
to get information about the component.  There is a list of what is in
the data dictionary at the beginning of the class definition.

To see a description of the methods that are available to a component,
please see Chandler/applications/ComponentInterface."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from wxPython.wx import *
from wxPython.xrc import *

from ComponentXmlHandler import ComponentXmlHandler

class Component:
    """The application will access the data dictionary directly to
    get information from the component.  The key will determine the
    type of information that the application is requesting.  Possible
    keys are:
        ComponentName
            Returns a string representing this component's name.
                
        Description
            Returns a string that describes this component's 
            functionality.

        DefaultUri
            Returns a string representing the default uri for this
            component.

        View
            Returns a dictionary of views.  The dictionary has keys
            representing uri's.  A corresponding view is associated
            with each uri in the dictionary.

        SidebarTree
            Returns a list representing the strings that should be
            displayed for navigation within the sidebar.  Each item
            in the list is a tuple whose first element is the text
            to be displayed, and whose second element is either a list
            representing that item's children or None for a leaf

        NavigationMenu
            Returns a wxMenu that will be added to the View menu so
            that the user can navigate between views of this component.
            NOTE:  Whenever a view is added, the component is responsible
            for adding that view's navigation to the navigation menu,
            since the component still owns the menu.

        ComponentMenu
            Returns a wxMenu that will be used as a top level menu
            for this component when it is active.

        OriginalUriList
            Returns a list of all of the available uri's.
        """
    
    def Load(self, parent, frame, interface, resourceInfo):
        """Called when the component is first loaded.  This is a chance
        to allocate any data structures and do the necessary setup."""
        self._parent = parent
        self._frame = frame
        self.interface = interface
                
        self.data = {}
        self.data["ComponentName"] = ""
        self.data["Description"] = ""
        self.data["DefaultUri"] = ""
        self.data["View"] = {}
        self.data["SidebarTree"] = []
        self.data["NavigationMenu"] = None
        self.data["ComponentMenu"] = None
        self.data["OriginalUriList"] = []
        
        # Create the component menu from the xrc resource
        resourceLocation, menuName = resourceInfo
        self._resource = wxXmlResource(resourceLocation)
        self.data["ComponentMenu"] = self._resource.LoadMenu(menuName)

        self._xmlHandler = ComponentXmlHandler(self, self._frame)
        self._xmlHandler.Load(resourceLocation)
        
    def Unload(self, isActive = false):
        """Called when the component is no longer needed.  Deallocate any
        memory and do whatever necessary cleanup."""
        self._resource.Destroy()
        if not isActive:
            self.data["ComponentMenu"].Destroy()
            
    def Activate(self):
        """Called when the component has been selected.  Do whatever is
        necessary to be prepared to display."""
        pass

    def Deactivate(self):
        """Called when the component is no longer being displayed.  Do
        whatever cleanup is appropriate."""
        pass

 