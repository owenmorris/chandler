""" Thing, the base of all data in the Chandler repository.

    A thing is a collection of attribute value pairs. 

    @@@ Currently, this collection is implemented as a PersistentDict,
    where each entry in the dictionary represents an attribute. One 
    could imagine several different implementations. Consider this
    implementation a strawman, useful for conveying a mere taste of 
    what we want to accomplish.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

from application.repository.Namespace import chandler

class Thing(PersistentDict):
    def __init__(self, dict=None):
        PersistentDict.__init__(self, dict)

    def GetAttribute(self, uri):
        """ Returns the value of the attribute named by the uri argument.
        Looks for an AttributeTemplate for this uri, and does validation
        if it finds one.
        
        @@@ Note: we're doing validation because we can, to show off
        AttributeTemplates. We might not want to for performance reasons.
        """
        template = self.GetAttributeTemplate(uri)

        # If we have schema information about this attribute, use it
        if template:

            # If the attribute is required, throw an exception if
            # we don't find it. (usual dictionary behavior)
            if template.GetRequired():
                value = self[uri]

            # If the attribute is not required, provide a default
            else:
                value = self.get(uri, template.GetDefault())

            # Do a check against type and cardinality
            assert(template.IsValid(value))

        # If we don't have schema information, return None if
        # we can't find the attribute. (use get instead of [])
        else:
            value = self.get(uri, None)
            
        return value
    
    def SetAttribute(self, uri, value):
        """ Sets the attribute named by 'uri', giving it 'value'.
        Looks for an AttributeTemplate for this uri, and does validation
        if it finds one.
        
        @@@ Note: we're doing validation because we can, to show off
        AttributeTemplates. We might not want to for performance reasons.
        """
        template = self.GetAttributeTemplate(uri)

        # if we have schema information, use it for validation
        if template:
            assert(template.IsValid(value))
            
        self[uri] = value
        
    def GetAttributeTemplate(self, uri):
        """ Returns an AttributeTemplate for this uri, if we can find one.
        If this Thing has a type, we ask the KindOfItem
        """
        ako = self.GetAko()
        if ako:
            template = ako.GetAttributeTemplate(uri)
        else:
            template = None
        return template
        
    # Because we're bootstrapping, don't call the more general 
    # GetAttribute/SetAttribute.
    
    def GetAko(self):
        """ Returns the kind of Thing this object is an instance of. 
        Should return an instance of KindOfThing, or None.
        """
        return self.get(chandler.ako)
    
    def SetAko(self, akoThing):
        """ Set the kind of Thing this object is an instance of. 
        Expects an instance of KindOfThing.
        """
        self[chandler.ako] = akoThing
        
    def GetUri(self):
        """ Returns the uri that uniquely names this Thing.
        """
        return self.get(chandler.uri)
    
    def SetUri(self, uri):
        """ Sets the uri that uniquely names this Thing.
        """
        self[chandler.uri] = uri
        
        
    # For debugging purposes, be able to print a 'thing' as a list of
    # triples. From this exercise, one could imagine how one would
    # generate the appropriate RAP call to a repository.
    
    def PrintTriples(self):
        print ('******* Triples for ' + self.GetUri() + ' *********')
        for key in self.keys():
            value = self[key]
            if (type(value) is PersistentList):
                for oneValue in value:
                    self.PrintTriple(key, oneValue)
            else:
                self.PrintTriple(key, value)
        print('')

    def PrintTriple(self, key, value):
        if (isinstance(value, Thing)):
            print (self.GetUri(), key, value.GetUri())
        else:
            print (self.GetUri(), key, value)
        