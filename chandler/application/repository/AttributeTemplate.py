""" AttributeTemplate, meta-information about an attribute.

    AttributeTemplates are a Thing, and could have a
    KindOfThing associated with them. For bootstrapping
    purposes, we're skipping this step for now.
    
    @@@ This module is still in the "elaboration" phase, 
    a draft to explore current thinking.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.repository.Thing import Thing
from application.repository.Namespace import chandler

class AttributeTemplate(Thing):
    def __init__(self, dict=None):
        Thing.__init__(self, dict)
        
    def GetCardinality(self):
        """ Gets the cardinality for this attribute.
            1 => Only one value expected
            None => Multiple values allowed/expected
        """
        return self[chandler.cardinality]

    def SetCardinality(self, cardinality):
        """ Sets the cardinality for this attribute.
            1 => Only one value expected
            None => Multiple values allowed/expected
        """
        self[chandler.cardinality] = cardinality
    
    def GetRange(self):
        """ Gets the range for this attribute, values this
            attribute is allowed to have.
            'string' => python string
            'datetime' => mx.DateTime
            [] => simple enumeration, a list of strings
        """
        return self[chandler.range]

    def SetRange(self, range):
        """ Sets the range for this attribute, values this
            attribute is allowed to have.
            'string' => python string
            'datetime' => mx.DateTime
            [] => simple enumeration, a list of strings
        """        
        self[chandler.range] = range
    
    def GetRequired(self):
        """ Returns a boolean.
            True => attribute is required for the Thing
            False => attribute is not required
        """
        return self[chandler.required]
    
    def SetRequired(self, required):
        """ Expects a boolean.
            True => attribute is required for the Thing
            False => attribute is not required
        """
        self[chandler.required] = required
    
    def GetDefault(self):
        """ Gets the default value, should be
            consistent with range and cardinality.
        """
        return self[chandler.default]
    
    def SetDefault(self, default):
        """ Sets the default value, should be
            consistent with range and cardinality.
        """
        self[chandler.default] = default
        
    def GetDisplayName(self):
        """ Gets the display name, a string that can
            be used in a parcel viewer or other ui.
        """
        return self[chandler.displayName]
    
    def SetDisplayName(self, value):
        """ Sets the display name, a string that can
            be used in a parcel viewer or other ui.
        """
        self[chandler.displayName] = value
        
    def IsValid(self, value):
        """ Use cardinality, range, required, etc. to
            validate 'value' for this attribute.
            @@@ Not implemented, default to True
        """
        return True
