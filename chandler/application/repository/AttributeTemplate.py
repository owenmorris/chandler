""" AttributeTemplate, meta-information about an attribute.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"



from application.repository.Thing import Thing
from application.repository.Namespace import chandler

class AttributeTemplate(Thing):
    def __init__(self, dict=None):
        Thing.__init__(self, dict)
        
    def GetCardinality(self):
        return self[chandler.cardinality]

    def SetCardinality(self, cardinality):
        self[chandler.cardinality] = cardinality
    
    def GetRange(self):
        return self[chandler.range]

    def SetRange(self, range):
        self[chandler.range] = range
    
    def GetRequired(self):
        return self[chandler.required]
    
    def SetRequired(self, required):
        self[chandler.required] = required
    
    def GetDefault(self):
        return self[chandler.default]
    
    def SetDefault(self, default):
        self[chandler.default] = default
        
    def GetDisplayName(self):
        return self[chandler.displayName]
    
    def SetDisplayName(self, value):
        self[chandler.displayName] = value
        
    def IsValid(self, value):
        return True
