
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.schema.Types import Type


class Alias(Type):

    def isAlias(self):
        return True

    def type(self, value):

        if self.hasAttributeValue('types'):
            for t in self.types:
                if t.recognizes(value):
                    return t

        return None
        
    def recognizes(self, value):

        if not self.hasAttributeValue('types'):
            return True
        
        for t in self.types:
            if t.recognizes(value):
                return True
    
    def typeXML(self, value, generator):

        if not self.hasAttributeValue('types'):
            super(Alias, self).typeXML(value, generator)
            return

        for t in self.types:
            if t.recognizes(value):
                t.typeXML(value, generator)
                return

        raise ValueError, "value '%s' of type '%s' unrecognized by %s" %(value, type(value), self.getItemPath())
