"""Contact Method
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from application.repository.Thing import Thing
from application.repository.KindOfThing import AkoThingFactory
from application.repository.Namespace import chandler

from application.repository.Item import Item
from application.repository.ContactName import ContactName

_attributes = [{ chandler.uri : chandler.methodType,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.methodDescription,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.methodComment,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.phonenumber,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.emailAddress,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },

               { chandler.uri : chandler.imAddress,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },

               { chandler.uri : chandler.webUrl,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.note,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.postalAddress,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None }
               ]

class AkoContactMethodFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self,
                                 chandler.ContactMethod,
                                 _attributes)

class ContactMethod(Item):
    
    #@@@ Constructor might need to be more complicated
    def __init__(self):
        Item.__init__(self)
        self.SetAko(AkoContactMethodFactory().GetAko())
        
    def GetLocationAbbreviation(self):
        description = self.GetAttribute(chandler.methodDescription)
        return description[0]
    
    def GetFirstFormattedValue(self):
        return "@@@Fixme!"
    
    # @@@ Hook for formatting attributes in a type specific manner
    #     Unused for now, perhaps should be more general to
    #     'Things' or 'Items'.
    def GetFormattedAttribute(self, attribute):
        return self.GetAttribute(attribute)
        
        
        