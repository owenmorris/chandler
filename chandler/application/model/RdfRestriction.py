#!bin/env python

from RdfResource import RdfResource

class RdfRestriction(RdfResource):
    def __init__(self, domain, cardinality=0, required=0, default=None):
        RdfResource.__init__(self)
        
        self.domain = domain
        self.isList = (cardinality != 1)
        self.isRequired = required
        self.default = default
        self.cardinality = cardinality

    def isValid(self, value):
        # placeholder, can look more carefully at info
        if (not self.isRequired) and (value == None):
            return 1

        if self.isList:
            return (isinstance(value, list))
        else:
            return (isinstance(value, self.domain))


        

