__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.schema.AutoItem import AutoItem

class Preferences (AutoItem):
    """
       Global Application preferences.
    """
    def __init__(self, **args):
        super (Preferences, self).__init__ (**args)
        self.newAttribute ('windowSizeWidth', 850)
        self.newAttribute ('windowSizeHeight', 650)
        self.newAttribute ('attributes', {})
        
    def GetPreferenceValue(self, preferenceKey):
        if self.attributes.has_key(preferenceKey):
            return self.attributes[preferenceKey]
        return None
    
    def SetPreferenceValue(self, preferenceKey, preferenceValue):
        self.attributes[preferenceKey] = preferenceValue
      

