#!bin/env python

"""This is the interface that the application provides to components.
All interaction that a component wishes to have with Chandler should be
tunnelled through this interface.  It allows a component to modify the 
state of the application including the menus, toolbars, sidebar, and the
current view that is being displayed."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from wxPython.wx import *

class ComponentInterface:
    def __init__(self, window):
        self._window = window
        
    def GoToUri(self, uri, doAddToHistory = true):
        """Selects the view (indicated by the uri) from the proper
        component.  This method will update the main display, the menubar,
        and the sidebar to reflect the current location."""
        self._window.GoToUri(uri, doAddToHistory)
    
    def ManageMenu(self, command, data = None):
        """Possible commands are:
            GetMenuId (where data is the text of the menu who's id you want)
                Returns the id of the menu who's text you supplied.

            Insert (where data is a tuple whose first element is the id of the
                menu or menuItem after which you want to insert, and the
                second item is the wxMenu you wish to insert)

                Inserts the specified menu into the specified location.
                The menu will only remain there as long as the component is
                active.  When it is not, the application will remove it.

            Remove (where data is the id of the menu to remove)
                Removes the specified menu.  The menu will only remain
                removed while the component is active.  When it is not, the
                application will add it back in.

            Rename (where data is a tuple whose first element is the id of the
                menu to rename and whose second element is a string
                representing the new name for the menu)

                Renames the specified menu with the supplied new name.  This
                change will only last as long as the component is active.
                When it is not, the menu will revert to its old name.
                
            Enable (where data is a tuple whose first element is the id of the
                menu to enable/disable and whose second element is a boolean
                (true to enable the menu, false to disable it)
                
                Enables or disables the specified menu.
            
            Check (where data is a tuple whose first element is the id of the
                menu to check/uncheck and whose second element is a boolean
                (true to check the menu, false to uncheck it)
                
                Checks or unchecks the specified menu.
        """
        pass

    def ManageSidebar(self, command, data):
        """Possible commands are:
            GetItemId (where data is the text of the item who's id you want)
                Returns the id of the item who's text you supplied.

            Insert (where data is a tuple whose first element is the id of the
                item after which you want to insert, and the second item is
                a string represeting the item you wish to insert)

                Inserts the supplied item into the specified location.  The
                item will continue to remain there after the component is 
                no longer active and can only be removed by calling 
                ManageSidebar and passing the Remove command.

            Remove (where data is the id of the item to remove)
                Removes the specified item.  The item will be permanently
                removed unless a component specifically adds it back by
                calling ManageSidebar and passing the Insert command.

            Rename (where data is a tuple whose first element is the id of the
                item to rename and whose second element is a string
                representing the new name for the item)

                Renames the specified menu with the supplied new name.
                
            ChangeIcon (where data is a tuple whose first element is the id of
                the item whose icon you wish to change, and whose second
                element is the bitmap you wish to use for an icon)
                
                Changes the icon for the specified item.  If you no longer
                want an icon to be displayed, supply None as the second item
                in the data tuple.

            Enable (where data is a tuple whose first element is the id of the
                item to enable/disable and whose second element is a boolean
                (true to enable the item, false to disable it)
                
                Enables or disables the specified item.
        """
        pass
        
    def ManageToolbar(self, command, data):
        """Possible commands are:
            
            Insert (where data is a tuple whose first element is the id of the
                item after which you want to insert, and the second item is
                the tool to be inserted)

                Inserts the supplied tool into the specified location.  The
                tool will continue to remain there after the component is 
                no longer active and can only be removed by calling 
                ManageToolbar and passing the Remove command.

            Remove (where data is the id of the tool to remove)
                Removes the specified tool.  The tool will be permanently
                removed unless a component specifically adds it back by
                calling ManageToolbar and passing the Insert command.

            SetText (where data is a tuple whose first element is the id of the
                tool whose text we want to set and whose second element is 
                a string representing the new text for the tool)

                Sets the text of the specified tool to the supplied new name.
                
            ChangeIcon (where data is a tuple whose first element is the id of
                the tool whose icon you wish to change, and whose second
                element is the bitmap you wish to use for an icon)
                
                Changes the icon for the specified tool.  If you no longer
                want an icon to be displayed, supply None as the second item
                in the data tuple.
                   
            Enable (where data is a tuple whose first element is the id of the
                tool to enable/disable and whose second element is a boolean
                (true to enable the tool, false to disable it)
                
                Enables or disables the specified tool.

            AddAvailableUri (where data is a string represting the uri to add)
                Adds the supplied uri to the list of available uri's 
        """
        pass