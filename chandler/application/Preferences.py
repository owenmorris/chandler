# Preferences.py

__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

from wxPython.wx import *
from application.persist import Persist

class Preferences (Persist.Persistent):
    """
       Global Application preferences. """
    def __init__(self):
        self.windowSize = {'width':389, 'height':310}     #Default window size


