__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class DeclarationEntry:
    def __init__(self, name, clientID, type, description, acl = None):
        self.name = name
        self.owner = clientID
        self.type = type
        self.description = description
        self.acl = acl
        self.subscriptionList = []
        return
    
    #def __repr__(self):
    #    return self.name + " " + self.clientID + self.type + \
    #           self.description + str(self.subscriptionList)

    def GetName(self):
        return self.name
    
    def GetOwner(self):
        return self.owner
    
    def GetType(self):
        return self.type
    
    def GetDescription(self):
        return self.description
    
    def GetAcl(self):
        return self.acl
    
    def GetSubscriptionList(self):
        return self.subscriptionList
    