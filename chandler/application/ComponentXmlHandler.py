#!bin/env python

"""This class handles all of the xml processing for the Component parent
class.  It uses the generalized XmlReader to generate a dictionary directly
from the xml file, and then converts that dictionary into a more meaningful
structure for the component."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from application.XmlReader import XmlReader

class ComponentXmlHandler:
    def __init__(self, component, frame):
        """Sets up the initial variables for the handler."""
        self._component = component
        self._frame = frame

        # Associates menu ids (taken from the xml) with their corresponding
        # uri's
        self._ids = {}
        
    def Load(self, fileLocation):
        """Called when it is time for the xml handler to actually do its
        processing.  Creates a dom tree based on the specified xml file
        and then turns that tree into a dictionary so that it can be more
        easily accessed.  The information from that dictionary is then 
        stored in the component's data structure."""
        reader = XmlReader()
        dict = reader.ReadXmlFile(fileLocation)        
        self._dict = dict["resource"]
        
        self._component.data["ComponentName"] = self._dict["ComponentName"]
        self._component.data["Description"] = self._dict["Description"]
        self._component.data["DefaultUri"] = self._dict["DefaultUri"]
        self.__CreateNavigationElements()

    def __CreateNavigationElements(self):
        """Creates the navigation elements for this component.  This includes
        both the sidebar and the view menu navigation.  These elements are 
        all based on the same xml for consistency."""        
        tree = []
        menuList = []
        nav = self._dict["Navigation"]
        for navKey in nav.keys():
            navItem = nav[navKey]                        
            # Create a tuple of the item name & a list of children
            nameChildrenTuple = (navItem["Name"], [])
            menu = wxMenu()
            for key in navItem.keys():
                if key != "Name":
                    # Sidebar stuff
                    childName = navItem[key]["Name"]
                    nameChildrenTuple[1].append((childName, None))
                    # Nav menu stuff
                    id = string.atoi(navItem[key]["Id"])
                    menu.Append(id, childName)
                    self._ids[id] = navItem["Name"] + "/" + childName
                    EVT_MENU(self._frame, id, self.__MenuNavigationEvent)
            tree.append(nameChildrenTuple)
            menuList.append(menu)
                
        self._component.data["SidebarTree"] = tree
        self._component.data["NavigationMenu"] = menuList
        
    def __MenuNavigationEvent(self, event):
        """Envoked when the user has chosen one of the view navigation menus.
        Looks up the id of the event that has been generated and tells the
        application to navigate to the associated uri."""
        id = event.GetId()
        self._component.interface.GoToUri(self._ids[id])        
                
