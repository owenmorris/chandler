__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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
        
        self.attributes = PersistentDict()
        
    def GetPreferenceValue(self, preferenceKey):
        if self.attributes.has_key(preferenceKey):
            return self.attributes[preferenceKey]
        return None
    
    def SetPreferenceValue(self, preferenceKey, preferenceValue):
        self.attributes[preferenceKey] = preferenceValue
      

