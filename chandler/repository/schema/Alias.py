
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from chandlerdb.util.uuid import _hash, _combine
from chandlerdb.schema.descriptor import CDescriptor
from repository.schema.Types import Type
from repository.schema.TypeHandler import TypeHandler


class Alias(Type):

    def getImplementationType(self):
        return None

    def isAlias(self):
        return True

    def getFlags(self):

        flags = CDescriptor.ALIAS

        if 'types' in self._references:
            for t in self._references['types']:
                flags |= t.getFlags()
        else:
            flags |= CDescriptor.PROCESS

        return flags

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

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if 'types' not in self._references:
            return super(Alias, self).writeValue(itemWriter, buffer, item,
                                                 version, value, withSchema)

        for t in self.types:
            if t.recognizes(value):
                return t.writeValue(itemWriter, buffer, item,
                                    version, value, withSchema)

        raise TypeError, "value '%s' of type '%s' unrecognized by %s" %(value, type(value), self.itsPath)

    def hashItem(self):
        """
        Compute a hash value from this aliase's schema.

        The hash value is computed from the aliase's path and types.

        @return: an integer
        """

        hash = _hash(str(self.itsPath))
        if 'types' in self._references:
            for t in self.types:
                hash = _combine(hash, t.hashItem())

        return hash
