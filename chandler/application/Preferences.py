__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

from persistence import Persistent
from persistence.dict import PersistentDict

class Preferences (Persistent):
    """
       Global Application preferences.
    """
    def __init__(self):
        self.windowSize = PersistentDict()
        self.windowSize['width'] = 850
        self.windowSize['height'] = 650


