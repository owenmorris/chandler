#!bin/env python

"""This class keeps track of all of the open windows in the Chandler
application.  It also manages the properties about where new windows
should be created and what their properties should be."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *

from persist.Persist import Storage, Persistent
from persist.Persist import List as PList

from application.XmlReader import XmlReader
from application.ChandlerWindow import ChandlerWindow

import os

DEFAULT_X_PERCENTAGE = .8
DEFAULT_Y_PERCENTAGE = .9
COMPONENTS_DIRECTORY = './components'
PREFS_LOCATION = './application/resources/preferences.xrc'

class WindowManager(Persistent):
    def __init__(self):
        """We start out by seeing if the window manager has been persisted.
        If it has, then we don't have to do anything.  If not, then we
        set up a dictionary of windows, load the preferences, and load the
        components."""
        try: # See if we were persisted
            self._windowData
            self._windowData['preferences']
            self._windowData['componentList']
        except:
            self._windowData = {}
            self.__LoadPrefs()
            self.__LoadComponentList()        
    
    def NotifyAllWindows(self):
        """Sends a notify message to all of the windows in the window 
        list.  If the window list has not been created, we create it.
        If there are no windows in the list, then we create one."""
        try: # See if we have persisted the windows
            self._windowData['windowList']
        except:
            # We would like this to be just a normal list, but if it is,
            # then ZODB doesn't realize that it changes when you append
            # to it, and so it doesn't get dirtied, and thus additional
            # commits do not affect it.
            self._windowData['windowList'] = PList()
        if len(self._windowData['windowList']) < 1:
            size, pos = self.__NewWindowInfo()
            window = ChandlerWindow(None, self, 
                                    self._windowData['componentList'],
                                    size = size, 
                                    pos = pos)
            self._windowData['windowList'].append(window)
        for window in self._windowData['windowList']:
            window.Notify()

    def __LoadPrefs(self):
        """Reads the preferences from an xml file."""
        self._reader = XmlReader()
        dict = self._reader.ReadXmlFile(PREFS_LOCATION)
        prefsDict = dict['preferences']
        
        width = string.atoi(prefsDict['windowSize']['width'])
        height = string.atoi(prefsDict['windowSize']['height'])
        if width == -1 or height == -1:
            display = wxClientDisplayRect()
            width = display[2] - display[0]
            height = display[3] - display[1]
            width = width * DEFAULT_X_PERCENTAGE
            height = height * DEFAULT_Y_PERCENTAGE
        prefsDict['windowSize']['width'] = width
        prefsDict['windowSize']['height'] = height
        prefsDict['defaultPos']['x'] = string.atoi(prefsDict['defaultPos']['x'])
        prefsDict['defaultPos']['y'] = string.atoi(prefsDict['defaultPos']['y'])
        prefsDict['windowPos']['x'] = string.atoi(prefsDict['windowPos']['x'])
        prefsDict['windowPos']['y'] = string.atoi(prefsDict['windowPos']['y'])
        prefsDict['windowDelta']['x'] = string.atoi(prefsDict['windowDelta']['x'])
        prefsDict['windowDelta']['y'] = string.atoi(prefsDict['windowDelta']['y'])
        self._windowData['preferences'] = prefsDict
        
    def __LoadComponentList(self):
        """Gets a list of each of the components for Chandler.  Among other
        things, this will include the email, calendar, and contacts
        components.  In order for a component to be successfully loaded, it
        must have it's own folder in the components directory of Chandler, 
        that folder must contain an __init__.py file, it must have a file
        that subclasses Component, and it must have a data.xrc file in a 
        resources directory.

        Returns a list of tuples, with each tuple containing the information
        necessary to load a single component.  The first item in the tuple is
        the name of the class that subclasses ComponentLoader and the second
        item is the path to that component."""
        componentDirectory = os.listdir(COMPONENTS_DIRECTORY)

        componentStrings = []
        reader = XmlReader()
        for package in componentDirectory:
            try:
                componentName = self.GetBaseClassFromXml(reader, package)
                path = 'components.' + package + '.' + componentName
                componentStrings.append((componentName, path))
            except:
                # If it isn't a component (i.e extraneous folder) then
                # we don't want to say anything.  If it is a component,
                # but the xml is misformatted, we have already said all
                # we need to say
                pass
        self._windowData['componentList'] = componentStrings

    def GetBaseClassFromXml(self, reader, package):
        """Given a possible package name, sees if it actually is a component.
        It does this by first looking for a data.xrc file.  If it cannot find
        one, it raises an error indicating that this is not a component.  If 
        it does find the data.xrc file, it returns the base class that
        represents this component.  If the file is improperly formatted or 
        does not contain the necessary information, it prints a message
        indicating so and raises an exception."""
        try:
            dict = reader.ReadXmlFile('components/' + package + '/resources/data.xrc')
        except:
            raise "Not component"
        try:
            componentName = dict['resource']['ComponentClass']
        except:
            print 'Could not find proper information in Component XML file'
            print 'Failed to load component:  ' + package            
            raise "Bad XML File"
        return componentName
    
    def __NewWindowInfo(self):
        """Whenever a new window is created, we call this method to determine
        what that new window's size and position should be.  We first look
        in the preferences dictionary to see what the values should be.  We
        then make sure that the window will fit on the screen.  If not, we
        move it so that it will.

        Returns a tuple, the first element of which is a tuple representing
        the size, the second element of which is a tuple representing the
        position."""
        width = self._windowData['preferences']['windowSize']['width']
        height = self._windowData['preferences']['windowSize']['height']
        x = self._windowData['preferences']['windowPos']['x']
        y = self._windowData['preferences']['windowPos']['y']
        x += self._windowData['preferences']['windowDelta']['x']
        y += self._windowData['preferences']['windowDelta']['y']
        
        # Get a rectangle representing the available portion of the screen.
        # That portion takes into account things like the Window's Start
        # menu bar.
        display = wxClientDisplayRect()
        if x < display[0]:
            x = display[0]
        if y < display[1]:
            y = display[1]
        # If we don't fit on the screen
        if (x + width) > display[2] or (y + height) > display[3]:
            x = self._windowData['preferences']['defaultPos']['x']
            y = self._windowData['preferences']['defaultPos']['y']

        self._windowData['preferences']['windowPos']['x'] = x
        self._windowData['preferences']['windowPos']['y'] = y
            
        return ((width, height), (x, y))
    
    def SetSize(self, size):
        """Whenever a window is resized, then that new size is used as
        the default size when new windows are created."""
        width, height = size
        self._windowData['preferences']['windowSize']['width'] = width            
        self._windowData['preferences']['windowSize']['height'] = height

    def NewWindow(self):
        """Create a new ChandlerWindow and add it to the list of open
        windows.  Offsets the new window slightly so that they are not
        directly overlayed."""        
        newSize, pos = self.__NewWindowInfo()
        window = ChandlerWindow(None, self, 
                                self._windowData['componentList'],
                                size = newSize, 
                                pos = pos)

        self._windowData['windowList'].append(window)
            
        for window in self._windowData['windowList']:
            window.Notify()

    def RemoveWindow(self, win):
        """Remove the window from the list of open windows.  Should only be
        called right before the window is closed."""
        self._windowData['windowList'].remove(win)
        
    def QuitApp(self):
        """Quit the application by closing all open windows."""
        windowsToClose = self._windowData['windowList'][:]
        for window in windowsToClose:
            window.OnQuit()
