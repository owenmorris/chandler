
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.schema.Types import Type
from repository.schema.TypeHandler import TypeHandler


class Alias(Type):

    def getImplementationType(self):
        return None

    def isAlias(self):
        return True

    def type(self, value):

        if 'types' in self._references:
            for t in self._references['types']:
                if t.recognizes(value):
                    return t
        else:
            return TypeHandler.typeHandler(self.itsView, value)

        return None
        
    def recognizes(self, value):

        if 'types' not in self._references:
            return True
        
        for t in self.types:
            if t.recognizes(value):
                return True

        return False
    
    def typeXML(self, value, generator):

        if 'types' not in self._references:
            super(Alias, self).typeXML(value, generator)
            return

        for t in self.types:
            if t.recognizes(value):
                t.typeXML(value, generator)
                return

        raise TypeError, "value '%s' of type '%s' unrecognized by %s" %(value, type(value), self.itsPath)

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if 'types' not in self._references:
            super(Alias, self).writeValue(itemWriter, buffer, item, value,
                                          withSchema)
            return

        for t in self.types:
            if t.recognizes(value):
                t.writeValue(itemWriter, buffer, item, value, withSchema)
                return

        raise TypeError, "value '%s' of type '%s' unrecognized by %s" %(value, type(value), self.itsPath)
