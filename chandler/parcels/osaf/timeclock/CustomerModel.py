#!bin/env python

"""
Temporary Model Classe for Chandler Timeclock customers - will integrate with application.model soon
Note that I use the word 'customer' instead of 'client' purely to avoid any type of confusion
or namespace collision with the word 'client' as used in 'client-server application'.
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

                        
class CustomerModel:
    def __init__(self, customerName, billingRate):
        self.name = customerName
        self.billableHours = 0.0
        self.billingRate = billingRate
        # I thought about putting currency name in here as well, but then
        # I'd have to build in a currency converter as well, and I didn't
        # feel up for that.  -- KDS
        
    def GetName(self):
        return self.name
    
    # I don't imagine your customer will changes names often, but it's
    # good to leave them that option.
    def SetName(self, aName):
        self.name = aName
        
    def GetBillableHours(self):
        return self.billableHours

    def SetBillingRate(self,rate):
        self.billingRate = rate

    def GetBillingRate(self):
        return self.billingRate
    
    # SetBillableHours shouldn't be used in the normal case;
    # use AddBillableHours normally.
    def SetBillableHours(self):
        return self.bodyAttributes
    
    def AddBillableHours(self, hoursWorked):
        self.billableHours = self.billableHours + hoursWorked
