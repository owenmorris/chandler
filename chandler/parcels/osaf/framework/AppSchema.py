""" Class used for the AgentSchema Parcel.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.parcel.Parcel import Parcel
from OSAF.framework.Preferences import Preferences

class AppSchema(Parcel):
    def __init__(self, name, parent, kind):
        Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        repository = self.getRepository()
        pref = repository.find("//Data/prefs")
        if not pref:
            kind = repository.find("//Parcels/OSAF/AppSchema/Preferences")
            parent = repository.find("//Data")
            pref = Preferences("prefs", parent, kind)
            
        
        
