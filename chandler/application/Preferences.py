__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

from Persistence import Persistent, PersistentDict

class Preferences (Persistent):
    """
       Global Application preferences.
    """
    def __init__(self):
        self.windowSize = PersistentDict.PersistentDict()
        self.windowSize['width'] = 679
        self.windowSize['height'] = 532


