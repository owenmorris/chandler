"""Model object representing a contact's nane.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from application.repository.Thing import Thing
from application.repository.KindOfThing import AkoThingFactory
from application.repository.Namespace import chandler

# many of these strings should really be enumerated types; we'll convert them
# to that when the infrastructure is ready.

_attributes = [{ chandler.uri : chandler.fullname,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Full Name'),
                 chandler.default : '' },
               
               { chandler.uri : chandler.sortname,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Sort Name'),
                 chandler.default : '' }
               ]

# @@@ Hack, need to implement subclassing
_personAttributes = [ { chandler.uri : chandler.fullname,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Full Name'),
                        chandler.default : '' },
                      
                      { chandler.uri : chandler.sortname,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Sort Name'),
                        chandler.default : '' }, 
                      
                      { chandler.uri : chandler.firstname,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('First Name'),
                        chandler.default : '' },
                      
                      { chandler.uri : chandler.middlename,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Middle Name'),
                        chandler.default : '' },
                      
                      { chandler.uri : chandler.lastname,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Last Name'),
                        chandler.default : '' },
                      
                      { chandler.uri : chandler.nickname,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Nickname'),
                        chandler.default : '' },
                      
                      { chandler.uri : chandler.honorific,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Honorific'),
                        chandler.default : '' },
                      
                      { chandler.uri : chandler.suffix,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('Suffix'),
                        chandler.default : '' }
                      ]


class AkoContactNameFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self, chandler.ContactName, _attributes)
        
# @@@ Need to mark as a subclass
class AkoPersonNameFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self, chandler.PersonName, _personAttributes)

class ContactName(Thing):
    """ContactName"""
    
    # @@@ Note, some of the calls to self.get() should
    # perhaps be calls to self.GetAttribute(). The
    # first is a lookup that returns None if the
    # key is not in the dictionary. The second calls the
    # generic Thing call, looking at meta-data for the
    # attribute if it is there.
    
    def __init__(self, contact):
        Thing.__init__(self)

        if contact.contactType == 'Person':
            self.SetAko(AkoPersonNameFactory().GetAko())
        else:
            self.SetAko(AkoContactNameFactory().GetAko())
            
        self.SetUri(self.GetUniqueId())
        
    def IsPersonName(self):
        ako = self.GetAko()
        return (ako.GetUri() == chandler.PersonName)

    def SetAttribute(self, uri, value):
        Thing.SetAttribute(self, uri, value)
        if (uri == chandler.fullname):
            self.ParseFullName()
        else:
            self.CalcFullName()
        self.CalcSortName()
        
    def GetFullName(self):
        return self.GetAttribute(chandler.fullname)
        
    # return an abbreviated version of the name
    def GetShortName(self):
        if self.IsPersonName():
            firstName = self.get(chandler.firstname)
            lastName = self.get(chandler.lastname)
            if lastName == None:
                return firstName
            return '%s. %s' % (firstName[0], lastName)
        else:
            return self.GetFullName()
           
    # a name part was changed, so recompute the full name
    # FIXME: this needs be internationalized eventually
    def CalcFullName(self):
         if self.IsPersonName():
            if self.get(chandler.lastname) == None:
                self[chandler.fullname] = self.get(chandler.firstname)
                return
            
            if self.get(chandler.middlename) != None:
                self[chandler.fullname] = (self[chandler.firstname] + ' ' + 
                                           self[chandler.middlename] + ' ' + 
                                           self[chandler.lastname])
            else:
               self[chandler.fullname] = self[chandler.firstname] + ' ' + self[chandler.lastname]
    
    # the full name was set, so parse it into the constituent parts if appropriate
    def ParseFullName(self):
       if self.IsPersonName(): 
           nameList = self[chandler.fullname].split(' ')
           self[chandler.firstname] = nameList[0]
           partCount = len(nameList)
           if partCount == 1:
               self[chandler.lastname] = None
           else:
               if partCount > 2:
                   self[chandler.middlename] = nameList[1]
               else:
                    self[chandler.middlename] = None
               
               self[chandler.lastname] = nameList[-1]
 
    # calculate the sort name from the parts
    # FIXME: this must be internationalized eventually
    def CalcSortName(self):
        if self.IsPersonName():
            if self.get(chandler.lastname) == None:
                self[chandler.sortname] = self.get(chandler.firstname)
            else: 
                self[chandler.sortname] = self[chandler.lastname] + ', ' + self[chandler.firstname]
        else:
            self.sortname = self.get(chandler.fullname)